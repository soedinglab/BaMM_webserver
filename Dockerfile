FROM python:3.4
ENV PYTHONUNBUFFERED 1

ENV APP_USER user  

RUN groupadd -r ${APP_USER} && useradd -r -g ${APP_USER} ${APP_USER}
    
WORKDIR /code

RUN apt-get update && apt-get upgrade -y && apt-get install -y \ 
	r-base         \
	libxml2-dev    \
	libxslt-dev    \     
	libffi-dev     \
	libssl-dev     

# install python dependencies
ADD requirements.txt /code/
RUN pip install -r /code/requirements.txt

# install r packages
ADD	install_packages.R /code/
RUN	R --vanilla < /code/install_packages.R

USER ${APP_USER}

ADD bammmotif/ /code/ 
ADD webserver/ /code/ 
ADD DB/ /code/
ADD *.sh /code/
ADD *.py /code/

