from gevent import pywsgi
from prometheus_client import REGISTRY

from .app.prometheus import LibvirtCollector
from .app.rest import make_rest_app


def run():
    REGISTRY.register(LibvirtCollector())
    httpd = pywsgi.WSGIServer(('', 8181), make_rest_app())
    httpd.serve_forever()

if __name__ == '__main__':
    run()
