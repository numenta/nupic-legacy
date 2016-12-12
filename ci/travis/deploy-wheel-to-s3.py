# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
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

import os
import sys
import boto
from boto.s3.key import Key

# This script assumes the following environment variables are set for boto:
# - AWS_ACCESS_KEY_ID
# - AWS_SECRET_ACCESS_KEY

REGION = "us-west-2"
BUCKET = "artifacts.numenta.org"
RELEASE_FOLDER = "numenta/nupic/releases"



def upload(artifactsBucket, wheelFileName, wheelPath):
  key = Key(artifactsBucket)
  key.key = "%s/%s" % (RELEASE_FOLDER, wheelFileName)
  print "Uploading %s to %s/%s..." % (wheelFileName, BUCKET, RELEASE_FOLDER)
  key.set_contents_from_filename(wheelPath)



def run(wheelPath):
  wheelFileName = os.path.basename(wheelPath)
  conn = boto.connect_s3()
  artifactsBucket = conn.get_bucket(BUCKET)
  upload(artifactsBucket, wheelFileName, wheelPath)



if __name__ == "__main__":
  wheelPath = sys.argv[1]
  run(wheelPath)
