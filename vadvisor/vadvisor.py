import argparse
import collections
from gevent import pywsgi
from gevent import Greenlet, socket, sleep
import logging
import six
from geventhttpclient import HTTPClient
import json

from .app.rest import make_rest_app
from .virt.conn import LibvirtConnection
from .app.statsd import StatsdCollector
from .app.hawkular import HawkularCollector
from .virt.collector import Collector


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8181, help='Port to serve on.')
    parser.add_argument('--statsd-host', type=str, required=False, help="Push VM metrics to this statsd endpoint")
    parser.add_argument('--statsd-port', type=int, default=8125, help="Push VM metrics to this statsd endpoint")
    parser.add_argument('--statsd-interval', type=int, default=15, help="Statd push interval in seconds")
    parser.add_argument('--hawkular-host', type=str, required=False, help="Push VM metrics to this hawkular endpoint host")
    parser.add_argument('--hawkular-port', type=int, default=8080, help="Push VM metrics to this hawkular endpoint port")
    parser.add_argument('--hawkular-interval', type=int, default=15, help="Hawkular push interval in seconds")
    parser.add_argument('--hawkular-tenant', type=str, default="vadvisor", help="Hawkular tenant")
    parser.add_argument('-v', '--verbose', action='store_true', default=False)
    args = parser.parse_args()

    logging.getLogger().setLevel(level=logging.INFO)
    if args.verbose:
        logging.getLogger('vadvisor').setLevel(level=logging.DEBUG)
    conn = LibvirtConnection()
    httpd = pywsgi.WSGIServer(('', args.port), make_rest_app(conn))
    if args.statsd_host:
        logging.getLogger('vadvisor').info("Will push metrics to statsd endpoint %s:%s every %s seconds.", args.statsd_host, args.statsd_port, args.statsd_interval)

        def push_statsd_metrics():
            collector = StatsdCollector(Collector(conn))
            while True:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    for line in collector.collect():
                        socket.wait_write(sock.fileno())
                        sock.sendto(six.b(line), (args.statsd_host, args.statsd_port))
                except Exception as e:
                    logging.getLogger('vadvisor').error(e)
                sleep(args.statsd_interval)
        Greenlet(push_statsd_metrics).start()

    if args.hawkular_host:
        logging.getLogger('vadvisor').info("Will push metrics to hawkular endpoint %s:%s every %s seconds.", args.hawkular_host, args.hawkular_port, args.hawkular_interval)

        def push_hawkular_metrics():
            collector = HawkularCollector(Collector(conn))
            http = HTTPClient(args.hawkular_host, args.hawkular_port)
            while True:
                try:
                    hawkular_metrics = collections.defaultdict(list)
                    for metrics in collector.collect():
                        hawkular_metrics[metrics[0]].append(metrics[1])

                    for metrics_type, metrics in hawkular_metrics:
                        response = http.post(
                            '/hawkular/metrics/' + metrics_type + '/raw',
                            json.dumps(metrics),
                            headers={"Content-Type": "application/json", "Hawkular-Tenant": args.hawkular_tenant}
                        )
                        logging.getLogger('vadvisor').debug(response)
                except Exception as e:
                    logging.getLogger('vadvisor').error(e)
                sleep(args.hawkular_interval)
        Greenlet(push_hawkular_metrics).start()
    httpd.serve_forever()


if __name__ == '__main__':
    run()
