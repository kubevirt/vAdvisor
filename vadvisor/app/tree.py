import six


class Subtree:

    def __init__(self, field, elements):
        self._elements = {}
        for element in elements:
            self._elements[element.field] = element
        self.field = field

    def process(self, labels, domainStats, timestamp=None):
        for field, element in six.iteritems(self._elements):
            if field in domainStats:
                element.process(labels, domainStats[field], timestamp)

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

    def process(self, labels, domainStats, timestamp=None):
        for field, element in six.iteritems(self._elements):
            if field in domainStats:
                element.process(labels, domainStats[field], timestamp)

    def reset(self):
        for _, element in six.iteritems(self._elements):
            element.reset(self._label_keys)
