#!/bin/bash
cd /tmp
#rosdep db
#rosdep install --from-paths src --ignore-src -r -y
echo $SINGING_KEY
echo $LOCAL_RESPOSITORY
source /opt/ros/kinetic/setup.bash
sh -c 'echo "yaml file:///home/package/private.yaml" >> /etc/ros/rosdep/sources.list.d/20-default.list'
rosdep update
rosdep db
missing=`dpkg-checkbuilddeps 2>&1 | sed 's/dpkg-checkbuilddeps:\serror:\sUnmet build dependencies: //g' | sed 's/[\(][^)]*[\)] //g'`
echo "missing : $missing"
sh -c 'echo "deb http://172.17.0.1:49161 xenial main" >> /etc/apt/sources.list'
#url=http://local-repository:80/dists/
url=http://172.17.0.1:49161/dists/
if curl --output /dev/null --silent --head --fail "$url"; then
  printf '%s\n' "$url exist"
  	apt-get -y update
	apt-get -y upgrade
else
  printf '%s\n' "$url does not exist"
fi
apt-get install -y $missing
bloom-generate rosdebian --os-name ubuntu --os-version xenial --ros-distro kinetic
fakeroot debian/rules binary
cd ..
deb_pack=`find . -maxdepth 1 -name '*.deb'`
pack=${deb_pack#??}
echo "pack: $pack"
mv -f $pack /home/package/