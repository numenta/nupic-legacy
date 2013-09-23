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
import platform

def getArch() :
  """
  Return the NuPIC architecture name.
  Note that this is redundant with the calculation in configure.ac (<-- TODO so remove?) 
  """
  if sys.platform == "linux2":
    #
    # platform.processor() vs. platform.machine() is a bit of a mystery
    # On linux systems, they ultimately translate to uname -p and uname -m, respectively.
    # These options and their possible results aren't clearly documented. 
    # uname -p doesn't exist in some versions of uname (debian 3.x)
    # and returns "unknown" on others (Ubuntu). Python translates "unknown" to "". 
    # uname -p may also return "athlon" or other random words. 
    # 
    cpu = platform.machine()
    if cpu not in ["i686", "i386", "x86_64"]:
      cpu = platform.processor()
    if cpu in ["i686", "i386"]:
      return "linux32"
    elif cpu == "x86_64":
      return "linux64"
    else:
      raise Exception("Unknown cpu for linux system. platform.machine() = %s; platform.processor() = %s" % (platform.machine(), platform.processor()))
  elif sys.platform == "darwin":
    cpu = platform.processor()
    if cpu == "powerpc":
      raise Exception("Unsupported CPU %s for darwin system" %(cpu));
    else:
      return "darwin64"

  elif sys.platform == "win32":
    return "win32"
  else:
    raise Exception("Unknown os %s" % sys.platform)

