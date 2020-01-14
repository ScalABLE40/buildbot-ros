#!/bin/sh
sign=`grep -w 'SignWith' /var/www/building/ubuntu/conf/distributions`
if [ -z "$sign" ]
then
	echo "SignWith: ${SIGNKEY}" >> /var/www/building/ubuntu/conf/distributions
fi
gpg --batch --import /home/public.key /home/signing.key
service nginx start
