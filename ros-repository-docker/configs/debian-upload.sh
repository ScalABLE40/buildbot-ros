#!/bin/bash
cd /home/package
echo $package
shortname=${package%?}
python /home/rosdep/update_private_rosdep.py /home/package/private.yaml $shortname
deb_pack=`find . -name $package`
deb_pack=${deb_pack#??}
IFS='_' read -r -a strarr <<< "$deb_pack"
pack=${strarr}
add_version=${strarr[1]}
echo $add_version
existline=`reprepro -b /var/www/building/ubuntu/ list xenial $pack`
IFS=' ' read -r -a strarr <<< "$existline"
exist_version=${strarr[2]}
if [ ! -z "$existline" ];
then
	IFS=' ' read -r -a strarr <<< "$existline"
	exist_version=${strarr[2]}
	if [ add_version==exist_version ];
	then
		echo "exist"
	fi
else
	reprepro.exp /var/www/building/ubuntu/ includedeb xenial $deb_pack
fi
rm $deb_pack
