# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2016, Numenta, Inc.  Unless you have an agreement
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
import re



NUPIC = os.environ["NUPIC"]
REGEXP = re.compile("nupic.bindings([<>=][=]?.+)")



def extractNupicBindingsVersion(requirementsFile):
  with open(requirementsFile, "r") as f:
    for line in f:
      matchResult = REGEXP.match(line)
      if matchResult:
        return matchResult.group(1)



if __name__ == "__main__":
  requirementsFile = os.path.join(NUPIC, "requirements.txt")
  nupicBindingsVersion = extractNupicBindingsVersion(requirementsFile)
  print nupicBindingsVersion
