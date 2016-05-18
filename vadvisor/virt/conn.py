import libvirt
import inspect


class LibvirtConnection:

    ignore_codes = set([
        libvirt.VIR_ERR_NO_DOMAIN,  # Domain not found
        libvirt.VIR_ERR_NO_NETWORK,  # Network not found
    ])

    def __init__(self, con_str=None):
        self._con_str = con_str
        self._conn = None

    def __enter__(self):
        if not self._conn:
            self._conn = libvirt.openReadOnly(self._con_str)
        return self._conn

    def __exit__(self, exc_type, exc_value, traceback):
        if (self._conn and exc_type and inspect.isclass(exc_type)
                and issubclass(exc_type, libvirt.libvirtError)
                and exc_value.get_error_level() == libvirt.VIR_ERR_ERROR
                and exc_value.get_error_code() not in self.ignore_codes):
            try:
                self._conn.close()
            except Exception:
                pass

            self._conn = None
