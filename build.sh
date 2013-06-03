#!/bin/sh -x
# build.sh build_dir install_dir

NUPIC="$(pwd)/$( dirname $0 )"

# Clean up the installation dir.
rm -rf $2
mkdir -p $2
rm -rf $1
mkdir -p $1

python "$NUPIC/build_system/setup.py" --autogen
pushd "$1"
"$NUPIC/configure" --enable-optimization --enable-assertions=yes --prefix=$2
make -j 3
make install

popd
