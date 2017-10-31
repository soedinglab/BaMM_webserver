
# Starting the webserver

## Preparing the database directories on the host

All persistent data will be stored on the host. I am using the directory `/var/webserver`. Make sure to choose a folder in which your BaMM user account has read/write access.

```bash
WEBSERVER_DIR=/var/webserver
# create folder structure
mkdir -p $WEBSERVER_DIR/{media_db/logs,mysql_db,redis_db}

cd $WEBSERVER_DIR
git clone git@github.com:soedinglab/BaMM_webserver.git
## When working on Marvin use ssh conection (because NginX only allows ssh)
# git clone ssh://git@ssh.github.com:443/soedinglab/BaMM_webserver.git

cd  BaMM_webserver
git checkout fixit
git pull origin fixit
git submodule update --init --recursive
```

## Setting the environment variables for docker-compose
Move to a folder of your choice and clone the webserver again.

```bash
## this is not necessarily needed
cd ~/git_repositories
git clone git@github.com:soedinglab/BaMM_webserver.git
cd BaMM_webserver
git submodule update --init --recursive
cp .env_template .env
```

open `.env` with an editor of your choice and set the variables:

```
BAMM_USER_UID=1000

MYSQL_PASSWORD=3aMM!mot1f
MYSQL_ROOT_PASSWORD=3aMM!mot1f
NETWORK_PREFIX=172.12.12


WEBSERVER_DIR=/var/webserver/BaMM_webserver
MYSQL_DB_DIR=/var/webserver/mysql_db
REDIS_DB_DIR=/var/webserver/redis_db
MEDIA_DIR=/var/webserver/media_db
DB_DIR=/var/webserver/BaMM_webserver/DB
```

Make sure `BAMM_USER_UID` matches the UID of your user account. You can find your UID by executing `echo $UID` in the shell.

The DB_DIR needs to direct to the location of the folder where you have stored the database, so the folder which currently contains:

```
ENCODE.hg19.TFBS.QC.metadata.jun2012-TFs_SPP_pooled.tsv
ENCODE_ChIPseq/Results/
```

## Building and starting the webserver
Now use `docker-compose build` to download and build all docker images.

## Populating the database
When starting the webserver for the very first time comment in `populate.sh` (line 9) in the file `run_web.sh`. This will fill the mysql database updon running `docker-compose up`. NOTE: this should only be done the very first time when you start your webserver, because a repeated call of populate.sh will lead to redundancies in the database. AFTER having started t he webserver for the first time please comment out `populate.sh`(line 9) in the file `run_web.sh`again.

## Starting the webserver
After successfully building the webserver, use `docker-compose up` to start the webserver. In case you see errors related to mysql stop the server by `ctrl-C` and let is shut down gracefully and restart with `docker-compose up`. The error should be gone.

## Profit

Now you should be able to access the webserver at  `0.0.0.0:10080` in your favorite browser.

## Noteworthy things

* The webserver code inside the container is in `$WEBSERVER_DIR/BaMM_webserver`. Changes to that code should be automatically be available in the server. The webserver has to be started from `~/git_repositories/BaMM_webserver` however.
* All files created by the webserver are accessible on the host in `$WEBSERVER_DIR/media_db`
* If the database layout in the models.py file is changed, one hack to apply these changes is:
** docker-compose down
** remove everything in media_db, redis_db and mysql_db
** docker-compose up; "wait until the database is rebuilt"
** docker-compose down
** Now you can use the docker container as usual with docker-compose up
