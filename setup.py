import sys
import os
import subprocess
from distutils.core import setup

"""
This file only will call CMake process to generate scripts, build, and then install the NuPIC binaries.
ANY EXTRA code related to build process MUST be put into CMake file.
"""

# Read command line options looking for extra options for CMake and Make
# For example, an user could type:
#   python setup.py install make_options='-j3'
# which will add '-j3' option to Make commandline
cmakeOptions = ""
makeOptions = ""
for arg in sys.argv:
  if ("cmake_options" in arg) or ("make_options" in arg):
    option = arg.split("=")
    if option[0] == "cmake_options":
        cmakeOptions = option[1]
    if option[0] == "make_options":
        makeOptions = option[1]
    sys.argv.remove(arg)

# Prepare directories to the CMake process
repositoryDir = os.getcwd()
sourceDir = repositoryDir
buildScriptsDir = repositoryDir + '/build/scripts'
if not os.path.exists(buildScriptsDir):
  os.makedirs(buildScriptsDir)
os.chdir(buildScriptsDir)

# Generate build files with CMake
return_code = subprocess.call("cmake " + sourceDir + ' ' + cmakeOptions, shell=True)
if (return_code != 0):
  sys.exit("Unable to generate build scripts!")

# Build files with Make
return_code = subprocess.call("make " + makeOptions, shell=True)
if (return_code != 0):
  sys.exit("Unable to build the project!")

# Traverse nupic directory and create packages for each subdir containing a __init__.py file
packages = []
for root, dirs, files in os.walk(repositoryDir + '/nupic'):
    if '__init__.py' in files:
      subdir = root.replace(repositoryDir + '/', '')
      packages.append(subdir.replace('/','.'))

# Call the setup process
os.chdir(repositoryDir)
setup(
  name = 'nupic',
  version = '1.0.0',
  packages = packages,
  package_data = {'nupic': ['README.md', 'LICENSE.txt'], 'nupic.bindings': ['_*.so', '_*.dll']},
  description = 'Numenta Platform for Intelligent Computing',
  author='Numenta',
  author_email='help@numenta.org',
  url='https://github.com/numenta/nupic',
  classifiers=[
    'Programming Language :: Python',
    'Programming Language :: Python :: 2',
    'License :: OSI Approved :: GNU General Public License (GPL)',
    'Operating System :: OS Independent',
    'Development Status :: 5 - Production/Stable',
    'Environment :: Console',
    'Intended Audience :: Science/Research',
    'Topic :: Scientific/Engineering :: Artificial Intelligence'
  ],
  long_description = """\
NuPIC is a library that provides the building blocks for online prediction systems. The library contains the Cortical Learning Algorithm (CLA), but also the Online Prediction Framework (OPF) that allows clients to build prediction systems out of encoders, models, and metrics.

For more information, see numenta.org or the NuPIC wiki (https://github.com/numenta/nupic/wiki).
"""
)
