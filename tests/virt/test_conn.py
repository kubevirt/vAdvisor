import libvirt
import pytest
from vadvisor.virt.conn import LibvirtConnection


@pytest.fixture
def conn():

    class Conn:

        def __init__(self):
            self.init = True

        def close(self):
            self.init = False

        def lookupByID(self, index):
            if not isinstance(index, int):
                raise AttributeError()
            if not self.init:
                raise libvirt.libvirtError(0)

    c = LibvirtConnection()
    c._conn = Conn()
    return c


def test_close_on_libvirtError(conn):
    try:
        with conn:
            raise libvirt.libvirtError(0)
    except libvirt.libvirtError:
        pass

    assert not conn._conn


def test_close_on_libvirtError_subclass(conn):
    try:
        with conn:
            class Err(libvirt.libvirtError):
                pass
            raise Err(0)
    except libvirt.libvirtError:
        pass

    assert not conn._conn


def test_only_close_on_libvirtError(conn):
    e = None
    try:
        with conn as c:
            c.lookupById('not int')
    except AttributeError as err:
        e = err

    assert conn._conn
    assert e


def test_handle_access_on_closed_connection(conn):
    try:
        with conn as c:
            c.close()
            c.lookupByID(1)
    except libvirt.libvirtError:
        pass

    assert not conn._conn
