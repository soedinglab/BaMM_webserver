#!/bin/bash

# wait for database to start up first
#echo "import pty; pty.spawn('/bin/bash')" 
#echo "import pty; pty.spawn('/bin/bash')" > /tmp/asdf.py
#python /tmp/asdf.py
#echo "ran python " 
# prepare init migration
#su -m user -c "python manage.py makemigrations" -p passw
# migrate db, so we have the latest db schema
#su -m user -c "python manage.py migrate"  
# start development server on public ip interface, on port 8000
#su -m user -c "python manage.py runserver 0.0.0.0:8000"  

echo "THIS IS THE USER:-->"$USER"#####"
# start webserver
python manage.py makemigrations
python manage.py migrate
python manage.py runserver 0.0.0.0:10080
