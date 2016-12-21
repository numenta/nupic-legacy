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

"""Memory profiling tool."""

import os
import subprocess
import sys
import time



def main(expLocation):
  start = time.time()
  opfRunnerPath = os.path.join(os.getcwd(), os.path.dirname(__file__),
                               'run_opf_experiment.py')
  expPath = os.path.join(os.getcwd(), expLocation)
  expProc = subprocess.Popen(['python', opfRunnerPath, expPath])
  history = []
  while True:
    if expProc.poll() is not None:
      break
    process = subprocess.Popen(
        "ps -o rss,command | grep run_opf_experiment | "
        "awk '{sum+=$1} END {print sum}'",
        shell=True, stdout=subprocess.PIPE)
    try:
      stdoutList = process.communicate()[0].split('\n')
      mem = float(stdoutList[0]) * 1024 / 1048576
    except ValueError:
      continue
    history.append((time.time() - start, mem))

  print 'Max memory: ', max([a[1] for a in history])



if __name__ == '__main__':
  if len(sys.argv) != 2:
    print ('Usage: profile_opf_memory.py path/to/experiment/\n'
           '    See run_opf_experiment.py')
    sys.exit(1)
  main(sys.argv[1])
