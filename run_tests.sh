#!/bin/sh
pushd $NUPIC
python bin/run_tests.py $@ || exit
popd
