#!/bin/bash
cd /tmp/scalable_ws
apt-get update
apt-get upgrade -y
rosdep update
rosdep install --from-paths src --ignore-src -r -y
catkin build
source devel/setup.bash
catkin run_tests
catkin_test_results > out.txt

