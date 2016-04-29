FROM fedora:23

MAINTAINER "Roman Mohr" <rmohr@redhat.com>

ENV VERSION master

EXPOSE 8181

RUN dnf -y install tar python3-devel redhat-rpm-config-36 gcc libvirt-python3 && \
    curl -sLO https://github.com/kubevirt/vAdvisor/archive/$VERSION.tar.gz#/vAdvisor-$VERSION.tar.gz && \
    tar xf vAdvisor-$VERSION.tar.gz && cd vAdvisor-$VERSION && \
    sed -i '/libvirt-python/d' requirements.txt && \
    pip3 --no-cache-dir install -r requirements.txt && pip3 --no-cache-dir install . && \
    rm -rf ~/.pip && \
    cd .. && rm -rf vAdvisor-$VERSION* && \
    dnf -y remove gcc tar python3-devel redhat-rpm-config-36 && dnf clean all
    
ENTRYPOINT [ "/usr/bin/vAdvisor" ]
