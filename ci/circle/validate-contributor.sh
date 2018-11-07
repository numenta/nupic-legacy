#!/bin/bash
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2018, Numenta, Inc.  Unless you have purchased from
# Numenta, Inc. a separate commercial license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Affero Public License for more details.
#
# You should have received a copy of the GNU Affero Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------

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

