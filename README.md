# vAdvisor

VM monitoring application based on WSGI, libvirt, flask and gevent, inspired by cAdvisor. 

## Run it

To use it on a host with libvirtd running, use the prepared docker image

```bash
docker run \
    --volume=/var/run/libvirt/libvirt-sock-ro:/var/run/libvirt/libvirt-sock-ro:Z \
    --name vadvisor \
    --publish 8181:8181 \
    --detach=true \
    virtkube/vadvisor:latest
```

vAdvisor can now be accessed on port `8181`. If you are using RHEL, CentOS or
Fedora you need to add the `--privileged` flag because otherwise SELinux does
not allow it to access the libvirt socket.

## Prometheus

VM runtime metrics are exposed at `/metrics`.

## REST-API

### Polling metrics

VM runtime metrics are exposed at `/api/v1.0/vms`.

### Event stream

VM lifecycle changes can be monitored at `/api/v1.0/events`.

The following query parameters are supported:

| Parameter           | Description                                   | Default           |
|---------------------|-----------------------------------------------|-------------------|
|`stream`             |Stream events as they occur.                   | false             |
|`start_time`         |Start time of events to query (`stream=false`) | Beginning of time |
|`end_time`           |End time of events to query (`stream=false`)   | Now               |
|`max_events`         |Number of events to return (`stream=false`)    | 10                |
|`all_events`         |Return all supported events                    | false             |
|`undefined_events`   |Include delete events                          | false             |
|`defined_events`     |Include create events                          | false             |
|`started_events`     |Include start events                           | false             |
|`suspended_events`   |Include supend events                          | false             |
|`resumed_events`     |Include resume events                          | false             |
|`stopped_events`     |Include stop events                            | false             |
|`shutdown_events`    |Include shutdown events                        | false             |
|`pmsuspended_events` |Include power management suspended events      | false             |
|`crashed_events`     |Include crash events                           | false             |
