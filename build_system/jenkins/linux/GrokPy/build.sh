TAG=$1
WORKSPACE=$2
cd $WORKSPACE
python2 setup.py build
echo $TAG > $WORKSPACE/build/lib/grokpy/.buildinfo
