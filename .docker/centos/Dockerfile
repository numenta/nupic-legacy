FROM centos:latest
MAINTAINER Austin Marshall <amarshall@numenta.com>

RUN rpm -Uvh http://download.fedoraproject.org/pub/epel/6/x86_64/epel-release-6-8.noarch.rpm

# Install required yum packages
RUN yum groupinstall -y "Development tools"
RUN yum install -y clang zlib-devel install bzip2-devel openssl-devel ncurses-devel cmake28 python-devel python-pip openssh-server sudo libyaml wget

# Use clang
ENV CC clang
ENV CXX clang++

# Download, build, and install Python 2.7
WORKDIR /usr/local/src
RUN wget --no-check-certificate https://www.python.org/ftp/python/2.7.6/Python-2.7.6.tar.xz
RUN tar xf Python-2.7.6.tar.xz
WORKDIR /usr/local/src/Python-2.7.6
RUN ./configure --prefix=/usr/local --enable-shared
RUN make && make altinstall

# Make newly compile Python the default
ENV LD_LIBRARY_PATH /usr/local/lib
ENV PYTHONPATH /usr/local/lib/python2.7/site-packages
RUN ln -s /usr/local/bin/python2.7 /usr/local/bin/python

# Download, build, and install setuptools
RUN wget https://bitbucket.org/pypa/setuptools/raw/bootstrap/ez_setup.py
RUN /usr/local/bin/python2.7 ez_setup.py
RUN /usr/local/bin/easy_install-2.7 pip

# Set NuPIC environment
ENV NUPIC /usr/local/src/nupic
ENV NTA $NUPIC/build/release
ENV PYTHONPATH $PYTHONPATH:$NTA/lib/python2.7/site-packages
ENV PY_VERSION 2.7
ENV NTA_DATA_PATH $NTA/share/prediction/data
ENV USER root
ENV PYTHON /usr/local/bin/python2.7

# Install Python dependencies
RUN git clone git://github.com/numenta/nupic.git /usr/local/src/nupic
WORKDIR /usr/local/src/nupic
RUN pip install --allow-all-external --allow-unverified PIL --allow-unverified  psutil -r external/common/requirements.txt

# Build and install NuPIC
RUN mkdir -p /usr/local/src/nupic/build/scripts
WORKDIR /usr/local/src/nupic/build/scripts
RUN cmake28 -DPYTHON_LIBRARY=/usr/local/lib/libpython2.7.so /usr/local/src/nupic
RUN make
