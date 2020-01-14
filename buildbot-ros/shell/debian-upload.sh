#!/bin/bash
cd /home/package
echo $package
deb_pack=`find . -name $package`
echo $deb_pack
pack=${deb_pack#??}
echo $pack
reprepro.exp /var/www/building/ubuntu/ includedeb xenial $pack
