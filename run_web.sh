#!/bin/bash


# construct empty database
yes | python manage.py makemigrations
python manage.py migrate

python manage.py sync_databases

# fill db construct (only use this when setting up webserver on completely new environment!)
# ./populate.sh

# start webserver
python manage.py runserver 0.0.0.0:10080 
