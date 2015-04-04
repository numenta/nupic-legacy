import sys
import os
import subprocess
import shutil
import glob
import urllib2
import tarfile
import re
import numpy
from setuptools import setup, find_packages, Extension

"""
This file builds and installs the NuPIC binaries.
"""

NUPIC_CORE_BUCKET = (
  "https://s3-us-west-2.amazonaws.com/artifacts.numenta.org/numenta/nupic.core"
)
REPO_DIR = os.path.dirname(os.path.realpath(__file__))
DARWIN_PLATFORM = "darwin"
LINUX_PLATFORM = "linux"
UNIX_PLATFORMS = [LINUX_PLATFORM, DARWIN_PLATFORM]
WINDOWS_PLATFORMS = ["windows"]



def downloadFile(url, destFile, silent=False):
  """
  Download a file to the specified location
  """

  if not silent:
    print "Downloading from\n\t%s\nto\t%s.\n" % (url, destFile)

  destDir = os.path.dirname(destFile)
  if not os.path.exists(destDir):
    os.makedirs(destDir)

  try:
    response = urllib2.urlopen(url)
  except urllib2.URLError:
    return False

  with open(destFile, "wb") as fileObj:
    totalSize = response.info().getheader("Content-Length").strip()
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

      fileObj.write(chunk)

      # Show progress
      if not silent:
        percent = (float(bytesSoFar) / totalSize) * 100
        percent = int(percent)
        if percent != oldPercent and percent % 5 == 0:
          print ("Downloaded %i of %i bytes (%i%%)."
                 % (bytesSoFar, totalSize, int(percent)))
          oldPercent = percent

  return True



def unpackFile(package, dirToUnpack, destDir, silent=False):
  """
  Unpack package file to the specified directory
  """

  if not silent:
    print "Unpacking %s into %s..." % (package, destDir)

  with tarfile.open(package, "r:gz") as tarFileObj:
    tarFileObj.extractall(destDir)

  # Copy subdirectories to a level up
  subDirs = os.listdir(destDir + "/" + dirToUnpack)
  for subDir in subDirs:
    shutil.rmtree(destDir + "/" + subDir, True)
    shutil.move(destDir + "/" + dirToUnpack + "/" + subDir,
                destDir + "/" + subDir)

  shutil.rmtree(destDir + "/" + dirToUnpack, True)



def printOptions(optionsDesc):
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



def getCommandLineOptions():

  # optionDesc = [name, value, description]
  optionsDesc = []
  optionsDesc.append(
    ["nupic-core-dir",
     "dir",
     "(optional) Absolute path to nupic.core binary release directory"]
  )
  optionsDesc.append(
    ["skip-compare-versions",
     "",
     "(optional) Skip nupic.core version comparison"]
  )
  optionsDesc.append(
    ["optimizations-native",
    "value",
    "(optional) enable aggressive compiler optimizations"]
  )
  optionsDesc.append(
    ["optimizations-lto",
    "value",
    "(optional) enable link-time optimizations (LTO); currently only for gcc and linker ld.gold"]
  )
  optionsDesc.append(
    ["debug",
    "value",
    "(optional) compile in mode suitable for debugging; overrides any optimizations"]
  )



  # Read command line options looking for extra options
  # For example, an user could type:
  #   python setup.py install --nupic-core-dir="path/to/release"
  # which will set the nupic.core release dir
  optionsValues = dict()
  for arg in sys.argv[:]:
    optionFound = False
    for option in optionsDesc:
      name = option[0]
      if "--" + name in arg:
        value = None
        hasValue = (option[1] != "")
        if hasValue:
          value = arg.partition("=")[2]

        optionsValues[name] = value
        sys.argv.remove(arg)
        optionFound = True
        break

    if not optionFound:
      if ("--help-nupic" in arg):
        printOptions(optionsDesc)
        sys.exit()

  return optionsValues



