import libvirt
from xml.etree import ElementTree
from datetime import datetime


class Collector:

    def __init__(self, con_str=None):
        self._con_str = con_str
        self._conn = None

    def collect(self):
        try:
            return self._collect()
        except Exception:
            # print('Failed to collect metrics from libvirt: {0}'.format(e))
            if self._conn is not None:
                self._conn.close()
            self._conn = None
            raise

    def _collect(self):
        stats = []
        if not self._conn:
            self._conn = libvirt.openReadOnly(self._con_str)
        domainIDs = self._conn.listDomainsID()
        if not domainIDs:
            print('Failed to get list of domains')
        for domainID in domainIDs:
            domain = self._conn.lookupByID(domainID)
            tree = ElementTree.fromstring(domain.XMLDesc())
            interfaces = []
            for iface in tree.findall('devices/interface/target'):
                name = iface.get('dev')
                ifStats = domain.interfaceStats(name)
                interfaces.append({
                    'name': name,
                    'rx_bytes': ifStats[0],
                    'rx_packets': ifStats[1],
                    'rx_errors': ifStats[2],
                    'rx_drops': ifStats[3],
                    'tx_bytes': ifStats[4],
                    'tx_packets': ifStats[5],
                    'tx_errors': ifStats[6],
                    'tx_dropped': ifStats[7],
                }
                )
            disks = []
            for disk in tree.findall('devices/disk/target'):
                name = disk.get('dev')
                diskStats = domain.blockStats(name)
                disks.append({
                    'name': name,
                    'rd_req': diskStats[0],
                    'rd_bytes': diskStats[1],
                    'wr_req': diskStats[2],
                    'wr_bytes': diskStats[3],
                    'errors': diskStats[4],
                })
            domainName = domain.name()
            domainUUID = domain.UUIDString()
            domainStats = {}
            domainStats['uuid'] = domainUUID
            domainStats['name'] = domainName
            domainStats['memory'] = domain.memoryStats()
            domainStats['cpu'] = {
                "usage": domain.getCPUStats(True)[0],
                "per_cpu_usage": domain.getCPUStats(False),
            }
            domainStats['network'] = {
                'interfaces': interfaces
            }
            domainStats['diskio'] = disks
            domainStats['timestamp'] = datetime.utcnow()
            stats.append(domainStats)
        return stats
