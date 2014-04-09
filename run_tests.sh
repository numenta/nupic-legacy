#!/bin/sh
pushd $NUPIC > /dev/null
python ./bin/run_tests.py $@ || exit
popd > /dev/null