def getPlatformInfo():
  """
  Identify platform
  """

  if "linux" in sys.platform:
    platform = "linux"
  elif "darwin" in sys.platform:
    platform = "darwin"
  elif "windows" in sys.platform:
    platform = "windows"
  else:
    raise Exception("Platform '%s' is unsupported!" % sys.platform)

  if sys.maxsize > 2**32:
    bitness = "64"
  else:
    bitness = "32"

  return platform, bitness



def getVersion():
  """
  Get version from local file.
  """
  with open("VERSION", "r") as versionFile:
    return versionFile.read().strip()



def generateSwigWrap(swigExecutable, swigFlags, interfaceFile):
  """
  Generate C++ code from the specified SWIG interface file.
  """
  wrap = interfaceFile.replace(".i", "_wrap.cxx")

  cmd = swigExecutable + " -c++ -python "
  for flag in swigFlags:
    cmd += flag + " "
  cmd += interfaceFile
  print cmd
  proc = subprocess.Popen(cmd, shell=True)
  proc.wait()

  return wrap



def findRequirements():
  """
  Read the requirements.txt file and parse into requirements for setup's
  install_requirements option.
  """
  requirementsPath = os.path.join(REPO_DIR, "external/common/requirements.txt")
  return [
    line.strip()
    for line in open(requirementsPath).readlines()
    if not line.startswith("#")
  ]



def getLibPrefix(platform):
  """
  Returns the default system prefix of a compiled library.
  """
  if platform in UNIX_PLATFORMS:
    return "lib"
  elif platform in WINDOWS_PLATFORMS:
    return ""



def getStaticLibExtension(platform):
  """
  Returns the default system extension of a compiled static library.
  """
  if platform in UNIX_PLATFORMS:
    return ".a"
  elif platform in WINDOWS_PLATFORMS:
    return ".lib"



def getSharedLibExtension(platform):
  """
  Returns the default system extension of a compiled shared library.
  """
  if platform in UNIX_PLATFORMS:
    return ".so"
  elif platform in WINDOWS_PLATFORMS:
    return ".dll"




def extractNupicCoreTarget():
  # First, get the nupic.core SHA and remote location from local config.
  nupicConfig = {}
  if os.path.exists(REPO_DIR + "/.nupic_config"):
    execfile(
      os.path.join(REPO_DIR, ".nupic_config"), {}, nupicConfig
    )
  elif os.path.exists(os.environ["HOME"] + "/.nupic_config"):
    execfile(
      os.path.join(os.environ["HOME"], ".nupic_config"), {}, nupicConfig
    )
  else:
    execfile(
      os.path.join(REPO_DIR, ".nupic_modules"), {}, nupicConfig
    )
  return nupicConfig["NUPIC_CORE_COMMITISH"]



def getDefaultNupicCoreDirectories():
  # Default nupic.core location is relative to the NuPIC checkout.
  return (
    REPO_DIR + "/extensions/core/build/release",
    REPO_DIR + "/extensions/core"
  )



