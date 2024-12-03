# Copyright 2013 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

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
