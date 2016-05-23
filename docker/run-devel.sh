docker stop vadvisor
docker stop cadvisor
docker rm vadvisor
docker rm cadvisor
docker network rm testnet
docker network create testnet

sudo docker run \
  --volume=/:/rootfs:ro \
  --volume=/var/run:/var/run:rw \
  --volume=/sys:/sys:ro \
  --volume=/var/lib/docker/:/var/lib/docker:ro \
  --volume=/cgroup:/cgroup:ro \
  --publish=8080:8080 \
  --detach=true \
  --name=cadvisor \
  --privileged=true \
  --net=testnet \
  google/cadvisor:latest

sleep 10

sudo docker run \
    --volume=/var/run/libvirt/libvirt-sock-ro:/var/run/libvirt/libvirt-sock-ro:Z \
    --name vadvisor \
    --publish 8181:8181 \
    --detach=true \
    --privileged=true \
    --net=testnet \
    --label io.cadvisor.metric.prometheus-vadvisor="/var/vadvisor/cadvisor_config.json" \
    -e METRICS="http://vadvisor:8181/metrics" \
    virtkube/vadvisor:latest
