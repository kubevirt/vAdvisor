from datetime import datetime
from .conn import LibvirtConnection
import libvirt


class Collector:

    def __init__(self, conn=LibvirtConnection()):
        self._conn = conn

    def collect(self):
        stats = []
        bulk_stats = self._bulk_collect()

        for vm in bulk_stats:
            domainStats = {}
            domainStats['uuid'] = vm['uuid']
            domainStats['name'] = vm['name']
            domainStats['state'] = vm['state']
            interfaces = []
            if vm.get('net'):
                for interface in vm['net']:
                    interfaces.append({
                        'name': interface['name'],
                        'rx_bytes': interface['rx_bytes'],
                        'rx_packets': interface['rx_pkts'],
                        'rx_errors': interface['rx_errs'],
                        'rx_dropped': interface['rx_drop'],
                        'tx_bytes': interface['tx_bytes'],
                        'tx_packets': interface['tx_pkts'],
                        'tx_errors': interface['tx_errs'],
                        'tx_dropped': interface['rx_drop'],
                    }
                    )
            domainStats['network'] = {
                'interfaces': interfaces
            }
            disks = []
            if vm.get('block'):
                for disk in vm['block']:
                    values = {
                        'name': disk['name'],
                        'rd_reqs': disk['rd_reqs'],
                        'rd_bytes': disk['rd_bytes'],
                        'rd_times': disk['rd_times'],
                        'wr_reqs': disk['wr_reqs'],
                        'wr_bytes': disk['wr_bytes'],
                        'wr_times': disk['wr_times'],
                        'fl_times': disk['fl_times'],
                        'fl_reqs': disk['fl_reqs']
                    }
                    # A disk has them or not, don't make them 'None'
                    for key in ('physical', 'allocation', 'capacity'):
                        value = disk.get(key)
                        if value:
                            values[key] = value

                    disks.append(values)
            domainStats['diskio'] = disks
            domainStats['memory'] = {
                'actual': vm['memory']['actual'],
                'swap_in': vm['memory'].get('swap_in'),
                'rss': vm['memory']['rss']
            }
            balloon = {}
            if vm.get('balloon'):
                balloon.update(
                    {
                        'current': vm['balloon']['current'],
                        'maximum': vm['balloon']['maximum']
                    }
                )

            domainStats['balloon'] = balloon

            domainStats['timestamp'] = datetime.utcnow()

            domainStats['cpu'] = {
                "usage": {
                    "system_time": vm['cpu']['system'] / 1000000,
                    "user_time": vm['cpu']['user'] / 1000000,
                    "cpu_time": vm['cpu']['time'] / 1000000
                },
                "per_cpu_usage": vCpuStats(vm.get('vcpu'))
            }
            stats.append(domainStats)
        return stats

    def _bulk_collect(self):
        bulk_stats = []
        with self._conn as conn:
            s = conn.getAllDomainStats(
                libvirt.VIR_DOMAIN_STATS_CPU_TOTAL |
                libvirt.VIR_DOMAIN_STATS_BALLOON |
                libvirt.VIR_DOMAIN_STATS_VCPU |
                libvirt.VIR_DOMAIN_STATS_INTERFACE |
                libvirt.VIR_DOMAIN_STATS_BLOCK,
                libvirt.VIR_CONNECT_GET_ALL_DOMAINS_STATS_ACTIVE)

            for domain, stats in s:
                parsed = {}
                parsed["uuid"] = domain.UUIDString()
                parsed["name"] = domain.name()
                parsed['state'] = domStateToString(domain.state()[0])
                parsed['memory'] = domain.memoryStats()
                for key in stats:
                    keys = key.split('.')
                    if len(keys) > 2:
                        t = keys[0]
                        index = keys[1]
                        name = '_'.join(keys[2:])
                        if not parsed.get(t):
                            parsed[t] = {}
                        if not parsed[t].get(index):
                            parsed[t][index] = {}
                        parsed[t][index][name] = stats[key]
                    if len(keys) == 2:
                        t, name = keys
                        if not parsed.get(t):
                            parsed[t] = {}
                        parsed[t][name] = stats[key]

                for c in ('net', 'block'):
                    category = parsed[c]
                    devices = [None] * category['count']
                    for index in range(len(devices)):
                        devices[index] = category[str(index)]
                    parsed[c] = devices
                bulk_stats.append(parsed)
        return bulk_stats


def vCpuStats(vcpus):
    stats = []
    if not vcpus:
        return stats
    for key in vcpus:
        try:
            index = int(key)
        except ValueError:
            continue
        stats.append({
            'index': index,
            'state': vCpuStateToString(vcpus[key]['state']),
            'vcpu_time': vcpus[key]['time'] / 1000000})
    ordered_stats = [None] * len(stats)
    for s in stats:
        ordered_stats[s['index']] = s
    return ordered_stats


def domStateToString(state):
    states = (
        "Unknown",
        "Running",
        "Blocked",
        "Paused",
        "Shutdown",
        "Shutoff",
        "Crashed",
        "PMSuspended"
    )
    return states[state]


def vCpuStateToString(state):
    states = (
        "Offline",
        "Running",
        "Blocked"
    )
    return states[state]
