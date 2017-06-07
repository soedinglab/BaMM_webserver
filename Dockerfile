FROM python:3.4
ENV PYTHONUNBUFFERED 1

ENV APP_USER user
ENV R_BASE_VERSION 3.3.1  

RUN groupadd -r ${APP_USER} && useradd -r -g ${APP_USER} ${APP_USER}
    
WORKDIR /code

RUN apt-get update && apt-get upgrade -y && apt-get install -y \ 
	libxml2-dev    \
	libxslt-dev    \     
	libffi-dev     \
	libssl-dev     

# install R
RUN apt-get update && apt-get install -t unstable -y --no-install-recommends \
		littler \
        r-cran-littler \
		r-base=${R_BASE_VERSION}* \
		r-base-dev=${R_BASE_VERSION}* \
		r-recommended=${R_BASE_VERSION}* \
        && echo 'options(repos = c(CRAN = "https://cran.rstudio.com/"), download.file.method = "libcurl")' >> /etc/R/Rprofile.site \
        && echo 'source("/etc/R/Rprofile.site")' >> /etc/littler.r \
	&& ln -s /usr/share/doc/littler/examples/install.r /usr/local/bin/install.r \
	&& ln -s /usr/share/doc/littler/examples/install2.r /usr/local/bin/install2.r \
	&& ln -s /usr/share/doc/littler/examples/installGithub.r /usr/local/bin/installGithub.r \
	&& ln -s /usr/share/doc/littler/examples/testInstalled.r /usr/local/bin/testInstalled.r \
	&& install.r docopt \
	&& rm -rf /tmp/downloaded_packages/ /tmp/*.rds \
	&& rm -rf /var/lib/apt/lists/*


# install python dependencies
COPY requirements.txt /code/
RUN pip install -r /code/requirements.txt

# install r packages
COPY	install_packages.R /code/
RUN	R --vanilla < /code/install_packages.R

USER ${APP_USER}

COPY bammmotif/ /code/ 
COPY webserver/ /code/ 
COPY DB/ /code/
COPY *.sh /code/
COPY *.py /code/

