import six
from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily

from ..virt.collector import Collector


class Subtree:

    def __init__(self, field, elements):
        self._elements = {}
        for element in elements:
            self._elements[element.field] = element
        self.field = field

    def process(self, labels, domainStats):
        for field, element in six.iteritems(self._elements):
            if field in domainStats:
                element.process(labels, domainStats[field])

    def reset(self, label_keys):
        for _, element in six.iteritems(self._elements):
            element.reset(label_keys)

    def expose(self):
        for _, element in six.iteritems(self._elements):
            for metric in element.expose():
                yield metric


class Tree(Subtree):

    def __init__(self, label_keys, elements):
        Subtree.__init__(self, None, elements)
        self._label_keys = label_keys

    def process(self, labels, domainStats):
        for field, element in six.iteritems(self._elements):
            if field in domainStats:
                element.process(labels, domainStats[field])

    def reset(self):
        for _, element in six.iteritems(self._elements):
            element.reset(self._label_keys)


class Metric:

    def __init__(self, name, field, description):
        self.field = field
        self.name = name
        self.description = description
        self.metric = None

    def expose(self):
        yield self.metric


class Gauge(Metric):

    def process(self, labels, value):
        self.metric.add_metric(labels, value)

    def reset(self, label_keys):
        self.metric = GaugeMetricFamily(self.name, self.description, labels=label_keys)


class Counter(Metric):

    def process(self, labels, value):
        self.metric.add_metric(labels, value)

    def reset(self, label_keys):
        self.metric = CounterMetricFamily(self.name, self.description, labels=label_keys)


class LibvirtCollector:

    _vm = Tree(['uuid'], [
        Subtree('cpu', [
            Counter('vm_cpu_time', 'cpu_time', 'Overall VM CPU time in milliseconds'),
            Counter('vm_cpu_system_time', 'system_time', 'Overall VM System CPU time in milliseconds'),
            Counter('vm_cpu_user_time', 'user_time', 'Overall VM User CPU time in milliseconds')
        ]),
        Subtree('memory', [
            Gauge('vm_memory_actual', 'actual', "VM Memory in bytes"),
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
        Counter('vm_disk_write_requests_total', 'wr_req', 'Cumulative count of disk write requests'),
        Counter('vm_disk_write_bytes_total', 'wr_bytes', 'Cumulative count of disk writes in bytes'),
        Counter('vm_disk_read_requests_total', 'rd_req', 'Cumulative count of disk read requests'),
        Counter('vm_disk_read_bytes_total', 'rd_bytes', 'Cumulative count of disk reads in bytes'),
    ])

    _cpus = Tree(['uuid', 'cpu'], [
        Counter('vm_vcpu_total', 'vcpu_time', 'Overall CPU time on the virtual CPU in milliseconds'),
        Counter('vm_cpu_total', 'cpu_time', 'Overall CPU time on the host CPU in milliseconds'),
    ])

    def __init__(self, collector=Collector()):
        self.collector = collector

    def collect(self):
        # Get stats from libvirt
        stats = self.collector.collect()

        # Reset all metrics since the python prometheus library does not
        # override collected metrics with identical label values
        for tree in (self._vm, self._interfaces, self._disks, self._cpus):
            tree.reset()

        # Collect metrics
        for domainStats in stats:
            # VM stats
            labels = [domainStats['uuid']]
            self._vm.process(labels, domainStats)
            # Networking stats
            for interface in domainStats['network']['interfaces']:
                labels = [domainStats['uuid'], interface['name']]
                self._interfaces.process(labels, interface)
            # Disk stats
            for disk in domainStats['diskio']:
                labels = [domainStats['uuid'], disk['name']]
                self._disks.process(labels, disk)
            # CPU stats
            for indx, cpu in enumerate(domainStats['cpu']['per_cpu_usage']):
                labels = [domainStats['uuid'], str(indx)]
                self._cpus.process(labels, cpu)

        # Yield all collected metrics
        for tree in (self._vm, self._interfaces, self._disks, self._cpus):
            for metric in tree.expose():
                yield metric
