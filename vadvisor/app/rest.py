import json
import logging

from datetime import datetime
from dateutil import parser
from uuid import UUID

import libvirt

from flask import Flask, Response, request, abort
from gevent import Greenlet, queue, sleep
from prometheus_client.exposition import CONTENT_TYPE_LATEST
from prometheus_client import REGISTRY, generate_latest
from wsgigzip import gzip

from ..app.prometheus import LibvirtCollector
from ..app.statsd import StatsdCollector
from ..virt.collector import Collector
from ..virt.event import LibvirtEventBroker, LIFECYCLE_EVENTS
from ..virt.parser import parse_domain_xml
from ..store.event import InMemoryStore as EventStore
from ..store.collector import InMemoryStore as MetricStore
from ..store.event import datetime_serial


app = Flask(__name__)


@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/api/v1.0/specs/')
def getAllVMSpecs():
    data = []
    with app.conn as conn:
        domainIDs = conn.listDomainsID()
        if domainIDs:
            for domainID in domainIDs:
                domain = conn.lookupByID(domainID)
                data.append(parse_domain_xml(domain.XMLDesc()))

    return Response(
        json.dumps(data, default=datetime_serial),
        mimetype='application/json'
    )


@app.route('/api/v1.0/specs/<id>')
def getVMSpecs(id):
    data = None
    try:
        uuid = UUID(id)
    except Exception:
        uuid = None
    with app.conn as conn:
        try:
            if uuid:
                domain = conn.lookupByUUIDString(id)
            else:
                domain = conn.lookupByName(id)
        except libvirt.libvirtError as e:
            if e.get_error_code() == libvirt.VIR_ERR_NO_DOMAIN:
                abort(404)
            raise e
        data = parse_domain_xml(domain.XMLDesc())

    return Response(
        json.dumps(data, default=datetime_serial),
        mimetype='application/json'
    )


@app.route('/api/v1.0/stats/')
def getAllVMStats():
    if request.args.get('live') == 'true':
        data = {}
        for domain in app.collector.collect():
            uuid = domain['uuid']
            del domain['uuid']
            del domain['name']
            data[uuid] = [domain]
    else:
        data = app.metricStore.get()

    return Response(
        json.dumps(data, default=datetime_serial),
        mimetype='application/json'
    )


@app.route('/statsd')
def getStatsd():
    return Response(
        (x + "\n" for x in app.statsd.collect()),
        mimetype='text/plain'
    )


@app.route('/api/v1.0/stats/<uuid>')
def getVMStats(uuid):
    data = app.metricStore.get(uuid)
    if not data:
        abort(404)
    return Response(
        json.dumps(data, default=datetime_serial),
        mimetype='application/json'
    )


@app.route('/api/v1.0/events')
def getVmEvents():
    event_filter = _eventMapper(request.args)
    if request.args.get('stream') != 'true':
        start_time = parser.parse(request.args.get('start_time', datetime(1970, 1, 1).isoformat()))
        stop_time = parser.parse(request.args.get('end_time', datetime.utcnow().isoformat()))
        elements = int(request.args.get('max_events', 10))

        def generator():
            events = app.eventStore.get(start_time, stop_time, elements)
            for event in events:
                if 'all' in event_filter or event["event_type"] in event_filter:
                    yield json.dumps(event, default=datetime_serial) + '\n'
        return Response(generator(), mimetype='application/json')

    def stream(environ, start_response):
        start_response('200 OK', [('Content-Type', 'application/json')])

        def generator():
            body = queue.Queue()
            app.eventBroker.subscribe(body)
            try:
                for item in body:
                    if 'all' in event_filter or item["event_type"] in event_filter:
                        yield json.dumps(item, default=datetime_serial) + '\n'
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


def make_rest_app(libvirtConnection, eventStore=EventStore()):
    # start libvirt event broker
    broker = LibvirtEventBroker()
    Greenlet(broker.run).start()
    app.eventBroker = broker

    # Attach event store to broker
    app.eventStore = eventStore

    def store_events():
        q = queue.Queue()
        broker.subscribe(q)
        while True:
            app.eventStore.put(q.get())

    Greenlet(store_events).start()

    # Create metric collector
    app.conn = libvirtConnection
    app.collector = Collector(app.conn)

    # Register prometheus metrics
    REGISTRY.register(LibvirtCollector(app.collector))

    # For statsd debugging
    app.statsd = StatsdCollector(app.collector)

    # Collect metrics every second and store them in the metrics store
    app.metricStore = MetricStore()

    def store_metrics():
        while True:
            try:
                app.metricStore.put(app.collector.collect())
            except Exception as e:
                logging.error(e)
                sleep(5)
            sleep(1)

    Greenlet(store_metrics).start()

    # Add gzip support
    mime_types = ['application/json', 'text/plain']
    return gzip(mime_types=mime_types, compress_level=9)(app)
