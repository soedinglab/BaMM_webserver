
# Starting the webserver

## Preparing the database directories on the host

All persistent data will be stored on the host. I am using the directory `/var/webserver`. Make sure to choose a folder in which your BaMM user account has read/write access.

```bash
WEBSERVER_DIR=/var/webserver
# create folder structure
mkdir -p $WEBSERVER_DIR/{media_db,logs,motif_db,mysql_db,redis_db}

cd $WEBSERVER_DIR
git clone git@github.com:soedinglab/BaMM_webserver.git

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


DB_HOST=db
DB_NAME=webserver
DB_PORT=3306
DB_USER=root
MYSQL_PASSWORD=3aMM!mot1f
MYSQL_ROOT_PASSWORD=3aMM!mot1f

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

## Setting up the motif databases

Download the motif databases from [http://wwwuser.gwdg.de/~compbiol/bamm/](http://wwwuser.gwdg.de/~compbiol/bamm/), extract the databases into the database directory `/var/webserver/motif_db`.

The first level of motif_db might now look like this:

```
motif_db
├── gtrd_mouse_v1801
└── remap2018_human
```

## Building the webserver
Now use `docker-compose build` to download and build all docker images.

## Starting the webserver
After successfully building the webserver, use `docker-compose up` to start the webserver. In case you see errors related to mysql stop the server by `ctrl-C` and let is shut down gracefully and restart with `docker-compose up`. The error should be gone.

## Profit

Now you should be able to access the webserver at  `0.0.0.0:10080` in your favorite browser.

# Notes and caveats

## General notes

* docker-compose build commands always have to be started from the root of the git repository of the webserver
* all files created by the webserver are accessible on the host in `$WEBSERVER_DIR/media_db`

## Developer notes

* whenever you change the models, you have to restart the server. Django will create a database migration automatically. These migrations are under version control and should be committed to the git repository
* Sometimes building the migrations needs user input. In this case, use `docker exec -it bammmwebserver_web_1 bash` to jump into the webserver container and run the migration commands manually. You can find the code in `run_web.sh`.

## Notes for setting up the server on marvin
* the server is run by the user `bammmotif_admin`. You can find the current version in `/opt/bamm_server`
* Configuration in `.env` (**VERY IMPORTANT, please double check this**. Wrong configuration will lead to password leaks)
  - make sure `DJANGO_DEBUG` is not defined. Otherwise the server will run in debug mode and leak sensitive information
  - set `ALLOWED_HOSTS=bammmotif.mpibpc.mpg.de`
  - set `UID=BAMM_USER_UID=1002`
* `/etc/nginx/sites-available/bammmotif.mpibpc.mpg.de` has to edited to allow access to static data. See the template on the server
* all files and subdirectories in `motif_db` require group and other permissions. (755 on directories, 644 on files)
