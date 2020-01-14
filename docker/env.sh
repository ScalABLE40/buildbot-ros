#!/bin/bash 
# project name
export COMPOSE_PROJECT_NAME=ros-buildbot-docker
#
export BUILDBOT_WORKER_NAME=worker-1
export BUILDBOT_WORKER_PASS=
export BUILDBOT_WEB_URL=http://localhost:8010/
export BUILDBOT_WEB_PORT=tcp:port=8010
export BUILDBOT_PRIVATE_INDEX=git@github.com:ipa-rwu/rosdistro-scalable.git
export BUILDBOT_WORKER_PORT=9989
export BUILDBOT_ROSINSTALL_INDEX=git@github.com:ipa-rwu/scalable_system_setup.git
export LOCAL_RESPOSITORY=local-repository:80
export SINGING_KEY=