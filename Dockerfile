FROM ubuntu

MAINTAINER Allan Costa <allaninocencio@yahoo.com.br>

# Install dependencies
RUN \
    echo "deb http://archive.ubuntu.com/ubuntu precise main universe" > /etc/apt/sources.list;\
    apt-get update;\
    apt-get install -y wget;\
    apt-get install -y git-core;\
    apt-get install -y build-essential;\
    apt-get install -y python2.7;\
    apt-get install -y python-dev;\
    apt-get install -y libtool;\
    apt-get install -y automake;\
    wget https://bitbucket.org/pypa/setuptools/raw/bootstrap/ez_setup.py -O - | python;\
    wget https://raw.github.com/pypa/pip/master/contrib/get-pip.py -O - | python;\
#RUN

# Clone NuPIC repository (takes some time)
RUN git clone https://github.com/numenta/nupic.git /usr/local/src/nupic

# Set enviroment variables needed by NuPIC builder
ENV NTA /usr/bin/nta/eng
ENV NUPIC /usr/local/src/nupic
ENV BUILDDIR /tmp/ntabuild
ENV MK_JOBS 3

# More enviroment variables (setted originally by $NUPIC/env.sh)
ENV PY_VERSION 2.7
ENV PATH $NTA/bin:$PATH
ENV PYTHONPATH $NTA/lib/python$PY_VERSION/site-packages:$PYTHONPATH
ENV NTA_ROOTDIR $NTA
ENV NTA_DATA_PATH $NTA/share/prediction/data:$NTA_DATA_PATH
ENV LDIR $NTA/lib
ENV LD_LIBRARY_PATH $LDIR

# Install Python dependencies
RUN pip install --allow-all-external --allow-unverified PIL --allow-unverified  psutil -r $NUPIC/external/common/requirements.txt

# Install NuPIC
RUN $NUPIC/build.sh

# Cleanup
RUN rm setuptools*

# OPF needs this (It's a workaround. We can create a user, but I wanted to keep this image clean to use as base to my projects)
ENV USER docker

# Default directory
WORKDIR /home/docker
