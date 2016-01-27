FROM ubuntu:14.04

MAINTAINER Allan Costa <allaninocencio@yahoo.com.br>

# Install dependencies
RUN apt-get update && \
    apt-get install -y \
    curl \
    wget \
    git-core \
    gcc \
    g++ \
    cmake \
    python \
    python2.7 \
    python2.7-dev \
    zlib1g-dev \
    bzip2 \
    libyaml-dev \
    libyaml-0-2
RUN wget https://bootstrap.pypa.io/get-pip.py -O - | python
RUN pip install --upgrade setuptools
RUN pip install wheel

# Use gcc to match nupic.core binary
ENV CC gcc
ENV CXX g++

# Set enviroment variables needed by NuPIC
ENV NUPIC /usr/local/src/nupic
ENV NTA_DATA_PATH /usr/local/src/nupic/prediction/data

# OPF needs this
ENV USER docker

# Copy context into container file system
ADD . $NUPIC

WORKDIR /usr/local/src

# Clone nupic.core
RUN git clone `head -n 2 $NUPIC/.nupic_modules | tail -n 1 | sed -r "s/NUPIC_CORE_REMOTE = '(.+)'/\\1/"` && \
    cd nupic.core && \
    git reset --hard `head -n 3 $NUPIC/.nupic_modules | tail -n 1 | sed -r "s/NUPIC_CORE_COMMITISH = '(.+)'/\\1/"`

WORKDIR /usr/local/src/nupic.core

# Build nupic.core
RUN pip install \
        --cache-dir /usr/local/src/nupic.core/pip-cache \
        --build /usr/local/src/nupic.core/pip-build \
        --no-clean \
        pycapnp==0.5.5 \
        -r bindings/py/requirements.txt && \
    python setup.py install

WORKDIR /usr/local/src/nupic

# Install NuPIC with using SetupTools
RUN python setup.py install

WORKDIR /home/docker
