#!/bin/bash

exit_code=0;

pushd $NUPIC

for checkable in $(git diff --name-only ${TRAVIS_BRANCH} | grep py$)
do
    echo "running pylint on $checkable"
    echo "pylint --rcfile=${NUPIC}/pylintrc $checkable"
    pylint --rcfile=${NUPIC}/pylintrc $checkable
    echo $((exit_code+=$?)) > /dev/null
done

popd
echo $exit_code
exit $exit_code
