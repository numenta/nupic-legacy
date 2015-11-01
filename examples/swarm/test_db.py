#! /usr/bin/env python
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
import pymysql
from nupic.support.configuration import Configuration

# Get the values we need from NuPIC's configuration
host = Configuration.get('nupic.cluster.database.host')
port = int(Configuration.get('nupic.cluster.database.port'))
user = Configuration.get('nupic.cluster.database.user')
passwd = Configuration.get('nupic.cluster.database.passwd')

print 
print "This script will validate that your MySQL is setup correctly for NuPIC."
print "MySQL is required for NuPIC swarming. The settings are defined in a "
print "configuration file found in $NUPIC/src/nupic/support/nupic-default.xml "
print "Out of the box those settings contain MySQL's default access "
print "credentials."
print
print "The nupic-default.xml can be duplicated to define user specific changes, "
print "calling the copied file $NUPIC/src/nupic/support/nupic-site.xml"
print "Refer to the nupic-default.xml for additional instructions."
print
print "Defaults: localhost, 3306, root, no password"
print
print "Retrieved the following settings from NuPIC configuration:"
print "    host   :    ", host
print "    port   :    ", port
print "    user   :    ", user
print "    passwd :    ", passwd
print

try:
  conn = pymysql.connect(host=host, port=port, user=user, passwd=passwd)
except:
  raise RuntimeError("Couldn't connect to the database."
                     " Please ensure you have MySQL\n installed, running, and"
                     " accessible using the NuPIC configuration settings.")

print "Connection successful!!"

