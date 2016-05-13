import libvirt
import inspect


class LibvirtConnection:

    def __init__(self, con_str=None):
        self._con_str = con_str
        self._conn = None

    def __enter__(self):
        if not self._conn:
            self._conn = libvirt.openReadOnly(self._con_str)
        return self._conn

    def __exit__(self, exc_type, exc_value, traceback):
        if self._conn and exc_type and inspect.isclass(exc_type) and issubclass(exc_type, libvirt.libvirtError):
            try:
                self._conn.close()
            except Exception:
                pass

            self._conn = None
