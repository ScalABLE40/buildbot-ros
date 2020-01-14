#This docker image is based on https://github.com/glenux/docker-debian-repository. Original docker is out of date and doesn't work anymore.
FROM nginx
MAINTAINER Ruichao Wu <ruichao.wu@ipa.fraunhofer.de>

ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update


# Install supervisor for managing services
RUN apt-get install -q -y supervisor cron openssh-server pwgen reprepro screen vim-tiny nginx expect


# Configure cron
# Install cron for managing regular tasks
#RUN sed -i 's/\(session *required *pam_loginuid.so\)/#\1/' /etc/pam.d/cron


# Install ssh (run/stop to create required directories)
#RUN mkdir /var/run/sshd
#RUN service ssh start ; sleep 1
#RUN service ssh stop

#import gpg key
COPY ./public.key /home/public.key
COPY ./signing.key /home/signing.key

# Configure reprepro
ARG YourOrganizationName
ARG SIGNKEY
ENV SIGNKEY=${SIGNKEY} 
ARG KEY
ENV SIGNING_PASSWORD=${KEY} 
ADD scripts/reprepro-import.sh /usr/local/sbin/reprepro-import
RUN chmod 755 /usr/local/sbin/reprepro-import
RUN mkdir -p /var/www/building/ubuntu/conf
ADD configs/reprepro-distributions /var/www/building/ubuntu/conf/distributions
ADD configs/debian-upload.sh /tmp/debian-upload.sh 
ADD configs/reprepro.exp /usr/local/bin/reprepro.exp

# Configure nginx
RUN echo "daemon off;" >> /etc/nginx/nginx.conf
RUN rm -f /etc/nginx/conf.d/default.conf
ADD configs/nginx-default.conf /etc/nginx/conf.d/default.conf
RUN chmod 755 /usr/local/bin/reprepro.exp

# Setup root access
RUN echo "root:docker" | chpasswd

RUN passwd -d root 

# add rospdep to /home/package to share
RUN apt-get install -y python-pip
RUN pip install --upgrade pip  
RUN pip install pyyaml 
RUN mkdir -p /home/package
RUN mkdir -p /home/rosdep
ADD configs/rosdep_private.yaml /home/package/private.yaml
ADD scripts/update_private_rosdep.py /home/rosdep/update_private_rosdep.py

# Finalize
ENV DEBIAN_FRONTEND newt

ADD scripts/start.sh /usr/local/sbin/start
RUN chmod 755 /usr/local/sbin/start

#VOLUME ["/var/www/building/ubuntu"]

EXPOSE 80
EXPOSE 22
CMD ["/usr/local/sbin/start"]
