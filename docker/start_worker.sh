#!/bin/sh
B=`pwd`
docker login registry.msb.scalable.atm.virtualfortknox.de
# B = /buildbot
buildbot-worker create-worker $WORKERNAME $BUILDMASTER:$BUILDMASTER_PORT $WORKERNAME $WORKERPASS
pwd
cp /buildbot/buildbot.tac /buildbot/$WORKERNAME/buildbot.tac
cp buildbot.tac buildbot.tac.bk
#sed 's/umask = None/umask = 0o22/' buildbot.tac.bk > buildbot.tac
# wait for db to start by trying to upgrade the master
sleep 100
buildbot-worker start $WORKERNAME
/usr/bin/dumb-init twistd --pidfile= -ny $WORKERNAME/buildbot.tac 
tail -f /buildbot/$WORKERNAME/twistd.log