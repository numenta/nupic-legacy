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
RUN wget https://raw.github.com/pypa/pip/master/contrib/get-pip.py -O - | python

# Use clang
ENV CC clang
ENV CXX clang++

# Set enviroment variables needed by NuPIC
ENV NTA /usr/bin/nta/eng
ENV NUPIC /usr/local/src/nupic
ENV PY_VERSION 2.7
ENV PYTHONPATH $NTA/lib/python$PY_VERSION/site-packages:$PYTHONPATH
ENV NTA_DATA_PATH $NTA/share/prediction/data:$NTA_DATA_PATH

# OPF needs this
ENV USER docker

# Copy context into container file system
ADD . /usr/local/src/nupic

# Install Python dependencies
RUN pip install --allow-all-external --allow-unverified PIL --allow-unverified  psutil -r $NUPIC/external/common/requirements.txt

# Install NuPIC with CMAKE
# Generate make files with cmake
RUN mkdir $NUPIC/build_system
WORKDIR $NUPIC/build_system
RUN cmake $NUPIC

# Build with max 3 jobs/threads
RUN make -j3

# Default directory
WORKDIR /home/docker
