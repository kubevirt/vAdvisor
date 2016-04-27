from prometheus_client import REGISTRY, generate_latest
from prometheus_client.core import GaugeMetricFamily
from prometheus_client.exposition import CONTENT_TYPE_LATEST
from libvirt_collector import Collector
import six


def make_wsgi_app():
    def prometheus_app(environ, start_response):
        status = "200 OK"
        headers = [("Content-type", CONTENT_TYPE_LATEST)]
        start_response(status, headers)
        return [generate_latest(REGISTRY)]
    return prometheus_app


class LibvirtCollector:

    _labels = ['name', 'uuid']

    def __init__(self):
        self.collector = Collector()

    def collect(self):
        stats = self.collector.collect()
        for domainStats in stats:
            print domainStats
            for cat, metrics in six.iteritems(domainStats):
                if cat in self._labels:
                    continue
                for name, value in six.iteritems(metrics):
                    gauge = GaugeMetricFamily('_'.join(('vm', cat, name)),
                                              'Help text', labels=['uuid'])
                    gauge.add_metric((domainStats['uuid'],), value)
                    yield gauge
