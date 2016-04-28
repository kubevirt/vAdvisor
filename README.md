# vAdvisor

VM monitoring application based on WSGI, libvirt, flask and gevent, inspired by cAdvisor. 

## Prometheus

VM runtime metrics are exposed at `/metrics`.

## REST-API

### Polling metrics

VM runtime metrics are exposed at `/v1.0/vms`.

### Event stream

VM lifecycle changes can be monitored at `/v1.0/events`.
