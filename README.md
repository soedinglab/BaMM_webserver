
# Starting the webserver

## Preparing the database directories on the host

All persistent data will be stored on the host. I am using the directory `~/webserver`.

```bash
WEBSERVER_DIR=~/webserver
# create folder structure
mkdir -p $WEBSERVER_DIR/{media_db/logs,mysql_db,redis_db}

cd $WEBSERVER_DIR
git clone git@github.com:soedinglab/BaMM_webserver.git
git submodule init
git submodule update
```

## Setting the environment variables for docker-compose
Move to a folder of your choice and clone the webserver again.

```bash
cd ~/git_repositories
git clone git@github.com:soedinglab/BaMM_webserver.git
git submodule init
git submodule update

cd BaMM_webserver
cp .env_template .env
```

open `.env` with an editor of your choice and set the variables:

```
BAMM_USER_UID=1000

MYSQL_PASSWORD=3aMM!mot1f
MYSQL_ROOT_PASSWORD=3aMM!mot1f
NETWORK_PREFIX=172.12.12

MYSQL_DB_DIR=~/webserver/mysql_db
REDIS_DB_DIR=~/webserver/redis_db
WEBSERVER_DIR=~/webserver/BaMM_webserver
MEDIA_DIR=~/webserver/media_db
```

Make sure `BAMM_USER_UID` matches the UID of your user account. You can find your UID by executing `echo $UID` in the shell.

## Building and starting the webserver
Now use `docker-compose build` to download and build all docker images.

After successfully building the webserver, use `docker-compose up` to start the webserver. In case you see errors related to mysql stop the server by `ctrl-C` and let is shut down gracefully and restart with `docker-compose up`. The error should be gone.

## Profit

Now you should be able to access the webserver at  `0.0.0.0:10080` in your favorite browser.

## Noteworthy things

* The webserver code inside the container is in `WEBSERVER_DIR/BaMM_webserver`. Changes to that code should be automatically be available in the server. The webserver has to be started from `~/git_repositories/BaMM_webserver` however.
* All files created by the webserver are accessible on the host in `~/webserver/media_db`
