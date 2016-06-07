import vadvisor
import pytest
import webtest
from prometheus_client import REGISTRY
from vadvisor.store.collector import InMemoryStore as MetricStore
from vadvisor.app.prometheus import LibvirtCollector


@pytest.fixture
def _app():

    class Collector:

        def __init__(self):
            self.metrics = []

        def set_metrics(self, metrics):
            self.metrics = metrics

        def collect(self):
            return self.metrics

    app = vadvisor.app.rest.app
    app.collector = Collector()
    app.metricStore = MetricStore()
    REGISTRY.register(LibvirtCollector(collector=app.collector))
    return app


@pytest.fixture
def app(_app):
    return webtest.TestApp(_app)


def test_metrics(app):
    resp = app.get("/metrics")
    assert resp.status_int == 200
    assert "process_virtual_memory_bytes" in resp


def test_vms(app):
    resp = app.get("/api/v1.0/stats").follow()
    assert resp.status_int == 200
    assert resp.json == {}


def test_vm_state_report(app):
    app.app.collector.set_metrics([{
        "uuid": "1234",
        "state": "Running",
        "diskio": [],
        "cpu": {"per_cpu_usage": []},
        "network": {"interfaces": []}
    }])
    resp = app.get("/metrics")
    assert "vm_up{uuid=\"1234\"} 1.0" in resp
    app.app.collector.set_metrics([])
    resp = app.get("/metrics")
    assert "vm_up{uuid=\"1234\"} 0.0" in resp