def getExtensionModules(nupicCoreReleaseDir, platform, bitness, cmdOptions=None):
  #
  # Gives the version of Python necessary to get installation directories
  # for use with pythonVersion, etc.
  #
  if sys.version_info < (2, 7):
    raise Exception("Fatal Error: Python 2.7 or later is required.")

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

  commonDefines = [
    ("NUPIC2", None),
    ("NTA_OS_" + platform.upper(), None),
    ("NTA_ARCH_" + bitness, None),
    ("NTA_PYTHON_SUPPORT", pythonVersion),
    ("NTA_INTERNAL", None),
    ("NTA_ASSERTIONS_ON", None),
    ("NTA_ASM", None),
    ("HAVE_CONFIG_H", None),
    ("BOOST_NO_WREGEX", None)]

  commonIncludeDirs = [
    REPO_DIR + "/external/" + platform + bitness + "/include",
    REPO_DIR + "/external/common/include",
    REPO_DIR + "/extensions",
    REPO_DIR,
    nupicCoreReleaseDir + "/include",
    pythonIncludeDir,
    numpyIncludeDir]

  commonCompileFlags = [
    # Adhere to c++11 spec
    "-std=c++11",
    # Generate 32 or 64 bit code
    "-m" + bitness,
    # `position independent code`, required for shared libraries
    "-fPIC",
    "-fvisibility=hidden",
    "-Wall",
    "-Wextra",
    "-Wreturn-type",
    "-Wunused",
    "-Wno-unused-parameter",
    # optimization flags (generic builds used for binary distribution)
    "-mtune=generic",
    "-O2",
  ]
  if platform == "darwin":
    commonCompileFlags.append("-stdlib=libc++")

  commonLinkFlags = [
    "-m" + bitness,
    "-fPIC",
    "-L" + nupicCoreReleaseDir + "/lib",
    # for Cap'n'Proto serialization
    "-lkj",
    "-lcapnp",
    "-lcapnpc",
    # optimization (safe defaults)
    "-O2",
  ]

  # Optimizations
  if getCommandLineOption("debug", cmdOptions):
    commonCompileFlags.append("-Og")
    commonCompileFlags.append("-g")
    commonLinkFlags.append("-O0")
  else:
    if getCommandLineOption("optimizations-native", cmdOptions):
      commonCompileFlags.append("-march=native")
      commonCompileFlags.append("-O3")
      commonLinkFlags.append("-O3")
    if getCommandLineOption("optimizations-lto", cmdOptions):
      commonCompileFlags.append("-fuse-linker-plugin")
      commonCompileFlags.append("-flto-report")
      commonCompileFlags.append("-fuse-ld=gold")
      commonCompileFlags.append("-flto")
      commonLinkFlags.append("-flto")



  commonLibraries = [
    "dl",
    "python" + pythonVersion,
    "kj",
    "capnp",
    "capnpc"]
  if platform == "linux":
    commonLibraries.extend(["pthread"])

  commonObjects = [
    nupicCoreReleaseDir + "/lib/" +
      getLibPrefix(platform) + "nupic_core" + getStaticLibExtension(platform)]

  pythonSupportSources = [
    "extensions/py_support/NumpyVector.cpp",
    "extensions/py_support/PyArray.cpp",
    "extensions/py_support/PyHelpers.cpp",
    "extensions/py_support/PythonStream.cpp"]

  extensions = []

  libDynamicCppRegion = Extension(
    "nupic." + getLibPrefix(platform) + "cpp_region",
    extra_compile_args=commonCompileFlags,
    define_macros=commonDefines,
    extra_link_args=commonLinkFlags,
    include_dirs=commonIncludeDirs,
    libraries=commonLibraries,
    sources=pythonSupportSources +
      ["extensions/cpp_region/PyRegion.cpp",
       "extensions/cpp_region/unittests/PyHelpersTest.cpp"],
    extra_objects=commonObjects)
  extensions.append(libDynamicCppRegion)

  #
  # SWIG
  #
  swigDir = REPO_DIR + "/external/common/share/swig/3.0.2"
  swigExecutable = (
    REPO_DIR + "/external/" + platform + bitness + "/bin/swig"
  )

  # SWIG options from:
  # https://github.com/swig/swig/blob/master/Source/Modules/python.cxx#L111
  swigFlags = [
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
    "-nosafecstrings",
    "-w402", #TODO silence warnings
    "-w503",
    "-w511",
    "-w302",
    "-w362",
    "-w312",
    "-w389",
    "-DSWIG_PYTHON_LEGACY_BOOL",
    "-I" + swigDir + "/python",
    "-I" + swigDir]
  for define in commonDefines:
    item = "-D" + define[0]
    if define[1]:
      item += "=" + define[1]
    swigFlags.append(item)
  for includeDir in commonIncludeDirs:
    item = "-I" + includeDir
    swigFlags.append(item)

  wrapAlgorithms = generateSwigWrap(swigExecutable,
                                    swigFlags,
                                    "nupic/bindings/algorithms.i")
  libModuleAlgorithms = Extension(
    "nupic.bindings._algorithms",
    extra_compile_args=commonCompileFlags,
    define_macros=commonDefines,
    extra_link_args=commonLinkFlags,
    include_dirs=commonIncludeDirs,
    libraries=commonLibraries,
    sources=pythonSupportSources + [wrapAlgorithms],
    extra_objects=commonObjects)
  extensions.append(libModuleAlgorithms)

  wrapEngineInternal = generateSwigWrap(swigExecutable,
                                        swigFlags,
                                        "nupic/bindings/engine_internal.i")
  libModuleEngineInternal = Extension(
    "nupic.bindings._engine_internal",
    extra_compile_args=commonCompileFlags,
    define_macros=commonDefines,
    extra_link_args=commonLinkFlags,
    include_dirs=commonIncludeDirs,
    libraries=commonLibraries,
    sources=pythonSupportSources + [wrapEngineInternal],
    extra_objects=commonObjects)
  extensions.append(libModuleEngineInternal)

  wrapMath = generateSwigWrap(swigExecutable,
                              swigFlags,
                              "nupic/bindings/math.i")
  libModuleMath = Extension(
    "nupic.bindings._math",
    extra_compile_args=commonCompileFlags,
    define_macros=commonDefines,
    extra_link_args=commonLinkFlags,
    include_dirs=commonIncludeDirs,
    libraries=commonLibraries,
    sources=pythonSupportSources + [wrapMath,
                                    "nupic/bindings/PySparseTensor.cpp"],
    extra_objects=commonObjects)
  extensions.append(libModuleMath)

  return extensions



