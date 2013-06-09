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
import pybuild.test_release as test
import logging

if __name__ == '__main__':
  build = sys.argv[1]
  workspace = sys.argv[2]
  outfile = sys.argv[3]

  # Enable full logging right away, so that we see error messages
  log = logging.getLogger("auto") 
  initialhandler = logging.StreamHandler(sys.stdout)
  formatter = logging.Formatter("%(asctime)s %(name)-7s %(levelname)-7s %(message)s", "%y-%m-%d %H:%M:%S")
  initialhandler.setFormatter(formatter)
  initialhandler.setLevel(logging.NOTSET)

  rootlogger = logging.getLogger('')
  rootlogger.setLevel(logging.NOTSET)
  rootlogger.addHandler(initialhandler)

  # Turn down manifest file logging level
  logging.getLogger('autotest').setLevel(logging.INFO)
  # Setup very short log
  veryshortlog = 'veryshortlog.out'
  veryshortlogger = logging.FileHandler(veryshortlog, "w")
  formatter = logging.Formatter("%(asctime)s %(levelname)-7s %(message)s", "%H:%M:%S")
  veryshortlogger.setFormatter(formatter)
  veryshortlogger.addFilter(logging.Filter("auto"))
  veryshortlogger.setLevel(logging.NOTSET)
  rootlogger = logging.getLogger('')
  rootlogger.setLevel(logging.NOTSET)
  rootlogger.addHandler(veryshortlogger)

  longlog = outfile
  shortlog = 'shortlog.out'

  # long log contains all messages
  longlogger = logging.FileHandler(longlog, "w")
  formatter = logging.Formatter("%(asctime)s %(name)-7s %(levelname)-7s %(message)s", "%y-%m-%d %H:%M:%S")
  longlogger.setFormatter(formatter)
  longlogger.setLevel(logging.NOTSET)

  # short log contains only autobuild messages of INFO or higher
  shortlogger = logging.FileHandler(shortlog, "w")
  formatter = logging.Formatter("%(asctime)s %(levelname)-7s %(message)s", "%H:%M:%S")
  shortlogger.setFormatter(formatter)
  shortlogger.addFilter(logging.Filter("auto"))
  shortlogger.setLevel(logging.INFO)

  rootlogger = logging.getLogger('')
  rootlogger.setLevel(logging.NOTSET)
  veryshortlogger.setLevel(logging.CRITICAL)
  rootlogger.addHandler(shortlogger)
  rootlogger.addHandler(longlogger)


  (passed, failed, disabled) = test.runTests(build, workspace)
  test.logTestResults((passed, failed, disabled),
                        (False, True, True),
                        "Primary Tests", log)
  longlogger.flush()
  shortlogger.flush()
  if len(failed) > 0:
    print "The following tests failed: %s" %failed
