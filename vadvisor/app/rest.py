import logging
import json
from datetime import datetime

from flask import Flask, Response, request
from gevent import Greenlet, queue
from prometheus_client.exposition import CONTENT_TYPE_LATEST
from prometheus_client import REGISTRY, generate_latest
from wsgigzip import gzip

from ..virt.collector import Collector
from ..virt.event import LibvirtEventBroker, LIFECYCLE_EVENTS


app = Flask(__name__)


@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/api/v1.0/vms')
def getVMStats():
    return Response(
        json.dumps(app.collector.collect(), default=_datetime_serial),
        mimetype='application/json'
    )


@app.route('/api/v1.0/events')
def getVmEvents():
    def stream(environ, start_response):
        start_response('200 OK', [('Content-Type', 'text/event-stream')])
        events = _eventMapper(request.args)

        def generator():
            body = queue.Queue()
            app.eventBroker.subscribe(body)
            try:
                for item in body:
                    if 'all' in events or item["event_type"] in events:
                        yield json.dumps(item, default=_datetime_serial) + '\n'
            except Exception as e:
                app.eventBroker.unsubscribe(body)
                raise e
            except GeneratorExit as e:
                app.eventBroker.unsubscribe(body)
                raise e
        return generator()
    return stream


def _eventMapper(queryParams):
    events = []
    if queryParams.get('all_events') == 'true':
        events.append('all')
        return events
    for event in LIFECYCLE_EVENTS:
        if queryParams.get(event.lower() + "_events") == 'true':
            events.append(event)
    return events


@app.route('/metrics')
def getPromMetrics():
    @gzip()
    def prom_metrics(environ, start_response):
        status = "200 OK"
        headers = [("Content-type", CONTENT_TYPE_LATEST)]
        start_response(status, headers)
        return [generate_latest(REGISTRY)]
    return prom_metrics


def make_rest_app():
    # set up logging
    if not app.debug:
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.ERROR)
        app.logger.addHandler(stream_handler)

    # start libvirt event broker
    broker = LibvirtEventBroker()
    g = Greenlet(broker.run)
    g.start()
    app.eventBroker = broker

    # Attach libvirt metrics collector
    app.collector = Collector()

    # Add gzip support
    mime_types = ['application/json', 'text/plain']
    return gzip(mime_types=mime_types, compress_level=9)(app)


def _datetime_serial(obj):

    if isinstance(obj, datetime):
        # We should have all timestamps in utc. If not we have a problem
        serial = obj.isoformat() + "Z"
        return serial
    raise TypeError("Type not serializable")
