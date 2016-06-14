from gevent import pywsgi
import argparse

from .app.rest import make_rest_app


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8181, help='Port to serve on.')
    args = parser.parse_args()
    httpd = pywsgi.WSGIServer(('', args.port), make_rest_app())
    httpd.serve_forever()

if __name__ == '__main__':
    run()
