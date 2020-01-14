# ros-buildbot-docker

## Improvements

* 
* 
* 


## Installation
Just clone the repository

**Note:** 

Installing Docker and docker-compose
## Usage
* Prepare and Publish a Signing Key for local repository
```
gpg --gen-key
gpg --edit-key 'pub 10E6133F', addkey, save
gpg --export-secret-key 'pub 10E6133F' > private.key
gpg --export 'pub 10E6133F' >> private.key 
back up private key and rm private.key
gpg --export 'pub 10E6133F' > public.key
gpg --export-secret-subkeys 'sub A72DB3EF' > signing.key
gpg --delete-secret-key 'pub 10E6133F'
```
* Save public.key and signing.key in folder "ros-repository-docker"
* modify environment parameter in buildbot-ros/docker and ros-repository-docker
* Run start.sh 
```
sh start.sh
```
