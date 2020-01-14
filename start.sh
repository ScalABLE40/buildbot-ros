#!/bin/bash#
# check OathToken exists
OathToken="./secret_master/OathToken"
if [ -f "$OathToken" ]
then
	echo "OathToken exists."
else
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

# check ssh key for mater
ssh_master="./docker/ssh_master/id_rsa"
if [ -f "$ssh_master" ]
then
	echo "SSH key for mater exists."
else
	echo "SSH key for mater doesn't exist."
	read -r -p "Please enter your Email address for SSH-Key: " Emailadd
	while [ -z "$Emailadd" ]; do
		read -r -p "Please enter your Email address: " Emailadd
	done
	read -r -p "Please save you ssh in folder 'docker/ssh_master', don't give password for SSH-key, press any key to continue"
	ssh-keygen -t rsa -b 4096 -C $Emailadd
	eval "$(ssh-agent -s)"
	ssh-add $PWD"/docker/ssh_master/id_rsa"
	read -r -p "Please put id_rsa.pub for mater in your github" 
fi

# check ssh key for worker
ssh_master="./docker/ssh_worker/id_rsa"
if [ -f "$ssh_master" ]
then
	echo "SSH key for worker exists."
else
	echo "SSH key for worker doesn't exist."
	read -r -p "Please save you ssh in folder 'docker/ssh_worker', don't give password for SSH-key, press any key to continue"
	ssh-keygen -t rsa -b 4096 -C $Emailadd
	eval "$(ssh-agent -s)"
	ssh-add $PWD"/docker/ssh_master/id_rsa"
	read -r -p "Please put id_rsa.pub for worker in your github" 
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
docker build -f docker/Dockerfile_bb_master -t buildbot-ros:latest .
# crate docker image for buildbot worker
docker build -f docker/Dockerfile_bb_worker -t buildbot-worker:latest .

# add arg
source $PWD/buildbot-ros/docker/env.sh
source $PWD/ros-repository-docker/env.sh
# create local repository image
docker-compose -f ros-repository-docker/docker-compose.yaml build
docker-compose -f ros-repository-docker/docker-compose.yaml up

#start master worker db
docker-compose -f docker/docker-compose.yaml up