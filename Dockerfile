FROM python:3.4
ENV PYTHONUNBUFFERED 1

ENV APP_USER user  
ENV APP_ROOT /code

RUN groupadd -r ${APP_USER} \  
    && useradd -r -m \
    --home-dir ${APP_ROOT} \
    -s /usr/sbin/nologin \
    -g ${APP_USER} ${APP_USER}
    
    
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

RUN chmod -R ugo+rwx .

USER ${APP_USER}  
ADD bammmotif/ /code/ 
ADD webserver/ /code/ 
ADD *.sh /code/
ADD *.py /code/


