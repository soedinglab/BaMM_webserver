#!/bin/bash

set -e
# Wait for mysql to start
echo Waiting $MYSQL_STARTUP_DELAY_SECONDS seconds before webserver startup
sleep $MYSQL_STARTUP_DELAY_SECONDS

# construct empty database
python manage.py makemigrations
python manage.py makemigrations bammmotif
python manage.py migrate
python manage.py sync_databases

if [[ "$FORCE_EXAMPLE_CREATION" == "1" ]]; then
	python manage.py run_examples --flush &
else
	python manage.py run_examples &
fi


# start webserver
python manage.py runserver 0.0.0.0:10080