def getCommandLineOption(name, options):
  if name is None or options is None:
    return False
  if name in options:
    return options[name]



def prepareNupicCore(options, platform, bitness):

  nupicCoreReleaseDir = getCommandLineOption("nupic-core-dir", options)
  if nupicCoreReleaseDir is not None:
    nupicCoreReleaseDir = os.path.expanduser(nupicCoreReleaseDir)
  nupicCoreSourceDir = None
  fetchNupicCore = True

  if nupicCoreReleaseDir:
    # User specified that they have their own nupic.core
    fetchNupicCore = False
  else:
    nupicCoreReleaseDir, nupicCoreSourceDir = getDefaultNupicCoreDirectories()

  nupicCoreCommitish = extractNupicCoreTarget()

  if fetchNupicCore:
    # User has not specified 'nupic.core' location, so we'll download the
    # binaries.

    nupicCoreRemoteUrl = (NUPIC_CORE_BUCKET + "/nupic_core-"
                          + nupicCoreCommitish + "-" + platform + bitness + ".tar.gz")
    nupicCoreLocalPackage = (nupicCoreSourceDir + "/nupic_core-"
                             + nupicCoreCommitish + "-" + platform + bitness + ".tar.gz")
    nupicCoreLocalDirToUnpack = ("nupic_core-"
                                 + nupicCoreCommitish + "-" + platform + bitness)

    if os.path.exists(nupicCoreLocalPackage):
      print ("Target nupic.core package already exists at "
             + nupicCoreLocalPackage + ".")
      unpackFile(
        nupicCoreLocalPackage, nupicCoreLocalDirToUnpack, nupicCoreReleaseDir
      )
    else:
      print "Attempting to fetch nupic.core binaries..."
      downloadSuccess = downloadFile(
        nupicCoreRemoteUrl, nupicCoreLocalPackage
      )

      # TODO: Give user a way to clean up all the downloaded binaries. It can
      # be manually done with `rm -rf $NUPIC_CORE/extensions/core` but would
      # be cleaner with something like `python setup.py clean`.

      if not downloadSuccess:
        raise Exception("Failed to download nupic.core tarball from %s}! "
                        "Ensure you have an internet connection and that the "
                        "remote tarball exists." % nupicCoreRemoteUrl)
      else:
        print "Download successful."
        unpackFile(nupicCoreLocalPackage,
                        nupicCoreLocalDirToUnpack,
                        nupicCoreReleaseDir)

  else:
    print "Using nupic.core binaries at " + nupicCoreReleaseDir

  if getCommandLineOption("skip-compare-versions", options):
    skipCompareVersions = True
  else:
    skipCompareVersions = not fetchNupicCore

  if not skipCompareVersions:
    # Compare expected version of nupic.core against installed version
    with open(nupicCoreReleaseDir + "/include/nupic/Version.hpp",
              "r") as fileObj:
      content = fileObj.read()

    nupicCoreVersionFound = re.search(
      "#define NUPIC_CORE_VERSION \"([a-z0-9]+)\"", content
    ).group(1)

    if nupicCoreCommitish != nupicCoreVersionFound:
      raise Exception(
        "Fatal Error: Unexpected version of nupic.core! "
        "Expected %s, but detected %s."
        % (nupicCoreCommitish, nupicCoreVersionFound)
      )

  # Copy proto files located at nupic.core dir into nupic dir
  protoSourceDir = glob.glob(os.path.join(nupicCoreReleaseDir, "include/nupic/proto/"))[0]
  protoTargetDir = REPO_DIR + "/nupic/bindings/proto"
  if not os.path.exists(protoTargetDir):
    os.makedirs(protoTargetDir)
  for fileName in glob.glob(protoSourceDir + "/*.capnp"):
    shutil.copy(fileName, protoTargetDir)

  return nupicCoreReleaseDir



