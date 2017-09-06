FROM python:3.5
ENV PYTHONUNBUFFERED 1

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

RUN apt-get install -y \
	cmake\
	build-essential\
	libboost-all-dev

RUN mkdir -p /ext/bin

ADD tools/bamm /tmp/bamm
RUN cd /tmp/bamm && mkdir build && cd build && cmake .. && make
RUN cp /tmp/bamm/build/BaMMmotif/BaMMmotif /ext/bin
RUN cp /tmp/bamm/R/* /ext/bin
RUN rm -rf /tmp/bamm

ADD tools/suite /tmp/suite
RUN mkdir -p /tmp/suite/build
RUN cd /tmp/suite/build && cmake -DCMAKE_INSTALL_PREFIX:PATH=/ext .. && make install
RUN pip install /tmp/suite/bamm-suite-py
RUN rm -rf /tmp/suite

ENV PATH="/ext/bin:${PATH}"
