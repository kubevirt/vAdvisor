import argparse
from gevent import pywsgi
from gevent import Greenlet, socket, sleep
import logging
import six
from .app.rest import make_rest_app
from .virt.conn import LibvirtConnection
from .app.statsd import StatsdCollector
from .virt.collector import Collector
from .store.event import InMemoryStore
from .store.event import LevelDBStore


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8181, help='Port to serve on.')
    parser.add_argument('--statsd-host', type=str, required=False, help="Push VM metrics to this statsd endpoint")
    parser.add_argument('--statsd-port', type=int, default=8125, help="Push VM metrics to this statsd endpoint")
    parser.add_argument('--statsd-interval', type=int, default=15, help="Statd push interval in seconds")
    parser.add_argument('--event-store', type=str, required=False, default="memory", choices=["memory", "leveldb"], help="Storage backend for events")
    parser.add_argument('--leveldb-path', type=str, required=False, default="./db", help="Path where the leveldb should be created")
    parser.add_argument('--event-retention-time', type=int, required=False, help="Retention time for historical data in minutes. Default for the memory backend is one minute, for leveldb it is one day.")
    parser.add_argument('-v', '--verbose', action='store_true', default=False)
    args = parser.parse_args()

    logging.getLogger().setLevel(level=logging.INFO)
    if args.verbose:
        logging.getLogger('vadvisor').setLevel(level=logging.DEBUG)
    conn = LibvirtConnection()
    if args.event_store == "memory":
        seconds = (args.event_retention_time or 1) * 60
        eventStore = InMemoryStore(seconds=seconds)
    else:
        if args.event_retention_time:
            seconds = args.event_retention_time * 60
        else:
            seconds = 3600 * 24
        eventStore = LevelDBStore(path=args.leveldb_path, seconds=seconds)
    httpd = pywsgi.WSGIServer(('', args.port), make_rest_app(conn, eventStore))
    if args.statsd_host:
        logging.getLogger('vadvisor').info("Will push metrics to statsd endpoint %s:%s every %s seconds.", args.statsd_host, args.statsd_port, args.statsd_interval)

        def push_metrics():
            collector = StatsdCollector(Collector(conn))
            while True:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    for line in collector.collect():
                        socket.wait_write(sock.fileno())
                        sock.sendto(six.b(line), (args.statsd_host, args.statsd_port))
                except Exception as e:
                    logging.error(e)
                sleep(args.statsd_interval)
        Greenlet(push_metrics).start()
    httpd.serve_forever()


if __name__ == '__main__':
    run()
