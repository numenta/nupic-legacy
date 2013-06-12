#!/usr/bin/env python2
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

import sys
import os
import time
import socket
import json

if __name__ == '__main__':

  arch = sys.argv[1]
  tag = sys.argv[2]
  dir = sys.argv[3]
  curtime = time.ctime()
  hostname = socket.gethostname()
  assertions = True
  

  buildinfo = os.path.join(dir, "..", tag, 'nta', 'eng', '.buildinfo')
  buildnumber = os.path.join(dir, "..", tag, 'nta', 'eng', '.build.number')
  jsonbuildnumber = os.path.join(dir, "..", tag, 'nta', 'eng', '.build.json')
  os.system('touch %s' %buildinfo)
  file = open(buildinfo, 'w')
  print >> file, "==============================="
  print >> file, "Timestamp: %s" %curtime
  print >> file, "Arch: %s" %arch
  print >> file, "Buildhost: %s" %hostname
  print >> file, "Tag: %s" %tag
  print >> file, "Assertions: %s" %assertions
  print >> file, "==============================="
  file.close()

  file = open(buildnumber, 'w')
  print >> file, tag[0:7],
  print >> file, " ",
  print >> file, curtime[0:11]
  file.close()

  to_dump = {}
  to_dump["tag"] = tag
  file = open(jsonbuildnumber, 'w')
  json.dump(to_dump,file)
  file.close()

