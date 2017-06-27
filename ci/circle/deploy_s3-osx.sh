#!/bin/bash
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013-2017, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
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

echo
echo Running deploy_s3-osx.sh...
echo

cp requirements.txt dist/
mkdir release
tar -zcv -f release/nupic-${CIRCLE_SHA1}-darwin64.tar.gz dist

# awscli needs to be manually installed on Circle's OS X
pip install awscli --user

aws s3 cp release/nupic-${CIRCLE_SHA1}-darwin64.tar.gz s3://artifacts.numenta.org/numenta/nupic/circle/
