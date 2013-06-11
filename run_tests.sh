#!/bin/bash

ROOTDIR=`dirname $0`
TESTS="tests/external/py tests/unit/py"
COVERAGE=""
while true; do
 case $1 in
 -c) COVERAGE="--with-coverage --cover-package=nupic" ;;
 -u) TESTS="tests/unit/" ;;
 -r) case "$2" in
     xunit)
       case "$3" in
         -*) RUNID=`date +"%Y%m%d%H%M%S"` ;;
         "") RUNID=`date +"%Y%m%d%H%M%S"` ;;
         *) RUNID=$3 ; shift ; 
       esac
       RESULTS="tests/results/py/xunit/${RUNID}"
       mkdir -p $RESULTS
       XUNIT="--with-xunit --xunit-file=$RESULTS/nosetests.xml" ;;
     stdout) XUNIT="" ;;
     --) break ;;
     esac
     shift ;;
  # Individual tests/modules
  -e) ENGINE_TESTS="true" ;
    TESTS=`cat tests/engine_aws_cluster_tests.testlist` ;
    case "$2" in
      -*) ;;
      "") ;;
      *.testlist) TESTS=`cat $2`; shift ;;
      *) TESTS=$2 ; shift ;;
    esac ;;
 -*) break ;;
 *) break ;;
 --) break ;;
 esac
 shift
done
shift

run_engine_tests() {
  for TEST in $TESTS; do
    if [[ -n $XUNIT ]]; then
      XUNIT_NAME=`echo $TEST | sed "s/\//_/g"`
      XUNIT="--with-xunit --xunit-file=$RESULTS/$XUNIT_NAME.xml"
    fi
    echo "Running" `basename $TEST` 1>&2
    nosetests -v --nologcapture $XUNIT $TEST $@
  done
}

if [[ -n $ENGINE_TESTS ]]; then
  run_engine_tests $@
else
  nosetests -v --exe $COVERAGE $XUNIT $TESTS $@
fi


