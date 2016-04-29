from flask import Flask, Response
from virt.collector import Collector
import json

from virt.event import LibvirtEventBroker
from gevent import Greenlet, queue
from wsgigzip import gzip


app = Flask(__name__)


@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/v1.0/vms')
def getVMStats():
    return Response(json.dumps(app.collector.collect()), mimetype='application/json')


@app.route('/v1.0/events')
def getVmEvents():
    def stream(environ, start_response):
        start_response('200 OK', [('Content-Type', 'text/event-stream')])

        def generator():
            body = queue.Queue()
            app.eventBroker.subscribe(body)
            try:
                for item in body:
                    yield json.dumps(item) + '\n'
            except Exception as e:
                app.eventBroker.unsubscribe(body)
                raise e
            except GeneratorExit as e:
                app.eventBroker.unsubscribe(body)
                raise e
        return generator()
    return stream


def make_rest_app():
    broker = LibvirtEventBroker()
    g = Greenlet(broker.run)
    g.start()
    app.eventBroker = broker
    app.collector = Collector()
    mime_types = ['application/json']
    return gzip(mime_types=mime_types, compress_level=9)(app)
