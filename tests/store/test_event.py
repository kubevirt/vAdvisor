from vadvisor.store.event import InMemoryStore
import pytest
from freezegun import freeze_time
from datetime import datetime, timedelta


@pytest.fixture
@freeze_time("2012-01-14 03:00:00")
def expired_store():
    store = InMemoryStore(60)
    # Insert old data
    store.put('old')
    store.put('old')
    store.put('old')
    return store


@pytest.fixture
@freeze_time("2012-01-14 03:01:30")
def new_store(expired_store):
    # Insert newer data
    expired_store.put('new')
    expired_store.put('new')
    expired_store.put('new')
    return expired_store


@pytest.fixture
@freeze_time("2012-01-14 03:01:50")
def newest_store(new_store):
    # Insert newer data
    new_store.put('newest')
    new_store.put('newest')
    new_store.put('newest')
    return new_store


def test_empty_store():
    store = InMemoryStore()
    assert store.get() == []


@freeze_time("2012-01-14 03:02:00")
def test_expire_on_get(expired_store):
    expired_store.get()
    assert expired_store.get() == []


@freeze_time("2012-01-14 03:02:00")
def test_get_all_new(new_store):
    assert new_store.get() == ['new', 'new', 'new']


@freeze_time("2012-01-14 03:02:00")
def test_get_two_new(new_store):
    assert new_store.get(elements=2) == ['new', 'new']


@freeze_time("2012-01-14 03:02:00")
def test_get_not_older_than(newest_store):
    events = newest_store.get(
        elements=2,
        start_time=datetime.utcnow() - timedelta(seconds=20)
    )
    assert events == ['newest', 'newest']


@freeze_time("2012-01-14 03:02:00")
def test_get_not_newer_than(newest_store):
    events = newest_store.get(
        elements=2,
        stop_time=datetime.utcnow() - timedelta(seconds=20)
    )
    assert events == ['new', 'new']
