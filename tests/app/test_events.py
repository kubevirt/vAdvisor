import vadvisor.app.rest
import pytest
import webtest
from vadvisor.virt.event import create_event, LIFECYCLE_EVENTS
from vadvisor.store.event import InMemoryStore
from gevent import queue


def event(event):
    return create_event(
        "test",
        "12345678-1234-5678-1234-567812345678",
        event,
        0)


@pytest.fixture
def _app():
    class Broker:

        def subscribe(self, subscriber):
            for idx, _ in enumerate(LIFECYCLE_EVENTS):
                subscriber.put(event(idx))
            subscriber.put(StopIteration)

        def unsubscribe(self, queue):
            queue.put(StopIteration)

    app = vadvisor.app.rest.app
    broker = Broker()
    app.eventBroker = broker
    app.eventStore = InMemoryStore()

    q = queue.Queue()
    broker.subscribe(q)
    for element in q:
        app.eventStore.put(element)

    return app


@pytest.fixture
def app(_app):
    return webtest.TestApp(_app)


def test_get_no_events(app):
    resp = app.get("/api/v1.0/events", 'stream=true')
    assert resp.status_int == 200
    assert 'event_type' not in resp


def test_get_all_events(app):
    resp = app.get('/api/v1.0/events', 'stream=true&all_events=true')
    assert resp.status_int == 200
    assert 'event_type' in resp
    assert len(resp.body.splitlines()) == 9


def test_get_two_events(app):
    resp = app.get('/api/v1.0/events', 'stream=true&started_events=true&resumed_events=true')
    assert resp.status_int == 200
    assert 'Started' in resp
    assert 'Resumed' in resp
    assert len(resp.body.splitlines()) == 2


def test_get_single_events(app):
    for event in LIFECYCLE_EVENTS:
        resp = app.get('/api/v1.0/events', event.lower() + '_events=true&stream=true')
        assert resp.status_int == 200
        assert event in resp
        assert len(resp.body.splitlines()) == 1


def test_get_no_history(app):
    resp = app.get("/api/v1.0/events")
    assert resp.status_int == 200
    assert 'event_type' not in resp


def test_get_full_history(app):
    resp = app.get("/api/v1.0/events", "all_events=true")
    assert resp.status_int == 200
    assert 'event_type' in resp
    assert len(resp.body.splitlines()) == 9
