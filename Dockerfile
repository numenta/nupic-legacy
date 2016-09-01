# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2016, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Affero Public License for more details.
#
# You should have received a copy of the GNU Affero Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------

FROM ubuntu:14.04

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
RUN wget http://releases.numenta.org/pip/1ebd3cb7a5a3073058d0c9552ab074bd/get-pip.py -O - | python
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

# Set up nupic.core
RUN pip install numpy pycapnp
RUN git clone https://github.com/numenta/nupic.core /usr/local/src/nupic.core
WORKDIR /usr/local/src/nupic.core
RUN mkdir -p build/scripts
WORKDIR /usr/local/src/nupic.core/build/scripts
RUN cmake -DCMAKE_BUILD_TYPE=Debug -DCMAKE_INSTALL_PREFIX=../release -DPY_EXTENSIONS_DIR=../../bindings/py/nupic/bindings ../..
RUN make install
WORKDIR /usr/local/src/nupic.core
RUN python setup.py install

# Copy context into container file system
ADD . $NUPIC

WORKDIR /usr/local/src/nupic

# Install NuPIC with using SetupTools
RUN python setup.py install

WORKDIR /home/docker
