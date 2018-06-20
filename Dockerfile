FROM alpine
ENV PYTHONUNBUFFERED 1

WORKDIR /code

RUN apk add --no-cache --update\
  python3-dev\
  boost-dev\
  cmake\
  mysql-client\
  g++\
  supervisor\
  make\
  freetype-dev\
  R\
  R-dev\
  bash\
  sed\
  vim\
  zip

RUN pip3 install --no-cache-dir numpy scipy pandas matplotlib

# use a cool init system for handing signals: https://github.com/Yelp/dumb-init
RUN wget -O /usr/local/bin/dumb-init https://github.com/Yelp/dumb-init/releases/download/v1.2.1/dumb-init_1.2.1_amd64
RUN chmod +x /usr/local/bin/dumb-init

# install python dependencies

COPY requirements.txt /code/
RUN apk add --no-cache --virtual .build-deps mariadb-dev \
    && pip3 install --no-cache-dir -r /code/requirements.txt\
    && apk add --virtual .runtime-deps mariadb-client-libs \
    && apk del .build-deps
  
# install r packages
COPY install_packages.R /code/

RUN Rscript /code/install_packages.R

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
RUN pip3 install /tmp/suite/bamm-suite-py
RUN rm -rf /tmp/suite

RUN apk --update add fontconfig ttf-dejavu
RUN sed -i 's~#!/usr/bin/env python~#!/usr/bin/env python3~g' /ext/bin/*.py
ENV PATH="/ext/bin:${PATH}"
ENV PATH="/usr/local/bin:${PATH}"
