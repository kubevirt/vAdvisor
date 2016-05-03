from vadvisor.app.rest import make_rest_app
import pytest
import webtest


@pytest.fixture
def _app():
    return make_rest_app()


@pytest.fixture
def app(_app):
    return webtest.TestApp(_app)


def test_metrics(app):
    resp = app.get("/metrics")
    assert resp.status_int == 200
    assert "process_virtual_memory_bytes" in resp


def test_vms(app):
    resp = app.get("/api/v1.0/vms")
    assert resp.status_int == 200
    assert resp.json == {}
