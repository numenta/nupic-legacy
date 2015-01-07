import shutil
import sys
import os
import subprocess
from setuptools import setup, Extension

"""
This file only will call CMake process to generate scripts, build, and then
install the NuPIC binaries. ANY EXTRA code related to build process MUST be
put into CMake file.
"""

repositoryDir = os.getcwd()


# Read command line options looking for extra options for CMake and Make
# For example, an user could type:
#   python setup.py install make_options="-j3"
# which will add "-j3" option to Make commandline
cmakeOptions = ""
makeOptions = "install"
setupOptions = ""
mustBuildExtensions = False
requirementsFile = "external/common/requirements.txt"

for arg in sys.argv[:]:
  if ("cmake_options" in arg) or ("make_options" in arg):
    (option, _, rhs) = arg.partition("=")
    if option == "--cmake_options":
      cmakeOptions = rhs
      sys.argv.remove(arg)
    if option == "--make_options":
      makeOptions = makeOptions + " " + rhs
      sys.argv.remove(arg)
  elif not "setup.py" in arg:
    if ("build" in arg) or ("install" in arg):
      mustBuildExtensions = True
    setupOptions += arg + " "


# Check if no option was passed, i.e. if "setup.py" is the only option
# If True, "develop" is passed by default
# This is useful when a developer wish build the project directly from an IDE
if len(sys.argv) == 1:
  print "No command passed. Using 'develop' as default command. Use " \
        "'python setup.py --help' for more information."
  sys.argv.append("develop")
  mustBuildExtensions = True


# Get version from local file.
version = None
with open("VERSION", "r") as versionFile:
  version = versionFile.read().strip()



def findPackages(repositoryDir):
  """
  Traverse nupic directory and create packages for each subdir containing a
  __init__.py file
  """
  packages = []
  for root, _, files in os.walk(repositoryDir + "/nupic"):
    if "__init__.py" in files:
      subdir = root.replace(repositoryDir + "/", "")
      packages.append(subdir.replace("/", "."))
  return packages



def findRequirements(repositoryDir):
  """
  Read the requirements.txt file and parse into requirements for setup's
  install_requirements option.
  """
  requirementsPath = os.path.join(repositoryDir, requirementsFile)
  return [
    line.strip()
    for line in open(requirementsPath).readlines()
    if not line.startswith("#")
  ]



def buildExtensionsNupic():
  """
  CMake-specific build operations
  """

  # Prepare directories to the CMake process
  sourceDir = repositoryDir
  buildScriptsDir = repositoryDir + "/build/scripts"
  if os.path.exists(buildScriptsDir):
    shutil.rmtree(buildScriptsDir)
  os.makedirs(buildScriptsDir)
  os.chdir(buildScriptsDir)

  # Generate build files with CMake
  returnCode = subprocess.call(
    "cmake %s %s" % (sourceDir, cmakeOptions), shell=True
  )
  if returnCode != 0:
    sys.exit("Unable to generate build scripts!")

  # Build library with Make
  returnCode = subprocess.call("make " + makeOptions, shell=True)
  if returnCode != 0:
    sys.exit("Unable to build the library!")



def setupNupic():
  """
  Package setup operations
  """

  packages = findPackages(repositoryDir)
  requires = findRequirements(repositoryDir)

  # This is a fake extension meant to fake out wheel to produce
  # platform-specific .whl files. Without this, wheel assumed the binary file
  # will be platform-independent, and we don't want that.
  fakeExtension = Extension(
      "fake-extension",
      swig_opts=[],
      extra_compile_args=[],
      define_macros=[],
      extra_link_args=[],
      include_dirs=[],
      libraries=[],
      sources=[],
      extra_objects=[]
  )

  # Setup library
  os.chdir(repositoryDir)
  setup(
    name = "nupic",
    ext_modules=[fakeExtension],
    version = version,
    packages = packages,
    install_requires = requires,
    # A lot of this stuff may not be packaged properly, most of it was added in
    # an effort to get a binary package prepared for nupic.regression testing
    # on Travis-CI, but it wasn't done the right way. I'll be refactoring a lot
    # of this for https://github.com/numenta/nupic/issues/408, so this will be
    # changing soon. -- Matt
    package_data = {
      "nupic.support": ["nupic-default.xml",
                        "nupic-logging.conf"],
      "nupic": ["README.md", "LICENSE.txt",
                "CMakeLists.txt", "*.so", "*.dll", "*.dylib"],
      "nupic.bindings": ["_*.so", "_*.dll", "*.i"],
      "nupic.data": ["*.json"],
      "nupic.frameworks.opf.exp_generator": ["*.json", "*.tpl"],
      "nupic.frameworks.opf.jsonschema": ["*.json"],
      "nupic.support.resources.images": ["*.png", "*.gif",
                                         "*.ico", "*.graffle"],
      "nupic.swarming.jsonschema": ["*.json"]
    },
    data_files=[
      ("", [
        "CMakeLists.txt",
        ]
      )
    ],
    include_package_data = True,
    description = "Numenta Platform for Intelligent Computing",
    author="Numenta",
    author_email="help@numenta.org",
    url="https://github.com/numenta/nupic",
    classifiers=[
      "Programming Language :: Python",
      "Programming Language :: Python :: 2",
      "License :: OSI Approved :: GNU General Public License (GPL)",
      "Operating System :: MacOS :: MacOS X",
      "Operating System :: POSIX :: Linux",
      # It has to be "5 - Production/Stable" or else pypi rejects it!
      "Development Status :: 5 - Production/Stable",
      "Environment :: Console",
      "Intended Audience :: Science/Research",
      "Topic :: Scientific/Engineering :: Artificial Intelligence"
    ],
    long_description = """\
Numenta Platform for Intelligent Computing: a machine intelligence platform that implements the HTM learning algorithms. HTM is a detailed computational theory of the neocortex. At the core of HTM are time-based continuous learning algorithms that store and recall spatial and temporal patterns. NuPIC is suited to a variety of problems, particularly anomaly detection and prediction of streaming data sources.

For more information, see http://numenta.org or the NuPIC wiki at https://github.com/numenta/nupic/wiki.
"""
  )



# Build and setup NuPIC
if mustBuildExtensions:
  buildExtensionsNupic()
setupNupic()
