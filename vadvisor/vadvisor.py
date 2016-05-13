from gevent import pywsgi

from .app.rest import make_rest_app


def run():
    httpd = pywsgi.WSGIServer(('', 8181), make_rest_app())
    httpd.serve_forever()

if __name__ == '__main__':
    run()
