FROM ubuntu:14.04

MAINTAINER Allan Costa <allaninocencio@yahoo.com.br>

# Install dependencies
RUN apt-get update
RUN apt-get install -y wget
RUN apt-get install -y git-core
RUN apt-get install -y clang
RUN apt-get install -y cmake
RUN apt-get install -y python2.7
RUN apt-get install -y python2.7-dev
RUN apt-get install -y zlib1g-dev
RUN apt-get install -y bzip2
RUN apt-get install -y libyaml-dev
RUN apt-get install -y libyaml-0-2
RUN wget https://raw.github.com/pypa/pip/master/contrib/get-pip.py -O - | python

# Use clang
ENV CC clang
ENV CXX clang++

# Set enviroment variables needed by NuPIC
ENV NUPIC /usr/local/src/nupic
ENV NTA_DATA_PATH /usr/local/src/nupic/prediction/data

# OPF needs this
ENV USER docker

# Copy context into container file system
ADD . /usr/local/src/nupic

# Install Python dependencies
RUN pip install --allow-all-external --allow-unverified PIL --allow-unverified  psutil -r $NUPIC/external/common/requirements.txt

# Docker don't expand ENV variables!
WORKDIR /usr/local/src/nupic

# Install NuPIC with using SetupTools
RUN python setup.py install
RUN python setup.py build
RUN python setup.py develop

WORKDIR /home/docker