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
from subprocess import call
from optparse import OptionParser
from datetime import datetime

from pkg_resources import (
  DistributionNotFound,
  get_distribution
)



try:
  pytestXdistAvailable = bool(get_distribution("pytest-xdist"))
except DistributionNotFound:
  print "ERROR: `pytest-xdist` is not installed.  Certain testing features" \
    " are not available without it.  The complete list of python" \
    " requirements can be found in requirements.txt."
  sys.exit(1)


def collect_set(option, opt_str, value, parser):
  """ Collect multiple option values into a single set.  Used in conjunction
  with callback argument to OptionParser.add_option().
  """

  assert value is None
  value = set([])

  for arg in parser.rargs:
    if arg[:1] == "-":
      break
    value.add(arg)

  del parser.rargs[:len(value)]
  setattr(parser.values, option.dest, value)


def collect_list(option, opt_str, value, parser):
  """ Collect multiple option values into a single list.  Used in conjunction
  with callback argument to OptionParser.add_option().
  """

  assert value is None
  value = []

  for arg in parser.rargs:
    if arg[:1] == "-":
      break
    value.append(arg)

  del parser.rargs[:len(value)]
  setattr(parser.values, option.dest, value)


parser = OptionParser(usage="%prog [options]\n\nRun NuPIC Python tests.")
parser.add_option(
  "-a",
  "--all",
  action="store_true",
  default=False,
  dest="all")
parser.add_option(
  "-c",
  "--coverage",
  action="store_true",
  default=False,
  dest="coverage")
parser.add_option(
  "-m",
  "--filtermarks",
  dest="markexpresson",
  help="Expression for filtering tests by tags that were used to mark the "
       "test classes and/or methods; presently, 'tag' or 'not tag' are "
       "supported; e.g., 'not clusterExclusive'")
parser.add_option(
  "-i",
  "--integration",
  action="store_true",
  default=False,
  dest="integration")
parser.add_option(
  "-w",
  "--swarming",
  action="store_true",
  default=False,
  dest="swarming")
parser.add_option(
    "-n",
    "--num",
    dest="processes")
parser.add_option(
  "-r",
  "--results",
  dest="results",
  action="callback",
  callback=collect_list)
parser.add_option(
  "-s",
  dest="tests",
  action="callback",
  callback=collect_set)
parser.add_option(
  "-u",
  "--unit",
  action="store_true",
  default=False,
  dest="unit")
parser.add_option(
  "-x",
  "--failfast",
  action="store_true",
  default=False,
  dest="failfast")


def main(parser, parse_args):
  """ Parse CLI options and execute tests """

  # Default to success, failures will flip it.
  exitStatus = 0

  # Extensions to test spec (args not part of official test runner)

  parser.add_option(
    "-t",
    "--testlist",
    action="callback",
    callback=collect_set,
    dest="testlist_file",
    help="Test list file, specifying tests (one per line)")
  parser.add_option(
    "-v",
    "--verbose",
    action="store_true",
    dest="verbose")

  # Parse CLI args

  (options, tests) = parser.parse_args(args=parse_args)

  tests = set(tests)

  # Translate spec args to py.test args

  args = [
    "--boxed", # See https://pypi.python.org/pypi/pytest-xdist#boxed
    "--verbose"
  ]

  root = "tests"

  if options.coverage:
    args.append("--cov=nupic")

  if options.processes is not None:
    # See https://pypi.python.org/pypi/pytest-xdist#parallelization
    args.extend(["-n", options.processes])

  if options.markexpresson is not None:
    args.extend(["-m", options.markexpresson])

  if options.results is not None:
    results = options.results[:2]

    format = results.pop(0)

    if results:
      runid = results.pop(0)
    else:
      runid = datetime.now().strftime('%Y%m%d%H%M%S')

    results = os.path.join(root, "results", "xunit", str(runid))

    try:
      os.makedirs(results)
    except os.error:
      pass

    args.append("--junitxml=" + os.path.join(results, "results.xml"))

  if options.tests is not None:
    tests.update(options.tests)

  if options.unit or options.all:
    tests.add(os.path.join(root, "unit"))

  if options.integration or options.all:
    tests.add(os.path.join(root, "integration"))

  if options.swarming or options.all:
    tests.add(os.path.join(root, "swarming"))

  if options.verbose:
    args.append("-v")

  if options.failfast:
    args.append("-x")

  if not tests or options.all:
    tests.add(os.path.join(root, "external"))
    tests.add(os.path.join(root, "unit"))

  # Run tests

  if options.testlist_file is not None:
    # Arbitrary test lists

    if options.testlist_file:
      testlist = options.testlist_file.pop()
      if testlist.endswith(".testlist"):
        testlist = [test.strip() for test in open(testlist).readlines()]

      else:
        testlist = options.testlist_file
        testlist.add(testlist)

    for test in testlist:
      specific_args = \
        [
          arg.replace("results.xml", test.replace("/", "_") + ".xml")
            if arg.startswith("--junitxml=")
            else arg
          for arg in args
        ]
      testStatus = call(["py.test"] + specific_args + [test])
      # exitStatus defaults to 0, if any test returns non-0, we'll set it.
      if testStatus is not 0:
        exitStatus = testStatus

  else:
    # Standard tests
    exitStatus = call(["py.test"] + args + list(tests))

  return exitStatus


if __name__ == "__main__":
  # Tests need to run from $NUPIC, so let's change there and at the end back to actual_dir
  actual_dir=os.getcwd()
  os.chdir(os.getenv('NUPIC'))

  result = main(parser, sys.argv[1:])

  os.chdir(actual_dir)
  sys.exit(result)
