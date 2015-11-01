FROM ubuntu:14.04

MAINTAINER Allan Costa <allaninocencio@yahoo.com.br>

# Install dependencies
RUN apt-get update
RUN apt-get install -y wget git-core build-essential python2.7 python 2.7-dev
RUN wget https://raw.github.com/pypa/pip/master/contrib/get-pip.py -O - | python
RUN pip install --upgrade setuptools
RUN pip install wheel

# Use gcc to match nupic.core binary
ENV CC gcc
ENV CXX g++

# Install capnproto from source
RUN wget https://capnproto.org/capnproto-c++-0.5.2.tar.gz && \
    tar zxf capnproto-c++-0.5.2.tar.gz && \
    cd capnproto-c++-0.5.2 && \
    ./configure && \
    make check && \
    make install

# Set enviroment variables needed by NuPIC
ENV NUPIC /usr/local/src/nupic
ENV NTA_DATA_PATH /usr/local/src/nupic/prediction/data

# OPF needs this
ENV USER docker

# Copy context into container file system
ADD . $NUPIC

WORKDIR /usr/local/src/nupic

# Install nupic.bindings
RUN pip install https://s3-us-west-2.amazonaws.com/artifacts.numenta.org/numenta/nupic.core/releases/nupic.bindings/nupic.bindings-`git grep nupic.bindings\=\= -- external/common/requirements.txt | cut -d ':' -f 2 | sed "s/nupic\.bindings\=\=//"`-cp27-none-linux_x86_64.whl

# Install NuPIC with using SetupTools
RUN python setup.py install

WORKDIR /home/docker
