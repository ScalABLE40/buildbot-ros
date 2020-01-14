#!/bin/sh
source /root/buildbot-env/bin/activate
/root/buildbot-env/bin/buildbot create-master /root/buildbot-ros
cd /root/buildbot-ros
B=`pwd`
# B = /home/buildbot-ros
cp /root/buildbot-ros/buildbot.tac /root/buildbot-ros/buildbot.tac.bk
sed 's/umask = None/umask = 0o22/' buildbot.tac.bk > buildbot.tac
chmod 400 /root/buildbot-ros/secret/OathToken
# wait for db to start by trying to upgrade the master
until /root/buildbot-env/bin/buildbot upgrade-master $B
do
    echo "Can't upgrade master yet. Waiting for database ready?"
    sleep 1
done

# we use exec so that twistd use the pid 1 of the container, and so that signals are properly$
#exec  twistd -ny $B/buildbot.tac
cd ..
/root/buildbot-env/bin/buildbot restart buildbot-ros
if [[ $1 == "-d" ]]; then
  while true; do sleep 1000; done
fi

if [[ $1 == "-bash" ]]; then
  /bin/bash
fi

tail -f /root/buildbot-ros/twistd.log