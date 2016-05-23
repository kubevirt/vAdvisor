#!/bin/bash
set -e

sed -i -e "s METRICS $METRICS g" /var/vadvisor/cadvisor_config.json
/usr/bin/vAdvisor $@
