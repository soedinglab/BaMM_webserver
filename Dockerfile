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
RUN cd /tmp/bamm && mkdir -p build && cd build && cmake .. && make
RUN cp /tmp/bamm/build/bin/* /ext/bin
RUN cp /tmp/bamm/R/* /ext/bin
RUN rm -rf /tmp/bamm

ADD tools/suite /tmp/suite
RUN mkdir -p /tmp/suite/build
RUN cd /tmp/suite/build && cmake -DCMAKE_INSTALL_PREFIX:PATH=/ext .. && make install >/dev/null 2>/dev/null
RUN pip install /tmp/suite/bamm-suite-py
RUN rm -rf /tmp/suite


ENV PATH="/ext/bin:${PATH}"
