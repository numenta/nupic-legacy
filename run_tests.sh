#!/bin/sh
actual_dir = "$PWD"
cd $NUPIC
python bin/run_tests.py $@ || exit
cd "$actual_dir"
