import libvirt


class Collector:

    def __init__(self, con_str=None):
        self._con_str = con_str
        self._conn = None

    def collect(self):
        stats = []
        if not self._conn:
            self._conn = libvirt.openReadOnly(self._con_str)
        if not self._conn:
            print('Failed to open connection to the hypervisor')
            return None
        domainIDs = self._conn.listDomainsID()
        if not domainIDs:
            print('Failed to get list of domains')
        for domainID in domainIDs:
            domain = self._conn.lookupByID(domainID)
            domainName = domain.name()
            domainUUID = domain.UUIDString()

            domainStats = {}
            domainStats['uuid'] = domainUUID
            domainStats['name'] = domainName
            domainStats['memory'] = domain.memoryStats()
            domainStats['cpu'] = domain.getCPUStats(True)[0]
            stats.append(domainStats)
        return stats
