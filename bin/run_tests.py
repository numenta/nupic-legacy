#!/usr/bin/env python
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
import os
import sys

from optparse import OptionParser

import pytest

def collect(option, opt_str, value, parser):
  """ Collect multiple option values into a single list.  Used in conjunction
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


parser = OptionParser(usage="%prog [options]\n\n" \
  "Run Grok Engine tests.")
parser.add_option("-a", "--all",
  action="store_true",
  default=False,
  dest="all")
parser.add_option("-c", "--coverage",
  action="store_true",
  default=False,
  dest="coverage")
parser.add_option("-i", "--integration",
  action="store_true",
  default=False,
  dest="integration")
parser.add_option("-n", "--num",
  dest="processes")
parser.add_option("-r", "--results",
  dest="results",
  nargs=2)
parser.add_option("-s",
  dest="tests",
  action="callback",
  callback=collect)
parser.add_option("-u", "--unit",
  action="store_true",
  default=False,
  dest="unit")
parser.add_option("-x", "--failfast",
  action="store_true",
  default=False,
  dest="failfast")


def main(parser, parse_args):
  """ Parse CLI options and execute tests """

  # Extensions to test spec (args not part of official test runner)

  parser.add_option("-v", "--verbose",
    action="store_true",
    dest="verbose")

  # Parse CLI args

  (options, tests) = parser.parse_args(args=parse_args)

  tests = set(tests)

  # Translate spec args to py.test args

  args = ["--boxed"]

  root = "tests"

  if options.coverage:
    args.append("--cov=nupic")

  if options.processes is not None:
    args.extend(["-n", options.processes])

  if options.results is not None:
    (format, runid) = options.results

    results = os.path.join(root, "results", "py2", "xunit", str(runid))

    try:
      os.makedirs(results)
    except os.error:
      pass

    args.append("--junitxml=" + os.path.join(results, "results.xml"))

  if options.tests is not None:
    tests.update(options.tests)

  if options.unit or options.all:
    tests.add(os.path.join(root, "unit", "py2"))

  if options.verbose:
    args.append("-v")

  if options.failfast:
    args.append("-x")

  if not tests or options.all:
    tests.add(os.path.join(root, "external", "py2"))
    tests.add(os.path.join(root, "unit", "py2"))


  # Run tests

  pytest.main(args + list(tests))


if __name__ == "__main__":
  main(parser, sys.argv[1:])
