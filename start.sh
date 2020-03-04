#!/bin/bash#

# add arg
#source $PWD/docker/env.sh
# check OathToken exists
OathToken="./buildbot-ros/secret/OathToken"
if [ -f "$OathToken" ]
then
	echo "OathToken exists."
else
	mkdir $PWD/buildbot-ros/secret/
	touch $PWD/buildbot-ros/secret/OathToken
	read -r -p "Please enter your OathToken: " response
	if [ -z "$response" ]
	then 
		read -r -p "Please enter your OathToken: " response
	else
	cat > $OathToken << EOF
$response 
EOF
	fi
fi

# check gpg key in folder ros-repository-docker
gpgkey_pub="./ros-repository-docker/public.key"
gpgkey_sign="./ros-repository-docker/signing.key"
if [ -f "$gpgkey_pub" ] && [ -f "$gpgkey_sign" ]
then
	echo "gpg signing key and public key exists."
else
	echo "You missed public key or signing key. Please create your gpg key"
	exit 1
fi

#add Signing key to docker-compouse-deb,test,doc,sys
read -r -p "Please enter your Signing Key(gpg): " Signing_key
echo $PWD
python edit-compose.py $PWD/buildbot-ros/docker_components/docker-compose-deb.yaml $Signing_key
#python edit-compose.py ./buildbot-ros/docker-compose/docker-compouse-doc $Signing_key
python edit-compose.py $PWD/buildbot-ros/docker_components/docker-compose-test.yaml $Signing_key
python edit-compose.py $PWD/buildbot-ros/docker_components/docker-compose-sys.yaml $Signing_key


# crate docker image for buildbot master
docker build -f docker/Dockerfile_bb_master -t buildbot-ros:latest --build-arg SSH_KEY="$(cat $HOME/.ssh/id_rsa)" .
# crate docker image for buildbot worker
docker build -f docker/Dockerfile_bb_worker -t buildbot-worker:latest --build-arg SSH_KEY="$(cat $HOME/.ssh/id_rsa)" .

# add arg
source $PWD/docker/env.sh
source $PWD/ros-repository-docker/env.sh
# create local repository image
docker-compose -f ros-repository-docker/docker-compose.yaml build
# start all 
docker-compose -f docker/docker-compose.yaml up
