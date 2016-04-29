from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily
from virt.collector import Collector
import six


class Subtree:

    def __init__(self, field, elements):
        self._elements = {}
        for element in elements:
            self._elements[element.field] = element
        self.field = field

    def process(self, labels, domainStats):
        for field, element in six.iteritems(self._elements):
            if field in domainStats:
                for metric in element.process(labels, domainStats[field]):
                    yield metric


class Metric:
    _labels = ['name', 'uuid']

    def __init__(self, name, field, description):
        self.field = field
        self.name = name
        self.description = description


class Gauge(Metric):

    def process(self, labels, value):
        gauge = GaugeMetricFamily(self.name, self.description, labels=self._labels)
        gauge.add_metric(labels, value)
        yield gauge


class Counter(Metric):

    def process(self, labels, value):
        gauge = CounterMetricFamily(self.name, self.description, labels=self._labels)
        gauge.add_metric(labels, value)
        yield gauge


class LibvirtCollector:

    _tree = Subtree(None, [
        Subtree('cpu', [
            Counter('vm_cpu_time', 'cpu_time', 'Overall VM CPU time'),
            Counter('vm_cpu_system_time', 'system_time', 'Overall VM System CPU time'),
            Counter('vm_cpu_user_time', 'user_time', 'Overall VM User CPU time')
        ]),
        Subtree('memory', [
            Gauge('vm_memory_actual', 'actual', "VM Memory"),
        ])
    ])

    def __init__(self):
        self.collector = Collector()

    def collect(self):
        stats = self.collector.collect()
        for domainStats in stats:
            labels = [domainStats['name'], domainStats['uuid']]
            for metric in self._tree.process(labels, domainStats):
                yield metric
