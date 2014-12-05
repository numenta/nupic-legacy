import setuptools
import sys
import os
import subprocess
import shutil
import urllib2
import tarfile
import re
import numpy
import py_compile
from distutils.command.build import build
from setuptools.command.install import install

"""
This file build and install the NuPIC binaries.
"""

class CustomBuild(build):
  def run(self):
    # Compile extensions before python modules to avoid that SWIG generated modules get out of the dist
    self.run_command('build_ext')
    build.run(self)

class CustomInstall(install):
  def run(self):
    # Compile extensions before python modules to avoid that SWIG generated modules get out of the dist
    self.run_command('build_ext')
    self.do_egg_install()

class Setup:

  def __init__(self):

    self.repositoryDir = os.getcwd()

    self.options = self.getCommandLineOptions()

    self.platform, self.bitness = self.getPlatformInfo()

    # Replace py_compile.compile with a function that skips certain files that are meant to fail
    self.origPyCompile = py_compile.compile
    py_compile.compile = self.skipPyCompile

    # Build and setup NuPIC
    os.chdir(self.repositoryDir)
    setuptools.setup(
      name="nupic",
      version=self.getVersion(),
      cmdclass={'build': CustomBuild, 'install': CustomInstall},
      packages=setuptools.find_packages(),
      package_data={
        "nupic": ["README.md", "LICENSE.txt"],
        "nupic.data": ["*.json"],
        "nupic.frameworks.opf.exp_generator": ["*.json", "*.tpl"],
        "nupic.frameworks.opf.jsonschema": ["*.json"],
        "nupic.support.resources.images": ["*.png", "*.gif", "*.ico", "*.graffle"],
        "nupic.swarming.jsonschema": ["*.json"]},
      data_files=[
        ("", ["config/default/nupic-default.xml"])],
      include_package_data=True,
      ext_modules=self.getExtensionModules(),
      description="Numenta Platform for Intelligent Computing",
      author="Numenta",
      author_email="help@numenta.org",
      url="https://github.com/numenta/nupic",
      classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: OS Independent",
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence"],
      long_description = """\
  NuPIC is a library that provides the building blocks for online prediction systems. The library contains the Cortical Learning Algorithm (CLA), but also the Online Prediction Framework (OPF) that allows clients to build prediction systems out of encoders, models, and metrics.

  For more information, see numenta.org or the NuPIC wiki (https://github.com/numenta/nupic/wiki).
  """)


  def getCommandLineOptions(self):

    # optionDesc = [name, value, description]
    optionsDesc = []
    optionsDesc.append(["nupic-core-dir", "dir", "(optional) Absolute path to nupic.core binary release directory"])
    optionsDesc.append(["skip-compare-versions", "", "(optional) Skip nupic.core version comparison"])
    optionsDesc.append(["user-make-command", "file", "(optional) Default `make` command used to build nupic.core"])

    # Read command line options looking for extra options
    # For example, an user could type:
    #   python setup.py install --user-make-command="usr/bin/make"
    # which will set the Make executable
    optionsValues = dict()
    for arg in sys.argv[:]:
      optionFound = False
      for option in optionsDesc:
        name = option[0]
        if "--" + name in arg:
          value = None
          hasValue = (option[1] != "")
          if hasValue:
            (_, _, value) = arg.partition("=")

          optionsValues[name] = value
          sys.argv.remove(arg)
          optionFound = True
          break
      if not optionFound:
        if ("--help-nupic" in arg):
          self.printOptions(optionsDesc)
          sys.exit()

    # Check if no option was passed, i.e. if "setup.py" is the only option
    # If True, "develop" is passed by default
    # This is useful when a developer wish build the project directly from an IDE
    if len(sys.argv) == 1:
      print "No command passed. Using 'develop' as default command. Use " \
            "'python setup.py --help' for more information."
      sys.argv.append("develop")

    return optionsValues


  def printOptions(self, optionsDesc):
    """
    Print command line options.
    """

    print "Options:\n"
    for option in optionsDesc:
      optionUsage = "--" + option[0]
      if option[1] != "":
        optionUsage += "=[" + option[1] + "]"
      optionDesc = option[2]
      print "    " + optionUsage.ljust(30) + " = " + optionDesc


  def getPlatformInfo(self):
    """
    Identify platform
    """

    if "linux" in sys.platform:
      platform = "linux"
    elif "darwin" in sys.platform:
      platform = "darwin"
    elif "win" in sys.platform:
      platform = "windows"

    if sys.maxsize > 2**32:
      bitness = "64"
    else:
      bitness = "32"

    return platform, bitness


  def skipPyCompile(self, file, cfile=None, dfile=None, doraise=False):
    filesToSkip = ["UnimportableNode.py"]
    if os.path.basename(file) not in filesToSkip:
      self.origPyCompile(file, cfile=cfile, dfile=dfile, doraise=doraise)


  def getVersion(self):
    """
    Get version from local file.
    """

    version = None
    with open("VERSION", "r") as versionFile:
      version = versionFile.read().strip()

    return version


  def getExtensionModules(self):

    nupicCoreReleaseDir = self.prepareNupicCore()

    #
    # Gives the version of Python necessary to get installation directories
    # for use with pythonVersion, etc.
    #
    if sys.version_info < (2, 7):
      print "FATAL_ERROR: Only these versions of Python are accepted: 2.7 or later"
      sys.exit()
    pythonVersion = str(sys.version_info[0]) + '.' + str(sys.version_info[1])

    #
    # Find out where system installation of python is.
    #
    pythonPrefix = sys.prefix
    pythonPrefix = pythonPrefix.replace("\\", "/")
    pythonIncludeDir = pythonPrefix + "/include/python" + pythonVersion

    #
    # Finds out version of Numpy and headers' path.
    #
    numpyIncludeDir = numpy.get_include()
    numpyIncludeDir = numpyIncludeDir.replace("\\", "/")

    stdLib = ""
    if self.platform == "darwin":
      stdLib = "-stdlib=libc++"

    commonDefines = [
      ("NUPIC2", ""),
      ("NTA_PLATFORM_" + self.platform + self.bitness, ""),
      ("NTA_PYTHON_SUPPORT", pythonVersion),
      ("NTA_INTERNAL", ""),
      ("NTA_ASSERTIONS_ON", ""),
      ("NTA_ASM", ""),
      ("HAVE_CONFIG_H", ""),
      ("BOOST_NO_WREGEX", "")]

    commonIncludeDirs = [
      self.repositoryDir + "/external/" + self.platform + self.bitness + "/include",
      self.repositoryDir + "/external/common/include",
      self.repositoryDir + "/extensions",
      self.repositoryDir,
      nupicCoreReleaseDir + "/include",
      pythonIncludeDir,
      numpyIncludeDir]

    commonCompileFlags = [
      "-std=c++11", # Adhere to c++11 spec
      "-m" + self.bitness, # Generate 32 or 64 bit code
      "-fPIC", # `position independent code`, required for shared libraries
      "-fvisibility=hidden",
      "-Wall",
      "-Wreturn-type",
      "-Wunused",
      "-Wno-unused-parameter"]
    if stdLib != "":
      commonCompileFlags.append(stdLib)

    commonLinkFlags = [
      "-std=c++11",
      "-m" + self.bitness,
      "-fPIC",
      "-L" + pythonPrefix + "/lib"]
    if stdLib != "":
      commonLinkFlags.append(stdLib)

    commonLibraries = []
    if self.platform == "linux":
      commonLibraries.extend(["pthread", "dl"])

    commonObjects = [
      nupicCoreReleaseDir + "/lib/" + self.getStaticLibFile("nupic_core")]

    pythonSupportSources = [
      "extensions/py_support/NumpyVector.cpp",
      "extensions/py_support/PyArray.cpp",
      "extensions/py_support/PyHelpers.cpp",
      "extensions/py_support/PythonStream.cpp"]

    extensions = []

    libDynamicCppRegion = setuptools.Extension(
      "nupic.cpp_region",
      extra_compile_args=commonCompileFlags + ["-shared"],
      define_macros=commonDefines,
      extra_link_args=commonLinkFlags,
      include_dirs=commonIncludeDirs,
      libraries =
        commonLibraries +
        ["dl",
        "python" + pythonVersion],
      sources=pythonSupportSources +
        ["extensions/cpp_region/PyRegion.cpp",
        "extensions/cpp_region/unittests/PyHelpersTest.cpp"],
      extra_objects=commonObjects)
    extensions.append(libDynamicCppRegion)

    #
    # SWIG
    #
    swigDir = self.repositoryDir + "/external/common/share/swig/3.0.2"
    swigExecutable = self.repositoryDir + "/external/" + self.platform + self.bitness + "/bin/swig"
    buildCommands = ["build", "build_ext", "install", "install_lib", "develop"]
    for arg in sys.argv:
      if arg in buildCommands:
        sys.argv.extend(["build_ext", "--swig", swigExecutable])
        break

    swigFlags = [
      "-c++",
      "-features",
      "autodoc=0,directors=0",
      "-noproxyimport",
      "-keyword",
      "-modern",
      "-modernargs",
      "-noproxydel",
      "-fvirtual",
      "-fastunpack",
      "-nofastproxy",
      "-fastquery",
      "-outputtuple",
      "-castmode",
      "-w402",
      "-w503",
      "-w511",
      "-w302",
      "-w362",
      "-w312",
      "-w389",
      "-DSWIG_PYTHON_LEGACY_BOOL",
      "-DNTA_PLATFORM_" + self.platform + self.bitness,
      "-I" + self.repositoryDir + "/extensions",
      "-I" + nupicCoreReleaseDir + "/include",
      "-I" + swigDir + "/python",
      "-I" + swigDir]

    swigLibraries = [
      "dl",
      "python" + pythonVersion]

    libSharedEngineInternal = setuptools.Extension(
      "nupic.bindings._engine_internal",
      swig_opts=swigFlags,
      extra_compile_args=commonCompileFlags,
      define_macros=commonDefines,
      extra_link_args=commonLinkFlags,
      include_dirs=commonIncludeDirs,
      libraries=swigLibraries,
      sources=pythonSupportSources +
        ["nupic/bindings/engine_internal.i"],
      extra_objects=commonObjects)
    extensions.append(libSharedEngineInternal)

    libSharedMath = setuptools.Extension(
      "nupic.bindings._math",
      swig_opts=swigFlags,
      extra_compile_args=commonCompileFlags,
      define_macros=commonDefines,
      extra_link_args=commonLinkFlags,
      include_dirs=commonIncludeDirs,
      libraries=swigLibraries,
      sources=pythonSupportSources +
        ["nupic/bindings/math.i",
        "nupic/bindings/PySparseTensor.cpp"],
      extra_objects=commonObjects)
    extensions.append(libSharedMath)

    libSharedAlgorithms = setuptools.Extension(
      "nupic.bindings._algorithms",
      swig_opts=swigFlags,
      extra_compile_args=commonCompileFlags,
      define_macros=commonDefines,
      extra_link_args=commonLinkFlags,
      include_dirs=commonIncludeDirs,
      libraries=swigLibraries,
      sources=pythonSupportSources +
        ["nupic/bindings/algorithms.i"],
      extra_objects=commonObjects)
    extensions.append(libSharedAlgorithms)

    return extensions


  def getStaticLibFile(self, libName):
    """
    Returns the default system name of a compiled static library.
    """

    if self.platform == "linux" or self.platform == "darwin":
      return "lib" + libName + ".a"
    elif self.platform == "windows":
      return libName + ".lib"


  def prepareNupicCore(self):

    if "nupic-core-dir" in self.options:
      nupicCoreReleaseDir = self.options["nupic-core-dir"]
    else:
      nupicCoreReleaseDir = ""

    if nupicCoreReleaseDir == "":
      # User did not specify 'nupic.core' binary location, assume relative to nupic
      nupicCoreReleaseDir = self.repositoryDir + "/extensions/core/build/release"
      nupicCoreSourceDir = self.repositoryDir + "/extensions/core"
      fetchNupicCore = True
    else:
      # User specified that they have their own nupic.core
      fetchNupicCore = False

    nupicCoreBucket = "https://s3-us-west-2.amazonaws.com/artifacts.numenta.org/numenta/nupic.core"

    if fetchNupicCore:
      # User has not specified 'nupic.core' location, so we'll download the binaries

      # First, get the nupic.core SHA and remote location from local config.
      nupicConfig = {}
      if os.path.exists(self.repositoryDir + "/.nupic_config"):
        execfile(os.path.join(self.repositoryDir, ".nupic_config"), {}, nupicConfig)
      elif os.path.exists(os.environ["HOME"] + "/.nupic_config"):
        execfile(os.path.join(os.environ["HOME"], ".nupic_config"), {}, nupicConfig)
      else:
        execfile(os.path.join(self.repositoryDir, ".nupic_modules"), {}, nupicConfig)
      nupicCoreRemote = nupicConfig["NUPIC_CORE_REMOTE"]
      nupicCoreCommitish = nupicConfig["NUPIC_CORE_COMMITISH"]

      nupicCoreRemoteUrl = nupicCoreBucket + "/nupic_core-" + nupicCoreCommitish + "-" + self.platform + self.bitness + ".tar.gz"
      nupicCoreLocalPackage = nupicCoreSourceDir + "/nupic_core-" + nupicCoreCommitish + "-" + self.platform + self.bitness + ".tar.gz"
      nupicCoreLocalDirToUnpack = "nupic_core-" + nupicCoreCommitish + "-" + self.platform + self.bitness

      if os.path.exists(nupicCoreLocalPackage):
        print "Target nupic.core package already exists at " + nupicCoreLocalPackage + "."
        self.unpackFile(nupicCoreLocalPackage, nupicCoreLocalDirToUnpack, nupicCoreReleaseDir)
      else:
        print "Attempting to fetch nupic.core binaries..."
        downloadSuccess = self.downloadFile(nupicCoreRemoteUrl, nupicCoreLocalPackage)

        # TODO: Give user a way to clean up all the downloaded binaries. It can be
        # manually done with `rm -rf $NUPIC_CORE/extensions/core` but would be
        # cleaner with something like `python setup.py clean`.

        if not downloadSuccess:
          print "Building nupic.core from local checkout " + nupicCoreSourceDir + "..."
          # Remove the local package file, which didn't get populated due to the
          # download failure.
          if os.path.exists(nupicCoreLocalPackage):
            os.remove(nupicCoreLocalPackage)

          # Get nupic.core dependency through git.
          if not os.path.exists(nupicCoreSourceDir + "/.git"):
            # There's not a git repo in nupicCoreSourceDir, so we can blow the whole
            # directory away and clone nupic.core there.
            shutil.rmtree(nupicCoreSourceDir, True)
            os.makedirs(nupicCoreSourceDir)
            process = subprocess.Popen("git clone " + nupicCoreRemote + " " + nupicCoreSourceDir,
              stdout=subprocess.PIPE,
              stderr=subprocess.PIPE,
              shell=True)
            _, exitCode = process.communicate()
            if exitCode != 0:
              print "FATAL_ERROR: Unable to clone " + nupicCoreRemote + " into " + nupicCoreSourceDir
              sys.exit()
          else:
            # Fetch if already cloned.
            process = subprocess.Popen("git fetch " + nupicCoreRemote,
              stdout=subprocess.PIPE,
              stderr=subprocess.PIPE,
              shell=True,
              cwd=nupicCoreSourceDir)
            _, exitCode = process.communicate()
            if exitCode != 0:
              print "FATAL_ERROR: Unable to fetch " + nupicCoreRemote
              sys.exit()

          # Get the exact SHA we need for nupic.core.
          process = subprocess.Popen("git reset --hard " + nupicCoreCommitish,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            cwd=nupicCoreSourceDir)
          _, exitCode = process.communicate()
          if exitCode != 0:
            print "FATAL_ERROR: Unable to checkout " + nupicCoreCommitish + " in " + nupicCoreSourceDir
            sys.exit()

          # Execute the Make scripts
          process = subprocess.Popen("git clean -fdx",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            cwd=nupicCoreSourceDir)
          _, exitCode = process.communicate()
          if exitCode != 0:
            print "FATAL_ERROR: Compiling 'nupic.core' library within " + self.repositoryDir + " failed."
            sys.exit()

          # Build and set external libraries
          print "Building 'nupic.core' library..."

          # Clean 'build/scripts' subfolder at submodule folder
          shutil.rmtree(nupicCoreSourceDir + "/build/scripts", True)
          os.makedirs(nupicCoreSourceDir + "/build/scripts")
          shutil.rmtree(nupicCoreReleaseDir, True)
          # Generate the Make scripts
          process = subprocess.Popen("cmake " + nupicCoreSourceDir + "/src -DCMAKE_INSTALL_PREFIX=" + nupicCoreReleaseDir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            cwd=nupicCoreSourceDir + "/build/scripts")
          _, exitCode = process.communicate()

          # Execute the Make scripts
          if "user-make-command" in self.options:
            userMakeCommand = self.options["user-make-command"]
          else:
            userMakeCommand = "make"
          process = subprocess.Popen(userMakeCommand + " install -j3",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            cwd=nupicCoreSourceDir + "/build/scripts")
          _, exitCode = process.communicate()
          if exitCode != 0:
            print "FATAL_ERROR: Compiling 'nupic.core' library within " + self.repositoryDir + " failed"
            sys.exit()

          print "Done."
        else:
          self.unpackFile(nupicCoreLocalPackage, nupicCoreLocalDirToUnpack, nupicCoreReleaseDir)
    else:
      print "Using nupic.core binaries at " + nupicCoreReleaseDir

    if "skip-compare-versions" in self.options:
      skipCompareVersions = True
    else:
      skipCompareVersions = not fetchNupicCore

    if not skipCompareVersions:
      # Compare expected version of nupic.core against installed version
      file = open(nupicCoreReleaseDir + "/include/nupic/Version.hpp", "r")
      content = file.read()
      file.close()
      nupicCoreVersionFound = re.search("#define NUPIC_CORE_VERSION \"([a-z0-9]+)\"", content).group(1)

      if nupicCoreCommitish != nupicCoreVersionFound:
        print "FATAL_ERROR: Unexpected version of nupic.core! Expected " + nupicCoreCommitish + \
              ", but detected " + nupicCoreVersionFound
        sys.exit()

    return nupicCoreReleaseDir


  def downloadFile(self, url, destFile, silent=False):
    """
    Download a file to the specified location
    """

    success = True

    if not silent:
      print "Downloading from '" + url + "' to '" + destFile + "'..."

    destDir = os.path.dirname(destFile)
    if not os.path.exists(destDir):
      os.makedirs(destDir)

    response = urllib2.urlopen(url)
    file = open(destFile, "wb")

    try:
      totalSize = response.info().getheader('Content-Length').strip()
      totalSize = int(totalSize)
      bytesSoFar = 0

      # Download chunks writing them to target file
      chunkSize = 8192
      oldPercent = 0
      while True:
        chunk = response.read(chunkSize)
        bytesSoFar += len(chunk)

        if not chunk:
          break

        file.write(chunk)

        # Show progress
        if not silent:
          percent = (float(bytesSoFar) / totalSize) * 100
          percent = int(percent)
          if percent != oldPercent and percent % 5 == 0:
            print "Downloaded " + str(bytesSoFar) + " of " + str(totalSize) + " bytes (" + str(percent) + "%)."
            oldPercent = percent

      file.close()
    except Exception, e:
      errMessage = str(e)
      success = False

    if not silent:
      if success:
        print "Download successful."
      else:
        print "WARNING: Error downloading: " + errMessage

    return success


  def unpackFile(self, package, dirToUnpack, destDir, silent=False):
    """
    Unpack package file to the specified directory
    """

    if not silent:
      print "Unpacking '" + package + "' into '" + destDir + "'..."

    file = tarfile.open(package, 'r:gz')
    file.extractall(destDir)
    file.close()

    # Copy subdirectories to a level up
    subDirs = os.listdir(destDir + "/" + dirToUnpack)
    for dir in subDirs:
      shutil.rmtree(destDir + "/" + dir, True)
      shutil.move(destDir + "/" + dirToUnpack + "/" + dir, destDir + "/" + dir)
    shutil.rmtree(destDir + "/" + dirToUnpack, True)


if __name__ == '__main__':
  setup = Setup()
