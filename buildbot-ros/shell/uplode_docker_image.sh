#!/bin/bash
# pwd build/
# Summary: 0 tests, 0 errors, 0 failures, 0 skipped
# 0 container
# 1 binddir
# 2 sys_name
#c[6] failures
args=("$@")
echo ${args[0]}
echo ${args[1]}
docker cp ${args[0]}':'${args[1]}'/scalable_ws/out.txt' 'out.txt'
result_ros=`cat out.txt`
echo $result_ros
tag='registry.msb.scalable.atm.virtualfortknox.de/buildbot_scalable/'
docker_image='scalable-sys'
i=0
c[i]=' '
for word in $result_ros
do
        c[$i]=$word
        echo ${c[$i]}
        i=$((i+1))
done
echo ${c[6]}
if [ ${c[5]} = 0 ]
then 
        docker tag $docker_image':'${args[2]} $tag$docker_image':'${args[2]}
        docker push $tag$docker_image':'${args[2]}
fi
