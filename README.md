# BaMM web server
[![License](https://img.shields.io/github/license/soedinglab/BaMM_webserver.svg)](https://choosealicense.com/licenses/agpl-3.0/)
[![Documentation Status](https://readthedocs.org/projects/bammserver/badge/?version=latest)](http://bammserver.readthedocs.io/en/latest/?badge=latest)
[![Issues](https://img.shields.io/github/issues/soedinglab/BaMM_webserver.svg)](https://github.com/soedinglab/BaMM_webserver/issues)

This repository contains the source code of the [BaMM web server](https://bammmotif.mpibpc.mpg.de/). A bioinformatic resource for analysis of nucleotide binding proteins with higher-order Bayesian Markov Models (BaMMs).

## News
* **2017/05/06**- We fixed a couple of edge cases, improved the input validation and alert the user if we suspect that refined motifs in the de-novo workflow may not be the actual motif.
* **2018/04/22**- We are happy to present a massively improved version. Highlights are a drastic speed improvement, a standalone one-step denovo workflow, estimation of the motif occurrence from the data, a cleaner user interface, a list of recently submitted jobs, and much more. We would like to thank our reviewers for their helpful suggestions for improving the server.
* **2018/03/07** - We fixed a bug in the interface causing a 500 error when running the seeding stage in single-strand mode.


## Setting up the webserver locally

### 1) Preparing the database directories on the host

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

### 2) Setting up the motif databases

Download the motif databases from [http://wwwuser.gwdg.de/~compbiol/bamm/](http://wwwuser.gwdg.de/~compbiol/bamm/), extract the databases into the database directory `/var/webserver/motif_db`.

Here I chose `gtrd_mouse_BaMMv102.zip` and `remap2018_human_BAMMv102.zip`. The first level of motif_db now looks like this:

```
motif_db
├── gtrd_mouse_v1801
└── remap2018_human
```

### 3) Configuring the webserver
```
cd $WEBSERVER_DIR/BaMM_webserver
cp .env_template .env
```

Now open `.env` with your favorite editor and adapt the server configuration to your system.

Please make sure that
- `DEFAULT_MOTIF_DB` is set to a database present in `/var/webserver/motif_db`
- `BAMM_USER_UID` matches the UID of the user account that owns the webserver files. You can find your UID by typing `echo $UID` in the shell.

If you are done, you can double check the settings by running `docker-compose config`. You should not see any warnings.

### 4) Building the webserver
Now you can build the webserver by running `docker-compose build` from the root of `$WEBSERVER_DIR/BaMM_webserver`

### 5) Starting the webserver
After successfully building, the webserver can be started typing `docker-compose up`. In case you see errors related to mysql migrations try stopping the server by `ctrl-C` and let is shut down gracefully, then restart by `docker-compose up`. The error should be gone.

Now you should be able to access the webserver at `0.0.0.0:10080` in your favorite browser.

---

## Notes and caveats

### General notes

* docker-compose build commands always have to be started from the root of the git repository of the webserver
* all files created by the webserver are accessible on the host in `$WEBSERVER_DIR/media_db`

### Developer notes
* whenever you change the models, you have to restart the server. Django will create a database migration automatically. These migrations are under version control and should be committed to the git repository
* Sometimes building the migrations needs user input. In this case, use `docker exec -it bammmwebserver_web_1 bash` to jump into the webserver container and run the migration commands manually. You can find the migration commands in `run_web.sh`.

### Setting up the server in production
We strongly advice against running your own publicly accessible webserver without familiarizing yourself the django documentation. Failure in doing so can lead to an insecure server.

## License

The BaMMserver code can be used, distributed and modified under the GNU Affero General Public License v3.0 ([GNU AGPLv3](https://choosealicense.com/licenses/agpl-3.0/))
