#!/bin/bash

# Wait for mysql to start
echo Waiting $MYSQL_STARTUP_DELAY_SECONDS seconds before webserver startup
sleep $MYSQL_STARTUP_DELAY_SECONDS

# construct empty database
python manage.py makemigrations
python manage.py migrate
python manage.py sync_databases

python manage.py run_examples &

# start webserver
python manage.py runserver 0.0.0.0:10080
