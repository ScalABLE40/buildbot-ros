#!/bin/bash
# ${args[0]} =kinetic
args=("$@")
echo ${args[0]}
python /root/docbuild.py /tmp/ ${args[0]}
ls /tmp/docs
cp -rf /tmp/docs /var/www/building/docs
