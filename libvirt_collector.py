import libvirt


class Collector:

    def __init__(self, con_str=None):
        self._con_str = con_str

    def collect(self):
        stats = []
        conn = libvirt.openReadOnly(self._con_str)
        if not conn:
            print 'Failed to open connection to the hypervisor'
            return None
        domainIDs = conn.listDomainsID()
        if not domainIDs:
            print 'Failed to get list of domains'
        for domainID in domainIDs:
            domain = conn.lookupByID(domainID)
            domainName = domain.name()
            domainUUID = domain.UUIDString()
            print domain.UUIDString()

            domainStats = {}
            domainStats['uuid'] = domainUUID
            domainStats['name'] = domainName
            domainStats['memory'] = domain.memoryStats()
            domainStats['cpu'] = domain.getCPUStats(True)[0]
            stats.append(domainStats)
        return stats
