# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2015, Numenta, Inc.  Unless you have an agreement
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
import setuptools
import sys

from setuptools import setup, find_packages, Extension

REPO_DIR = os.path.dirname(os.path.realpath(__file__))



def getVersion():
  """
  Get version from local file.
  """
  with open(os.path.join(REPO_DIR, "VERSION"), "r") as versionFile:
    return versionFile.read().strip()



def parse_file(requirementFile):
  try:
    return [
      line.strip()
      for line in open(requirementFile).readlines()
      if not line.startswith("#")
    ]
  except IOError:
    return []



def findRequirements():
  """
  Read the requirements.txt file and parse into requirements for setup's
  install_requirements option.
  """
  requirementsPath = os.path.join(REPO_DIR, "external", "common",
                                  "requirements.txt")
  requirements = parse_file(requirementsPath)

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
    include_package_data=True,
    zip_safe=False,
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
