from vadvisor.store.event import LevelDBStore
import pytest
from freezegun import freeze_time
from datetime import datetime, timedelta


@pytest.fixture
@freeze_time("2012-01-14 03:00:00")
def expired_store(tmpdir_factory):
    store = LevelDBStore(str(tmpdir_factory.mktemp("leveldb")), 60)
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


def test_empty_store(tmpdir_factory):
    store = LevelDBStore(str(tmpdir_factory.mktemp("leveldb")), 60)
    assert store.get() == []


@freeze_time("2012-01-14 03:02:00")
def test_dont_get_old_without_expire(expired_store):
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