def postProcess():
  buildDir = glob.glob(REPO_DIR + "/build/lib.*/")[0]

  # Copy binaries located at nupic.core dir into source dir
  print ("Copying binaries from " + nupicCoreReleaseDir + "/bin" + " to "
         + REPO_DIR + "/bin...")
  if not os.path.exists(REPO_DIR + "/bin"):
    os.makedirs(REPO_DIR + "/bin")
  shutil.copy(
    nupicCoreReleaseDir + "/bin/py_region_test", REPO_DIR + "/bin"
  )
  # Copy cpp_region located at build dir into source dir
  shutil.copy(buildDir + "/nupic/" + getLibPrefix(platform) + "cpp_region" +
              getSharedLibExtension(platform), REPO_DIR + "/nupic")

options = getCommandLineOptions()
platform, bitness = getPlatformInfo()

if platform == DARWIN_PLATFORM and not "ARCHFLAGS" in os.environ:
  raise Exception("To build NuPIC in OS X, you must "
                  "`export ARCHFLAGS=\"-arch x86_64\"`.")

# Build and setup NuPIC
cwd = os.getcwd()
os.chdir(REPO_DIR)

try:
  haveBuild = False
  buildCommands = ["build", "install", "develop", "bdist", "bdist_wheel"]
  for arg in sys.argv[:]:
    if arg in buildCommands:
      haveBuild = True

  if haveBuild:
    nupicCoreReleaseDir = prepareNupicCore(options, platform, bitness)
    extensions = getExtensionModules(
      nupicCoreReleaseDir, platform, bitness, cmdOptions=options
    )
  else:
    extensions = []

  setup(
    name="nupic",
    version=getVersion(),
    install_requires=findRequirements(),
    packages=find_packages(),
    package_data={
      "nupic.support": ["nupic-default.xml",
                        "nupic-logging.conf"],
      "nupic": ["README.md", "LICENSE.txt"],
      "nupic.data": ["*.json"],
      "nupic.frameworks.opf.exp_generator": ["*.json", "*.tpl"],
      "nupic.frameworks.opf.jsonschema": ["*.json"],
      "nupic.swarming.jsonschema": ["*.json"],
      "nupic.datafiles": ["*.csv", "*.txt"],
      "nupic.encoders": ["*.capnp"],
      "nupic.bindings.proto": ["*.capnp"],
    },
    include_package_data=True,
    ext_modules=extensions,
    description="Numenta Platform for Intelligent Computing",
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
  """)

  if haveBuild:
    postProcess()
finally:
  os.chdir(cwd)
