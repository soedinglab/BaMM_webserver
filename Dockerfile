FROM python:3.5
ENV PYTHONUNBUFFERED 1

WORKDIR /code

RUN apt-get update && apt-get upgrade -y && apt-get install -y \
	r-base          \
	libxml2-dev     \
	libxslt-dev     \
	libffi-dev      \
	libssl-dev      \ 
    libboost-all-dev\
    cmake           \
    imagemagick     \
    ghostscript     \
    build-essential 

# install python dependencies
COPY requirements.txt /code/
RUN pip install -r /code/requirements.txt

# install r packages
COPY	install_packages.R /code/
# silent output due to docker-compose unicode issue
RUN	Rscript /code/install_packages.R >/dev/null 2>/dev/null

RUN mkdir /code/media/
RUN mkdir -p /ext/bin

ADD tools/bamm /tmp/bamm
RUN cd /tmp/bamm && mkdir -p build && cd build && cmake .. && make -j8
RUN cp /tmp/bamm/build/bin/* /ext/bin
RUN cp /tmp/bamm/R/* /ext/bin
RUN rm -rf /tmp/bamm

ADD tools/suite /tmp/suite
RUN mkdir -p /tmp/suite/build
RUN cd /tmp/suite/build && CXXFLAGS=-std=c++1y cmake -DCMAKE_INSTALL_PREFIX:PATH=/ext .. && make -j8 install
RUN pip install /tmp/suite/bamm-suite-py
RUN rm -rf /tmp/suite

# use a cool init system for handing signals: https://github.com/Yelp/dumb-init
RUN wget -O /usr/local/bin/dumb-init https://github.com/Yelp/dumb-init/releases/download/v1.2.1/dumb-init_1.2.1_amd64
RUN chmod +x /usr/local/bin/dumb-init

ENV PATH="/ext/bin:${PATH}"
