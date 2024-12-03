#!/bin/bash
# Copyright 2018 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

set -o errexit

# Download latest contributors list
curl http://staging.numenta.org/resources/contributors.csv -o contributors.csv

# Checks if the given user is a valid contributor
# parameters:
# 1. Name
# 2. Email
function isValidContributor() {

    # Validate name
    if [ "$(cut -d, -f1 ./contributors.csv | grep "$1")" ]; then
        return 0
    fi

    # Validate email
    if [ "$(cut -d, -f3 ./contributors.csv | grep "$2")" ]; then
        return 0
    fi

    return 1
}

# Get last commiter's name and email
SHA=$(git rev-list --no-merges -1 HEAD)
NAME=$(git log -n 1 --pretty=format:%an ${SHA})
EMAIL=$(git log -n 1 --pretty=format:%ae ${SHA})

# Validate contributor
if isValidContributor "${NAME}" "${EMAIL}"; then
    echo  "${NAME} signed the Contributor License"
    exit 0
fi

# Not Found
echo "${NAME} <${EMAIL}> must sign the Contributor License (http://numenta.org/licenses/cl/)" 
exit 1

