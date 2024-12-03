# Copyright 2013 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

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
