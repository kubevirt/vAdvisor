from ..virt.collector import Collector
from .tree import Tree, Subtree

import time


class Metric:

    def __init__(self, name, field, unit=None):
        self.field = field
        self.name = name
        self.metric = None
        self.unit = unit

    def reset(self, label_keys):
        self.metric = []
        self.label_keys = label_keys

    def expose(self):
        if not self.metric:
            return
        yield (
            self.family,
            {
                "id": self.name,
                "data": self.metric
            }
        )

    def process(self, labels, value, timestamp):
        data = {
            "timestamp": timestamp,
            "value": value,
            "tags": {k: v for k, v in zip(self.label_keys, labels)}
        }
        if self.unit:
            data["tags"]["unit"] = self.unit
        self.metric.append(data)


class Gauge(Metric):

    family = "gauges"


class Availability(Metric):

    family = "availability"


class Counter(Metric):

    family = "counters"


class HawkularCollector:

    _vm = Tree(['uuid'], [
        Availability('vm_up', 'state'),
        Subtree('cpu', [
            Counter('vm_cpu_total', 'cpu_time', 'ms'),
            Counter('vm_cpu_system_total', 'system_time', 'ms'),
            Counter('vm_cpu_user_total', 'user_time', 'ms')
        ]),
        Subtree('memory', [
            Gauge('vm_memory', 'actual', 'bytes'),
        ])
    ])

    _interfaces = Tree(['uuid', 'interface'], [
        Counter('vm_network_receive_total', 'rx_bytes', 'bytes'),
        Counter('vm_network_receive_total', 'rx_packets', 'packets'),
        Counter('vm_network_receive_dropped_total', 'rx_dropped', 'packets'),
        Counter('vm_network_receive_errors_total', 'rx_errors'),
        Counter('vm_network_transmit_total', 'tx_bytes', 'bytes'),
        Counter('vm_network_transmit_total', 'tx_packets', 'packets'),
        Counter('vm_network_transmit_dropped_total', 'tx_dropped', 'packets'),
        Counter('vm_network_transmit_errors_total', 'tx_errors'),
    ])

    _disks = Tree(['uuid', 'device'], [
        Counter('vm_disk_write_requests_total', 'wr_reqs'),
        Counter('vm_disk_write_total', 'wr_bytes', 'bytes'),
        Counter('vm_disk_read_requests_total', 'rd_reqs'),
        Counter('vm_disk_read_total', 'rd_bytes', 'bytes'),
    ])

    _cpus = Tree(['uuid', 'cpu'], [
        Counter('vm_vcpu_total', 'vcpu_time', 'ms'),
        Counter('vm_cpu_total', 'cpu_time', 'ms'),
    ])

    def collect(self):
        # Get stats from libvirt
        stats = self.collector.collect()
        timestamp = int(time.time())

        # Reset all metrics
        for tree in (self._vm, self._interfaces, self._disks, self._cpus):
            tree.reset()

        # Collect metrics
        for domainStats in stats:
            # VM status, convert state to a number
            domainStats['state'] = "up" if domainStats['state'] == "Running" else "down"

            # VM stats
            labels = [domainStats['uuid']]
            self._vm.process(labels, domainStats, timestamp)

            # Networking stats
            for interface in domainStats['network']['interfaces']:
                labels = [domainStats['uuid'], interface['name']]
                self._interfaces.process(labels, interface, timestamp)
            # Disk stats
            for disk in domainStats['diskio']:
                labels = [domainStats['uuid'], disk['name']]
                self._disks.process(labels, disk, timestamp)
            # CPU stats
            for cpu in domainStats['cpu']['per_cpu_usage']:
                labels = [domainStats['uuid'], str(cpu['index'])]
                self._cpus.process(labels, cpu, timestamp)

        # Yield all collected metrics
        for tree in (self._vm, self._interfaces, self._disks, self._cpus):
            for metric in tree.expose():
                yield metric

    def __init__(self, collector=Collector()):
        self.collector = collector
