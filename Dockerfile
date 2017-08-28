FROM python:3.5
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
COPY requirements.txt /code/
RUN pip install -r /code/requirements.txt

# install r packages
COPY	install_packages.R /code/
RUN	R --vanilla < /code/install_packages.R

RUN mkdir /code/media/
# add BaMMmotif Pengmotif and plotFDR_rannk.R to Path variable for PEnGMotif
ENV PATH="${PATH}:/code/bammmotif/static/scripts/bamm-private/build/BaMMmotif/"
ENV PATH="${PATH}:/code/bammmotif/static/scripts/bamm-private/R/"
ENV PATH="${PATH}:/code/bammmotif/static/scripts/PEnG-motif/build/bin/"

COPY bammmotif/ /code/ 
COPY webserver/ /code/ 
COPY example_data/ExampleData.fasta /code/example_data/ExampleData.fasta
COPY example_data/result/ /code/media/293aae88-6e1e-48ba-ad87-19e7304e0391/
COPY DB/ /code/
COPY *.sh /code/
COPY *.py /code/

RUN chown -R ${APP_USER}:${APP_USER} /code
USER ${APP_USER}
