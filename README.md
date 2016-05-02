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
