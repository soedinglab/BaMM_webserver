#!/bin/bash


# construct empty database
python manage.py makemigrations
python manage.py migrate

# fill db construct
echo 'BEFORE POPULATION'
 ./populate.sh
#python manage.py populate_encode DB/ DB/ENCODE.hg19.TFBS.QC.metadata.jun2012-TFs_SPP_pooled.tsv
echo 'AFTER POPULATION'
# start webserver
python manage.py runserver 0.0.0.0:10080 
