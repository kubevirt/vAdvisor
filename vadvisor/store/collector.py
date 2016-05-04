from . import event


class InMemoryStore:

    def __init__(self, seconds=60):
        self.seconds = seconds
        self.metrics = {}

    def put(self, metrics):
        for domain in metrics:
            uuid = domain['uuid']
            if not self.metrics.get(uuid):
                self.metrics[uuid] = event.InMemoryStore(self.seconds)
            del domain['uuid']
            del domain['name']
            self.metrics[uuid].put(domain)
        for k in self.metrics.keys():
            self.metrics[k].expire()
            if self.metrics[k].empty():
                del self.metrics[k]

    def get(self, filter=None):
        result = {}
        if not filter:
            for k in self.metrics:
                result[k] = self.metrics[k].get(elements=self.seconds * 2)
        else:
            metrics = self.metrics.get(filter)
            if metrics:
                result[filter] = metrics.get(elements=self.seconds * 2)
        return result
