#!/bin/sh
actDir=$PWD
cd $NUPIC
python ./scripts/run_tests.py $@ || exit
cd $actDir
