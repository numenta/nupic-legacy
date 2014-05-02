import sys
import os
import subprocess
from distutils.core import setup
from distutils.command.build_py import build_py

"""
This file only will call CMake process to generate scripts, build, and then install the NuPIC binaries.
ANY EXTRA code related to build process MUST be put into CMake file.
"""

def find_packages(repositoryDir):
  """ Traverse nupic directory and create packages for each subdir containing a
  __init__.py file
  """
  packages = []
  for root, dirs, files in os.walk(repositoryDir + '/nupic'):
      if '__init__.py' in files:
        subdir = root.replace(repositoryDir + '/', '')
        packages.append(subdir.replace('/', '.'))
  return packages


class build_nupic(build_py):
  """ NuPIC/CMake-specific build command handler
  """
  description = "build nupic.core and nupic c/c++ extensions"
  user_options = [
    ("make-options=",
      None,
     "Make options"),
    ("cmake-options=",
      None,
      "CMake options")]


  def initialize_options(self):
    self.make_options = ""
    self.cmake_options = ""


  def finalize_options(self):
    pass #ABC, must override


  def run(self):
    """ Read command line options looking for extra options for CMake and Make

    For example, an user could type:

        python setup.py install build_nupic --make-options='-j3'

    which will add '-j3' option to Make commandline.
    """

    # Prepare directories to the CMake process
    repositoryDir = os.getcwd()
    sourceDir = repositoryDir
    buildScriptsDir = repositoryDir + '/build/scripts'
    if not os.path.exists(buildScriptsDir):
      os.makedirs(buildScriptsDir)
    os.chdir(buildScriptsDir)

    # Generate build files with CMake
    return_code = subprocess.call("cmake " + sourceDir + ' ' + self.cmake_options, shell=True)
    if (return_code != 0):
      sys.exit("Unable to generate build scripts!")

    # Build files with Make
    return_code = subprocess.call("make " + self.make_options, shell=True)
    if (return_code != 0):
      sys.exit("Unable to build the project!")
    os.chdir(repositoryDir)


# Call the setup process
setup(
  name = 'nupic',
  version = '1.0.0',
  packages = find_packages(os.getcwd()),
  package_data = {
    'nupic': ['README.md', 'LICENSE.txt'],
    'nupic.bindings': ['_*.so', '_*.dll'],
    'nupic.data': ['*.json'],
    'nupic.frameworks.opf.exp_generator': ['*.json', '*.tpl'],
    'nupic.frameworks.opf.jsonschema': ['*.json'],
    'nupic.support.resources.images': ['*.png', '*.gif', '*.ico', '*.graffle'],
    'nupic.swarming.jsonschema': ['*.json']},
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
""",
  cmdclass={"build_py": build_nupic}
)
