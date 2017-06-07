FROM python:3.4
ENV PYTHONUNBUFFERED 1

ENV APP_USER user  

RUN groupadd -r ${APP_USER} && useradd -r -g ${APP_USER} ${APP_USER}
    
WORKDIR /code

# Grabs your version of Ubuntu as a BASH variable
RUN CODENAME=`grep CODENAME /etc/lsb-release | cut -c 18-`

# Appends the CRAN repository to your sources.list file 
RUN sudo sh -c 'echo "deb http://cran.rstudio.com/bin/linux/ubuntu $CODENAME" >> /etc/apt/sources.list'

# Adds the CRAN GPG key, which is used to sign the R packages for security.
RUN sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys E084DAB9

RUN apt-get update && apt-get upgrade -y && apt-get install -y \ 
	r-base         \
	r-dev          \
	libxml2-dev    \
	libxslt-dev    \     
	libffi-dev     \
	libssl-dev     

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

