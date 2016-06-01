#!/bin/bash

exit_code=0;

echo "============= PYLINT ============="

for checkable in $(git diff --name-only ${TRAVIS_BRANCH} | grep py$)
do
    echo "===================>"
    echo "= running pylint on $checkable"
    echo "===================>"
    pylint --rcfile=${NUPIC}/pylintrc $checkable
    echo $((exit_code+=$?)) > /dev/null
done

if [ "$exit_code" -eq 0 ]; then
    echo "========== PYLINT PASSED ========="
else
    echo "========== PYLINT FAILED ========="
    exit $exit_code
fi
