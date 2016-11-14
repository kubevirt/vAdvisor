from ..virt.collector import Collector
from .tree import Tree, Subtree


class Metric:

    def __init__(self, name, field):
        self.field = field
        self.name = name
        self.metric = None

    def reset(self, label_keys):
        self.metric = []

    def expose(self):
        for metric in self.metric:
            yield metric

    def process(self, labels, value, timestamp=None):
        name = ".".join(("vm", ".".join(labels), self.name))
        self.metric.append("%s:%s|%s" % (name, str(value), self._abr))


class Gauge(Metric):

    _abr = "g"


class Counter(Metric):

    _abr = "c"


class Timer(Metric):

    _abr = "ms"


class StatsdCollector:

    _vm = Tree(['uuid'], [
        Gauge('up', 'state'),
        Subtree('cpu', [
            Counter('cpu.total', 'cpu_time'),
            Counter('cpu.system.total', 'system_time'),
            Counter('cpu.user.total', 'user_time')
        ]),
        Subtree('memory', [
            Gauge('memory.bytes', 'actual'),
        ])
    ])

    _interfaces = Tree(['uuid', 'interface'], [
        Counter('network.receive.bytes.total', 'rx_bytes'),
        Counter('network.receive.packets.total', 'rx_packets'),
        Counter('network.receive.dropped.packets.total', 'rx_dropped'),
        Counter('network.receive.errors.total', 'rx_errors'),
        Counter('network.transmit.bytes.total', 'tx_bytes'),
        Counter('network.transmit.packets.total', 'tx_packets'),
        Counter('network.transmit.dropped.packets.total', 'tx_dropped'),
        Counter('network.transmit.errors.total', 'tx_errors'),
    ])

    _disks = Tree(['uuid', 'device'], [
        Counter('disk.write.requests.total', 'wr_reqs'),
        Counter('disk.write.bytes.total', 'wr_bytes'),
        Counter('disk.read.requests.total', 'rd_reqs'),
        Counter('disk.read.bytes.total', 'rd_bytes'),
    ])

    _cpus = Tree(['uuid', 'cpu'], [
        Counter('vcpu.total', 'vcpu_time'),
        Counter('cpu.total', 'cpu_time'),
    ])

    def collect(self):
        # Get stats from libvirt
        stats = self.collector.collect()

        # Reset all metrics
        for tree in (self._vm, self._interfaces, self._disks, self._cpus):
            tree.reset()

        # Collect metrics
        for domainStats in stats:
            # VM status, convert state to a number
            domainStats['state'] = 1 if domainStats['state'] == "Running" else 0

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
            for cpu in domainStats['cpu']['per_cpu_usage']:
                labels = [domainStats['uuid'], str(cpu['index'])]
                self._cpus.process(labels, cpu)

        # Yield all collected metrics
        for tree in (self._vm, self._interfaces, self._disks, self._cpus):
            for metric in tree.expose():
                yield metric

    def __init__(self, collector=Collector()):
        self.collector = collector
