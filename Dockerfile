FROM fedora:23

MAINTAINER "Roman Mohr" <rmohr@redhat.com>

ENV VERSION master

EXPOSE 8181

RUN dnf -y install tar libvirt-python3 && dnf clean all

RUN dnf -y install python3-greenlet && dnf clean all && \
    curl -LO https://github.com/gevent/gevent/releases/download/v1.1.1/gevent-1.1.1-cp34-cp34m-manylinux1_x86_64.whl && \
    mv gevent-1.1.1-cp34-cp34m-manylinux1_x86_64.whl gevent-1.1.1-cp34-cp34m-linux_x86_64.whl && \
    pip3 --no-cache-dir install gevent-1.1.1-cp34-cp34m-linux_x86_64.whl && \
    rm -f gevent-1.1.1-cp34-cp34m-linux_x86_64.whl && \
    rm -rf ~/.pip

RUN \
    curl -LO https://github.com/kubevirt/vAdvisor/archive/$VERSION.tar.gz#/vAdvisor-$VERSION.tar.gz && \
    tar xf vAdvisor-$VERSION.tar.gz && cd vAdvisor-$VERSION && \
    sed -i '/libvirt-python/d' requirements.txt && \
    pip3 --no-cache-dir install -r requirements.txt && pip3 --no-cache-dir install . && \
    rm -rf ~/.pip && \
    cd .. && rm -rf vAdvisor-$VERSION*
    
ENTRYPOINT [ "/usr/bin/vAdvisor" ]
