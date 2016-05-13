import libvirt

from gevent import sleep
from logging import debug, error
from threading import Thread
from datetime import datetime

from . import loop
from .conn import LibvirtConnection


LIFECYCLE_EVENTS = ("Defined",
                    "Undefined",
                    "Started",
                    "Suspended",
                    "Resumed",
                    "Stopped",
                    "Shutdown",
                    "PMSuspended",
                    "Crashed",
                    )


class LibvirtEventBroker(Thread):

    def __init__(self, conn=LibvirtConnection()):
        Thread.__init__(self)
        self._conn = conn
        self._subscriptions = set()

    def subscribe(self, subscriber):
        debug("Adding subscription")
        self._subscriptions.add(subscriber)
        return subscriber

    def unsubscribe(self, queue):
        debug("Removing Subscription")
        queue.put(StopIteration)
        self._subscriptions.remove(queue)

    def run(self):
        loop.virEventLoopPureRegister()
        libvirt.registerErrorHandler(error_handler, self)

        while True:
            try:
                with self._conn as conn:
                    conn.registerCloseCallback(connection_close_callback, self)
                    conn.domainEventRegister(lifecycle_callback, self)
                loop.virEventLoopPureRun()
            except Exception as e:
                error(e)
                sleep(5)


def connection_close_callback(conn, reason, opaque):
    reasonStrings = ("Error", "End-of-file", "Keepalive", "Client",)
    error("Connection to libvirt unexpectedly closed: %s: %s" %
          (conn.getURI(), reasonStrings[reason]))
    loop.virEventLoopPureStop()
    if conn is not None:
        conn.close()


def error_handler(unused, error, listener):
    error(error)


def lifecycle_callback(connection, domain, event, detail, listener):
    debug("event received")
    e = create_event(domain.name(), domain.UUIDString(), event, detail)
    for subscriber in listener._subscriptions:
        subscriber.put(e)


def create_event(name, uuid, event, reason):
    return {
        'domain_name': name,
        'domain_id': uuid,
        'timestamp': datetime.utcnow(),
        'event_type': LIFECYCLE_EVENTS[event],
        'reason': domDetailToString(event, reason)
    }


def domDetailToString(event, detail):
    domEventStrings = (
        ("Added", "Updated"),
        ("Removed", ),
        ("Booted", "Migrated", "Restored", "Snapshot", "Wakeup"),
        ("Paused", "Migrated", "IOError", "Watchdog",
         "Restored", "Snapshot", "API error"),
        ("Unpaused", "Migrated", "Snapshot"),
        ("Shutdown", "Destroyed", "Crashed",
         "Migrated", "Saved", "Failed", "Snapshot"),
        ("Finished", ),
        ("Memory", "Disk"),
        ("Panicked", ),
    )
    return domEventStrings[event][detail]
