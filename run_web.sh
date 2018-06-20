#!/bin/bash

set -e
# Wait for mysql to start
echo Waiting $MYSQL_STARTUP_DELAY_SECONDS seconds before webserver startup
sleep $MYSQL_STARTUP_DELAY_SECONDS

# construct empty database
python3 manage.py makemigrations
python3 manage.py makemigrations bammmotif
python3 manage.py migrate
python3 manage.py sync_databases

if [[ "$FORCE_EXAMPLE_CREATION" == "1" ]]; then
	python3 manage.py run_examples --flush &
else
	python3 manage.py run_examples &
fi


# start webserver
python3 manage.py runserver 0.0.0.0:10080
