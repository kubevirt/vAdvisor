import collections
from datetime import datetime, timedelta


class InMemoryStore:

    """Naive memory based event store implementation.

    Don't make the history too big because we always have to go through the
    whole history for selecting and expiring the right entries.
    """

    def __init__(self, seconds=60):
        self.seconds = seconds
        self.deque = collections.deque()

    def put(self, data):
        now = datetime.utcnow()
        self._expire(now)
        self.deque.append(Element(now, data))

    def get(self, start_time=datetime(1970, 1, 1), stop_time=datetime.utcnow(), elements=10):
        now = datetime.utcnow()
        self._expire(now)
        events = []
        found = 0
        for event in self.deque:
            if event.timestamp >= start_time and event.timestamp <= stop_time:
                events.append(event.data)
                found += 1
                if elements and found >= elements:
                    break
            elif event.timestamp > stop_time:
                break
        return events

    def _expire(self, now):
        lower_bound = now - timedelta(seconds=self.seconds)
        while len(self.deque) > 0 and self.deque[0].timestamp < lower_bound:
            self.deque.popleft()


class Element:

    def __init__(self, timestamp, data):
        self.data = data
        self.timestamp = timestamp
