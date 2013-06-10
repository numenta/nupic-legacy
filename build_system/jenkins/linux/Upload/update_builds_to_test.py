# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have purchased from
# Numenta, Inc. a separate commercial license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------

""" Script to upload build to S3
 
Usage:
  python2 upload_build.py [--bucketname=bucketname] --filename=filename
"""


from optparse import OptionParser
import getpass
import boto
import sys
import time
import os
from boto.s3.key import Key


def downloadFile(conn, filename, bucketname, localpath):
  print "Getting all buckets ..."
  buckets = conn.get_all_buckets()
  bucket = boto.s3.bucket.Bucket()
  for b in buckets:
    if b.name == bucketname:
      print "Found the bucket ..."
      bucket = b
  k = Key(bucket)
  k.key = filename
  print "Checking if file exists locally ..."
  if filename == "":
    print "No filename specified. Quitting ..."
    return 1
  print "Downloading file ..."
  k.get_contents_to_filename(os.path.join(localpath, filename))
  print "Download file done."



def uploadFile(conn, filename, bucketname):
  print "Getting all buckets ..."
  buckets = conn.get_all_buckets()
  bucket = boto.s3.bucket.Bucket()
  for b in buckets:
    if b.name == bucketname:
      print "Found the bucket ..."
      bucket = b
  k = Key(bucket)
  k.key = filename
  print "Filename %s" %filename
  print "Key %s" %k.key
  print "Uploading file ..."
  tmpfilename = 'tmpfilename'
  os.system("sed '/^$/d' %s > %s" %(filename, tmpfilename))
  os.system("mv %s %s" %(tmpfilename, filename))
  k.set_contents_from_filename(filename)
  print "Upload file done."
   

def updateFile(tag, filename):
  print "Updating builds_to_test file ..."
  try:
    f = open(filename, 'a')
    print >> f,tag
    f.close()
  except:
    print "Updating builds_to_test file failed."
  

#############################################################################
if __name__ == "__main__":

  username = getpass.getuser()
  defaultBucketName = "numenta.builds"
  defaultFileName = "builds_to_test"

  parser = OptionParser()
  parser.add_option("--bucketname", help="Name of bucket (default: %default)",
                    dest="bucketname", default=defaultBucketName)
  parser.add_option("--tag", help="Name of builld",
		    dest="tag", default=None)
  parser.add_option("--filename", help="Name of file",
                    dest="filename", default=defaultFileName)

  options, args = parser.parse_args(sys.argv[1:])

  if len(args) > 0:
    print "Unknown arguments: %s" % (str(args))
    sys.exit(1)

  conn = boto.connect_s3()
  downloadFile(conn, options.filename, options.bucketname, '.')
  updateFile(options.tag, options.filename)
  uploadFile(conn, options.filename, options.bucketname)

