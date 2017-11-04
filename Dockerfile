FROM python:3.5
ENV PYTHONUNBUFFERED 1

WORKDIR /code

ENV MEME_VERSION=4.12.0

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
# add BaMMmotif Pengmotif and plotFDR_rannk.R to Path variable for PEnGMotif
ENV PATH="${PATH}:/code/bammmotif/static/scripts/bamm-private/build/BaMMmotif/"
ENV PATH="${PATH}:/code/bammmotif/static/scripts/bamm-private/R/"
ENV PATH="${PATH}:/code/bammmotif/static/scripts/PEnG-motif/build/bin/"
ENV PATH="${PATH}:/code/tools/suite/PEnG-motif/scripts/"

RUN apt-get install -y \
	cmake\
	build-essential\
	libboost-all-dev

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

ADD tools/meme_suite /tmp/meme_suite
RUN cp tools/meme_suite/meme_4.12.0.tar.gz /tmp/meme_suite
RUN cd /tmp/meme_suite
RUN tar xfvz meme_4.12.0.tar.gz
RUN cd meme_4.12.0
RUN ./configure --prefix=/tmp/meme-suite/meme --with-url=http://meme-suite.org --enable-build-libxml2 --enable-build-libxslt
RUN make && make test && make install
RUN cp meme/ceqlogo /ext/bin
RUN rm -rf /tmp/meme_suite


# Note: NOT ALL OF MEME-SUITES TOOLS INSTALL CORRECTLY. For now this is fine, since we are only interested in plotting.
# http://meme-suite.org/meme-software/4.12.0/meme_4.12.0.tar.gz
#ADD tools/meme_suite /tmp/meme_suite
#RUN cd /tmp/meme_suite && tar xfv meme_4.12.0.tar.gz
RUN mkdir -p /tmp/meme_suite
RUN cd /tmp/meme_suite && \
    wget http://meme-suite.org/meme-software/${MEME_VERSION}/meme_${MEME_VERSION}.tar.gz && \
    tar xfvz meme_${MEME_VERSION}.tar.gz && \
    cd meme_${MEME_VERSION} && \
    ./configure --prefix=/ext/meme --with-url=http://meme-suite.org --enable-build-libxml2 --enable-build-libxslt --enable-serial  && \
    make && \
    make install
RUN cp /ext/meme/bin/ceqlogo /ext/bin
RUN rm -rf /tmp/meme_suite

ENV PATH="/ext/bin:${PATH}"
