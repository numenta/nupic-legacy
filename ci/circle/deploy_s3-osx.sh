#!/bin/bash
# Copyright 2013-2017 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

echo
echo Running deploy_s3-osx.sh...
echo

cp requirements.txt dist/
mkdir release
tar -zcv -f release/nupic-${CIRCLE_SHA1}-darwin64.tar.gz dist

# awscli needs to be manually installed on Circle's OS X
pip install awscli --user

aws s3 cp release/nupic-${CIRCLE_SHA1}-darwin64.tar.gz s3://artifacts.numenta.org/numenta/nupic/circle/
