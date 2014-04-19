FROM ubuntu

MAINTAINER Allan Costa <allaninocencio@yahoo.com.br>

# Install dependencies
RUN echo "deb http://archive.ubuntu.com/ubuntu trusty main universe" > /etc/apt/sources.list
RUN apt-get update
RUN apt-get install -y wget
RUN apt-get install -y git-core
RUN apt-get install -y build-essential
RUN apt-get install -y clang
RUN apt-get install -y cmake
RUN apt-get install -y python2.7
RUN apt-get install -y python2.7-dev
RUN apt-get install -y zlib1g-dev
RUN apt-get install -y bzip2
RUN apt-get install -y libyaml-dev
RUN apt-get install -y libyaml-0-2
RUN wget https://bitbucket.org/pypa/setuptools/raw/bootstrap/ez_setup.py -O - | python
RUN wget https://raw.github.com/pypa/pip/master/contrib/get-pip.py -O - | python

# Set enviroment variables needed by NuPIC builder
ENV CC clang
ENV CXX clang++
ENV NTA /usr/bin/nta/eng
ENV NUPIC /usr/local/src/nupic
ENV BUILDDIR /tmp/ntabuild

# Clone NuPIC repository (takes some time)
ADD . $NUPIC

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

# Install Nupic with CMAKE
# Generate make files with cmake
RUN mkdir $NUPIC/build_system
WORKDIR $NUPIC/build_system
RUN cmake $NUPIC

# Build with max 3 jobs/threads
RUN make

# Cleanup
RUN rm /setuptools*

# OPF needs this (It's a workaround. We can create a user, but I wanted to keep this image clean to use as base to my projects)
ENV USER docker

# Default directory
WORKDIR /home/docker
