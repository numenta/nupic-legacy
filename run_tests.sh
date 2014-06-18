#!/bin/sh
pushd $NUPIC > /dev/null
python ./scripts/run_tests.py $@ || exit
popd > /dev/null
