import six
import logging
import collections
import plyvel
from datetime import datetime, timedelta
from dateutil import parser
import time
import json


class InMemoryStore:

    """Naive memory based in memory store implementation.

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

    def get(self, start_time=None, stop_time=None, elements=10):
        now = datetime.utcnow()
        lower_bound = now - timedelta(seconds=self.seconds)
        if not start_time:
            start_time = datetime(1970, 1, 1, 1)
        if not stop_time:
            stop_time = now
        if lower_bound > start_time:
            start_time = lower_bound
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

    def expire(self):
        now = datetime.utcnow()
        self._expire(now)

    def _expire(self, now):
        lower_bound = now - timedelta(seconds=self.seconds)
        while len(self.deque) > 0 and self.deque[0].timestamp < lower_bound:
            self.deque.popleft()

    def empty(self):
        return len(self.deque) == 0


class Element:

    def __init__(self, timestamp, data):
        self.data = data
        self.timestamp = timestamp


class LevelDBStore:

    def __init__(self, path, seconds=3600 * 24):
        self.path = path
        self.seconds = seconds
        self.db = plyvel.DB(path, create_if_missing=True)
        self.log = logging.getLogger('vadvisor')
        self.cnt = 0

    def get(self, start_time=None, stop_time=None, elements=10):
        now = _now()
        lower_bound = now - self.seconds
        if not start_time:
            start_time = 0
        else:
            start_time = _convert_time(start_time)
        if not stop_time:
            stop_time = now
        else:
            stop_time = _convert_time(stop_time)
        if lower_bound > start_time:
            start_time = lower_bound
        events = []
        found = 0
        self.log.debug("Asking for range %s - %s", start_time, stop_time)
        for key, value in self.db.iterator(start=_pack(start_time), stop=_pack(stop_time), include_stop=False):
            self.log.debug("Fetched %s", _unpack(key))
            event = _loads(value)
            events.append(event)
            found += 1
            if elements and found >= elements:
                break
        return events

    def expire(self):
        lower_bound = time.time() - self.seconds
        with self.db.write_batch(sync=True) as writer:
            for key, _ in self.db.iterator(stop=_pack(lower_bound), include_stop=False):
                self.log.debug("Deleting %s", _unpack(key))
                writer.delete(key)

    def empty(self):
        for _, _ in self.db.iterator():
            return False
        return True

    def put(self, data):
        now = _now()
        self.log.debug("Adding %s", now)
        self.db.put(_pack(now) + self._postfix(), _dumps(data), sync=True)
        self.expire()

    def _postfix(self):
        self.cnt = (self.cnt + 1) % 1000
        if six.PY3:
            return bytes(str(self.cnt), "utf-8")
        else:
            return bytes(str(self.cnt))


def _pack(timestamp):
    if six.PY3:
        return bytes(str(int(timestamp)), "utf-8")
    else:
        return bytes(long(timestamp))


def _dumps(data):
    if six.PY3:
        return bytes(json.dumps([data], default=datetime_serial), "utf-8")
    else:
        return json.dumps([data], default=datetime_serial)


def _loads(data):
    if six.PY3:
        return json.loads(str(data, "utf-8"))[0]
    else:
        return json.loads(data)[0]


def _unpack(timestamp):
    if six.PY3:
        return int(timestamp)
    else:
        return long(timestamp)


def _now():
    return _convert_time(datetime.utcnow())


def _convert_time(d):
    epoch = datetime(1970, 1, 1)
    return (d - epoch).total_seconds()


def datetime_serial(obj):

    if isinstance(obj, datetime):
        # We should have all timestamps in utc. If not we have a problem
        serial = obj.isoformat() + "Z"
        return serial
    raise TypeError("Type not serializable")
