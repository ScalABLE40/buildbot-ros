# ros-buildbot-docker
This is a project for building ROS components using [Buildbot](http://buildbot.net/). This is not aimed to be a replacement for the ROS buildfarm, but rather a (hopefully) easier to setup system
for developers wishing to build their own packages, run continuous integration testing, and build docs.

## Note
It is based on Buildbot-ros developed by Michael Ferguson.
## Design Overview
Buildbot uses a single master, and possibly multiple machines building. At present, the setup described below will use one mater and two workers running in different docker containers. Workers will do all builds in the independent docker containers. It will remove docker containers after workers finish tasks.

There are several 'builder' types available:
 * Debbuild - turns a gbp repository into a set of source and binary debs for a specific ROS distro and Ubuntu release. This is currently run in a nightly build.
 * Testbuild - this is a standard continuous integration testing setup. Checks out a branch of a repository, builds, and runs tests using catkin. Triggered by a commit to the watched branch of the repository. In the future, this could also be triggered by a post commit hook giving even faster response time to let you know that you broke the build or tests (buildbot already has nice GitHub post-commit hooks available). Test builds can also be done on pull requests.
 * Docbuild - are built and uploaded to the master. Currently triggered nightly and generating only the doxygen/epydoc/sphinx documentation (part of the docs you find on ros.org). Uses rosdoc_lite. Documentation builds can only be run on released repositories. 

Clearly, this is still a work in progress, but setup is fairly quick for a small set of projects.
## Improvements
Compared to Buildbot-ros improvements are as below:

* Using a docker container as a building environment instead of using cowbuilder.
* Publishing debian packages in a local repositories after building debian packages successfully.
* Updating rosdep after building debian packages successfully. So that rosdep can find dependencies for other packages.

## Setup of ROSdistro
Before you can build jobs, you will need a _rosdistro_ repository. The rosdistro format is specified
in [REP137](http://ros.org/reps/rep-0137.html). You'll need an index.yaml and at least one set of
distribution files (release.yaml, source.yaml, doc.yaml, *-build.yaml). A complete example of a
simple build configuration for a single repository can be found in
https://github.com/ScalABLE40/rosdistro-scalable.git 

During building time, it will update rosdep/private.yaml automatically. 
The DISTRO will be replaced by the actual building distribution at build time. At a minimum, you will want an Ubuntu archive, the ROS archive, and your building archive. The Ubuntu archive should
include the _universe_ section if you want to run docbuilders.
## Installation
Just clone the repository

**Install docker and docker-compose:** 

reference:
https://docs.docker.com/install/linux/docker-ce/ubuntu/

### install docker
Uninstall old versions
```
sudo apt-get remove docker docker-engine docker.io containerd runc
```
Install using the repository
```
sudo apt-get update
sudo apt-get install \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg-agent \
    software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository \
   "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
   $(lsb_release -cs) \
   stable"
sudo apt-get update
```
use Docker as a non-root user,
```
sudo usermod -aG docker your-user
```
### Install docker-compose
```
sudo curl -L "https://github.com/docker/compose/releases/download/1.25.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
```
Test the installation
```
docker-compose --version
```

## Usage
* Prepare and Publish a Signing Key for local repository

Generate the master key
```
gpg --gen-key
```
Choose RSA and RSA Key. Then you created a master key for signing. Make note of your signing key's ID (which is pub ...) for example, it is  10E6133F. We will need this in the next steps for creating another subkey for signing.
```
gpg --edit-key 'pub 10E6133F'
```
then type  
```
addkey
```
Then you need to choose RSA(sign only). You will get another key for signning, for example, it is A72DB3EF. Type "save" at the prompt.

Detach Master Key From Subkey. Because we already create subkey we don't need the master key on our server. Now you need to detach master key from subkey. First we need to export the mater key and subkey. Then we can delete the keys from GPG's storage. Then re-import the subkey.

First using the "--export-secret-key and --export" commands to export the whole key by using your master key.
```
gpg --export-secret-key 'pub 10E6133F' > private.key
gpg --export 'pub 10E6133F' >> private.key 
```
back up private key and then 
```
rm private.key
```
Then export your public key and your subkey.
```
gpg --export 'pub 10E6133F' > public.key
gpg --export-secret-subkeys 'sub A72DB3EF' > signing.key
```
Now you can delete your mater key.
```
gpg --delete-secret-key 'pub 10E6133F'
```

* Save public.key and signing.key in folder "ros-repository-docker"
* Add your OathToken from github to `buildbot-ros-docker/buildbot-ros/secret/OathToken` file
* modify environment parameter in buildbot-ros/docker and ros-repository-docker
	* Edit ros-repository-docker/env.sh file
	* Edit docker/env.sh 
* buildbot need to access your github repository. So it will add your ssh in its running environment. You can find it is defined in start.sh. Make sure the path of ssh key is right.
* Run start.sh 
```
sh start.sh
```
