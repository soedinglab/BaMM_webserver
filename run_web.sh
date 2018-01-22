#!/bin/bash

# Wait for mysql to start
MYSQL_STARTUP_WAIT_TIME=5
if [ -f MYSQL_STARTUP_TIME ]
then
    MYSQL_STARTUP_WAIT_TIME=`cat MYSQL_STARTUP_TIME`
fi

sleep $MYSQL_STARTUP_WAIT_TIME

# construct empty database
python manage.py makemigrations
python manage.py migrate

# fill db construct (only use this when setting up webserver on completely new environment!)
if [ ! -f POPULATED ]
then
    ./populate.sh
    touch POPULATED
fi

# start webserver
python manage.py runserver 0.0.0.0:10080
