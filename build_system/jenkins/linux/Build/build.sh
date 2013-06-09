TAG=$1
WORKSPACE=$2
python2 build_system/setup.py --autogen
cd ../$TAG/nta/build
$WORKSPACE/configure --enable-assertions=yes --prefix=$WORKSPACE/../$TAG/nta/eng
make
make install

