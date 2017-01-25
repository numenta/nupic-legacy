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

"""Installation script for Python nupic package."""

import os
import pkg_resources
import sys

from setuptools import setup, find_packages, Extension
from setuptools.command.test import test as BaseTestCommand



REPO_DIR = os.path.dirname(os.path.realpath(__file__))



def getVersion():
  """
  Get version from local file.
  """
  with open(os.path.join(REPO_DIR, "VERSION"), "r") as versionFile:
    return versionFile.read().strip()



def nupicBindingsPrereleaseInstalled():
  """
  Make an attempt to determine if a pre-release version of nupic.bindings is
  installed already.

  @return: boolean
  """
  try:
    nupicDistribution = pkg_resources.get_distribution("nupic.bindings")
    if pkg_resources.parse_version(nupicDistribution.version).is_prerelease:
      # A pre-release dev version of nupic.bindings is installed.
      return True
  except pkg_resources.DistributionNotFound:
    pass  # Silently ignore.  The absence of nupic.bindings will be handled by
    # setuptools by default

  # Also check for nupic.research.bindings
  try:
    nupicDistribution = pkg_resources.get_distribution("nupic.research.bindings")
    return True
  except pkg_resources.DistributionNotFound:
    pass  # Silently ignore.  The absence of nupic.bindings will be handled by
    # setuptools by default

  return False



def parse_file(requirementFile):
  try:
    return [
      line.strip()
      for line in open(requirementFile).readlines()
      if not line.startswith("#")
    ]
  except IOError:
    return []



class TestCommand(BaseTestCommand):
  user_options = [("pytest-args=", "a", "Arguments to pass to py.test")]


  def initialize_options(self):
    BaseTestCommand.initialize_options(self)
    self.pytest_args = ["unit"] # pylint: disable=W0201


  def finalize_options(self):
    BaseTestCommand.finalize_options(self)
    self.test_args = []
    self.test_suite = True


  def run_tests(self):
    import pytest
    cwd = os.getcwd()
    try:
      os.chdir("tests")
      errno = pytest.main(self.pytest_args)
    finally:
      os.chdir(cwd)
    sys.exit(errno)



def findRequirements():
  """
  Read the requirements.txt file and parse into requirements for setup's
  install_requirements option.
  """
  requirementsPath = os.path.join(REPO_DIR, "requirements.txt")
  requirements = parse_file(requirementsPath)

  if nupicBindingsPrereleaseInstalled():
    # User has a pre-release version of nupic.bindings installed, which is only
    # possible if the user installed and built nupic.bindings from source and
    # it is up to the user to decide when to update nupic.bindings.  We'll
    # quietly remove the entry in requirements.txt so as to not conflate the
    # two.
    requirements = [req for req in requirements if "nupic.bindings" not in req]

  return requirements



if __name__ == "__main__":
  requirements = findRequirements()

  setup(
    name="nupic",
    version=getVersion(),
    install_requires=requirements,
    package_dir = {"": "src"},
    packages=find_packages("src"),
    namespace_packages = ["nupic"],
    package_data={
      "nupic.support": ["nupic-default.xml",
                        "nupic-logging.conf"],
      "nupic": ["README.md", "LICENSE.txt"],
      "nupic.data": ["*.json"],
      "nupic.frameworks.opf.exp_generator": ["*.json", "*.tpl"],
      "nupic.frameworks.opf.jsonschema": ["*.json"],
      "nupic.swarming.exp_generator": ["*.json", "*.tpl"],
      "nupic.swarming.jsonschema": ["*.json"],
      "nupic.datafiles": ["*.csv", "*.txt"],
    },
    cmdclass = {"test": TestCommand},
    include_package_data=True,
    zip_safe=False,
    extras_require = {
      # Default requirement based on system type
      ":platform_system=='Linux' or platform_system=='Darwin'":
        ["pycapnp==0.5.8"],

      # Superseded by platform_system-conditional requirement, but keeping
      # empty extra for compatibility as recommended by setuptools doc.
      "capnp": [],
      "viz": ["networkx", "matplotlib", "pygraphviz"]
    },
    description="Numenta Platform for Intelligent Computing",
    author="Numenta",
    author_email="help@numenta.org",
    url="https://github.com/numenta/nupic",
    classifiers=[
      "Programming Language :: Python",
      "Programming Language :: Python :: 2",
      "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
      "Operating System :: MacOS :: MacOS X",
      "Operating System :: POSIX :: Linux",
      "Operating System :: Microsoft :: Windows",
      # It has to be "5 - Production/Stable" or else pypi rejects it!
      "Development Status :: 5 - Production/Stable",
      "Environment :: Console",
      "Intended Audience :: Science/Research",
      "Topic :: Scientific/Engineering :: Artificial Intelligence"
    ],
    long_description=(
        "Numenta Platform for Intelligent Computing: a machine intelligence "
        "platform that implements the HTM learning algorithms. HTM is a "
        "detailed computational theory of the neocortex. At the core of HTM "
        "are time-based continuous learning algorithms that store and recall "
        "spatial and temporal patterns. NuPIC is suited to a variety of "
        "problems, particularly anomaly detection and prediction of streaming "
        "data sources.\n\n"
        "For more information, see http://numenta.org or the NuPIC wiki at "
        "https://github.com/numenta/nupic/wiki.")
  )
