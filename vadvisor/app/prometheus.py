import six
from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily

from ..virt.collector import Collector


class Subtree:

    def __init__(self, field, elements):
        self._elements = {}
        for element in elements:
            self._elements[element.field] = element
        self.field = field

    def process(self, label_keys, labels, domainStats):
        for field, element in six.iteritems(self._elements):
            if field in domainStats:
                for metric in element.process(label_keys, labels, domainStats[field]):
                    yield metric


class Tree(Subtree):

    def __init__(self, label_keys, elements):
        Subtree.__init__(self, None, elements)
        self._label_keys = label_keys

    def process(self, labels, domainStats):
        for field, element in six.iteritems(self._elements):
            if field in domainStats:
                for metric in element.process(self._label_keys, labels, domainStats[field]):
                    yield metric


class Metric:

    def __init__(self, name, field, description):
        self.field = field
        self.name = name
        self.description = description
        self.metric = None


class Gauge(Metric):

    def process(self, label_keys, labels, value):
        metric = GaugeMetricFamily(self.name, self.description, labels=label_keys)
        metric.add_metric(labels, value)
        yield metric


class Counter(Metric):

    def process(self, label_keys, labels, value):
        metric = CounterMetricFamily(self.name, self.description, labels=label_keys)
        metric.add_metric(labels, value)
        yield metric


class LibvirtCollector:

    _vm = Tree(['uuid'], [
        Subtree('cpu', [
            Counter('vm_cpu_time', 'cpu_time', 'Overall VM CPU time'),
            Counter('vm_cpu_system_time', 'system_time', 'Overall VM System CPU time'),
            Counter('vm_cpu_user_time', 'user_time', 'Overall VM User CPU time')
        ]),
        Subtree('memory', [
            Gauge('vm_memory_actual', 'actual', "VM Memory"),
        ])
    ])

    _interfaces = Tree(['uuid', 'interface'], [
        Counter('vm_network_receive_bytes_total', 'rx_bytes', 'Cumulative count of bytes received'),
        Counter('vm_network_receive_packets_total', 'rx_packets', 'Cumulative count of packets received'),
        Counter('vm_network_receive_packages_dropped_total', 'rx_dropped', 'Cumulative count of packages dropped while receiving'),
        Counter('vm_network_receive_errors_total', 'rx_errors', 'Cumulative count of errors encountered while receiving'),
        Counter('vm_network_transmit_bytes_total', 'tx_bytes', 'Cumulative count of bytes transmitted'),
        Counter('vm_network_transmit_packets_total', 'tx_packets', 'Cumulative count of packets transmitted'),
        Counter('vm_network_transmit_packages_dropped_total', 'tx_dropped', 'Cumulative count of packages dropped while transmitting'),
        Counter('vm_network_transmit_errors_total', 'tx_errors', 'Cumulative count of errors encountered while transmitting'),
    ])

    _disks = Tree(['uuid', 'device'], [
        Counter('vm_disk_write_requests_total', 'wr_req', ''),
        Counter('vm_disk_write_bytes_total', 'wr_bytes', ''),
        Counter('vm_disk_read_requests_total', 'rd_req', ''),
        Counter('vm_disk_read_bytes_total', 'rd_bytes', ''),
    ])

    _cpus = Tree(['uuid', 'cpu'], [
        Counter('vm_vcpu_total', 'vcpu_time', ''),
        Counter('vm_cpu_total', 'cpu_time', ''),
    ])

    def __init__(self):
        self.collector = Collector()

    def collect(self):
        stats = self.collector.collect()
        for domainStats in stats:
            # VM stats
            labels = [domainStats['uuid']]
            for metric in self._vm.process(labels, domainStats):
                yield metric
            # Networking stats
            for interface in domainStats['network']['interfaces']:
                labels = [domainStats['uuid'], interface['name']]
                for metric in self._interfaces.process(labels, interface):
                    yield metric
            # Disk stats
            for disk in domainStats['diskio']:
                labels = [domainStats['uuid'], disk['name']]
                for metric in self._disks.process(labels, disk):
                    yield metric
            # CPU stats
            for indx, cpu in enumerate(domainStats['cpu']['per_cpu_usage']):
                labels = [domainStats['uuid'], str(indx)]
                for metric in self._cpus.process(labels, cpu):
                    yield metric
