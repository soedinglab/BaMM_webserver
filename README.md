# BaMM web server
[![License](https://img.shields.io/github/license/soedinglab/BaMM_webserver.svg)](https://choosealicense.com/licenses/agpl-3.0/) [![Documentation Status](https://readthedocs.org/projects/bammserver/badge/?version=latest)](http://bammserver.readthedocs.io/en/latest/?badge=latest)

This repository contains the source code of the BaMM web server. A bioinformatic resource for analysis of nucleotide binding proteins with higher-order Bayesian Markov Models (BaMMs).

## News
* 2017/03/07 - We fixed a bug in the interface causing a 500 error when running the seeding stage in single-strand mode.


## Setting up the webserver locally

### Preparing the database directories on the host

All persistent data will be stored on the host. I am using the directory `/var/webserver`. Make sure to choose a folder in which your BaMM user account has read/write access.

```bash
WEBSERVER_DIR=/var/webserver
# create folder structure
mkdir -p $WEBSERVER_DIR/{media_db,logs,motif_db,mysql_db,redis_db}

cd $WEBSERVER_DIR
git clone https://github.com/soedinglab/BaMM_webserver.git

cd  BaMM_webserver
git submodule update --init --recursive
```


### Configuring the webserver
```
cd $WEBSERVER_DIR/BaMM_webserver
cp .env_template .env
```

open `.env` with an editor of your choice and set the variables:

```
BAMM_USER_UID=1000


DB_HOST=db
DB_NAME=webserver
DB_PORT=3306
DB_USER=root
MYSQL_PASSWORD=verysecurepassword
MYSQL_ROOT_PASSWORD=verysecurepassword

NETWORK_PREFIX=172.12.12

# Data PATHS, make sure they are owned by the BAMM_USER_UID

MYSQL_DB_DIR=/var/webserver/mysql_db
REDIS_DB_DIR=/var/webserver/redis_db
WEBSERVER_DIR=/var/webserver/BaMM_webserver
MEDIA_DIR=/var/webserver/media_db
LOG_DIR=/var/webserver/logs
MOTIF_DB_DIR=/var/webserver/motif_db

# general settings
DJANGO_DEBUG=1
BAMM_LOG_LEVEL=DEBUG
SECRET_KEY=someverylongrandomstringthatisverynecessaryforhighsecurity
ALLOWED_HOSTS=0.0.0.0

MYSQL_STARTUP_DELAY_SECONDS=5
EXAMPLE_MOTIF_DB=remap2018_human
```

Make sure `BAMM_USER_UID` matches the UID of your user account. You can find your UID by executing `echo $UID` in the shell.

If done correctly, `docker-compose config` does not print any warnings.

### Setting up the motif databases

Download the motif databases from [http://wwwuser.gwdg.de/~compbiol/bamm/](http://wwwuser.gwdg.de/~compbiol/bamm/), extract the databases into the database directory `/var/webserver/motif_db`.

The first level of motif_db might now look like this:

```
motif_db
├── gtrd_mouse_v1801
└── remap2018_human
```

### Building the webserver
Now use `docker-compose build` to download and build all docker images.

### Starting the webserver
After successfully building the webserver, use `docker-compose up` to start the webserver. In case you see errors related to mysql stop the server by `ctrl-C` and let is shut down gracefully and restart with `docker-compose up`. The error should be gone.

### Profit

Now you should be able to access the webserver at `0.0.0.0:10080` in your favorite browser.

## Notes and caveats

### General notes

* docker-compose build commands always have to be started from the root of the git repository of the webserver
* all files created by the webserver are accessible on the host in `$WEBSERVER_DIR/media_db`

### Developer notes
* whenever you change the models, you have to restart the server. Django will create a database migration automatically. These migrations are under version control and should be committed to the git repository
* Sometimes building the migrations needs user input. In this case, use `docker exec -it bammmwebserver_web_1 bash` to jump into the webserver container and run the migration commands manually. You can find the code in `run_web.sh`.

### Setting up the server in production
We strongly advice against running your own publicly accessible webserver without first reading the django documentation carefully. Failure in doing so can lead to a insecure server.

## License

The BaMMserver code can be used, distributed and modified under the GNU Affero General Public License v3.0 ([GNU AGPLv3](https://choosealicense.com/licenses/agpl-3.0/))
