import sys
import os
import subprocess
import shutil
import glob
import urllib2
import tarfile
import re
import numpy
from distutils import ccompiler
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
HOME_DIR = os.path.expanduser("~")



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
    print "expecting %s" % dirToUnpack

  with tarfile.open(package, "r:gz") as tarFileObj:
    tarFileObj.extractall(destDir)

  # debug
  print "Unpacked tarball contains the following files:"
  print os.listdir(destDir)

  # Copy subdirectories to a level up
  subDirs = os.listdir(os.path.join(destDir, dirToUnpack))
  for subDir in subDirs:
    shutil.rmtree(os.path.join(destDir, subDir), True)
    shutil.move(
      os.path.join(destDir, dirToUnpack, subDir),
      os.path.join(destDir, subDir)
    )

  shutil.rmtree(os.path.join(destDir, dirToUnpack), True)



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
  # All windows platform show up as "win32". 
  # See http://stackoverflow.com/questions/2144748/is-it-safe-to-use-sys-platform-win32-check-on-64-bit-python
  elif "win32" == sys.platform:
    platform = "windows"
  else:
    raise Exception("Platform '%s' is unsupported!" % sys.platform)

  # Python 32-bits doesn't detect Windows 64-bits so the workaround is 
  # check whether "ProgramFiles (x86)" environment variable exists.
  is64bits = (sys.maxsize > 2**32 or 
    (platform in WINDOWS_PLATFORMS and 'PROGRAMFILES(X86)' in os.environ))
  if is64bits:
     bitness = "64"
  else:
    bitness = "32"

  return platform, bitness



def getCompilerInfo():
  """
  Identify compiler
  """

  cxxCompiler = ccompiler.get_default_compiler()
  if "msvc" in cxxCompiler:
    cxxCompiler = "MSVC"
  elif "clang" in cxxCompiler:
    cxxCompiler = "Clang"
  elif "gnu" in cxxCompiler:
    cxxCompiler = "GNU"
  # TODO: There is a problem here, because on OS X ccompiler.get_default_compiler()
  # returns "unix", not "clang" or "gnu". So we have to handle "unix" and we loose
  # the ability to decide which compiler is used. I'm not sure how big of a 
  # problem this is, so I'm moving ahead with this noted. 
  elif "unix" in cxxCompiler:
    cxxCompiler = "unix"
  else:
    raise Exception("C++ compiler '%s' is unsupported!" % cxxCompiler)

  return cxxCompiler



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
  requirementsPath = os.path.join(
    REPO_DIR, "external", "common", "requirements.txt"
  )
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



def getExecutableExtension(platform):
  """
  Returns the default system extension of an executable.
  """
  if platform in UNIX_PLATFORMS:
    return ""
  elif platform in WINDOWS_PLATFORMS:
    return ".exe"



def extractNupicCoreTarget():
  # First, get the nupic.core SHA and remote location from local config.
  nupicConfig = {}
  # Look for .nupic_config in repository directory.
  if os.path.exists(os.path.join(REPO_DIR, ".nupic_config")):
    execfile(
      os.path.join(REPO_DIR, ".nupic_config"), {}, nupicConfig
    )
  # Look for .nupic_config in HOME directory.
  elif os.path.exists(os.path.join(HOME_DIR, ".nupic_config")):
    execfile(
      os.path.join(HOME_DIR, ".nupic_config"), {}, nupicConfig
    )
  # Use default local .nupic_modules instead.
  else:
    execfile(
      os.path.join(REPO_DIR, ".nupic_modules"), {}, nupicConfig
    )
  return nupicConfig["NUPIC_CORE_COMMITISH"]



def getDefaultNupicCoreDirectories():
  # Default nupic.core location is relative to the NuPIC checkout.
  return (
    os.path.join(REPO_DIR, "extensions", "core", "build", "release"),
    os.path.join(REPO_DIR, "extensions", "core")
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
  if platform in WINDOWS_PLATFORMS:
    pythonIncludeDir = os.path.join(pythonPrefix, "include")
    pythonLib = "python" + pythonVersion.replace(".", "")
  else:
    pythonIncludeDir = os.path.join(
      pythonPrefix, "include", ("python" + pythonVersion)
    )
    pythonLib = "python" + pythonVersion

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
  if platform in WINDOWS_PLATFORMS:
    commonDefines.extend([
      ("PSAPI_VERSION", "1"),
      ("APR_DECLARE_STATIC", None),
      ("APU_DECLARE_STATIC", None),
      ("ZLIB_WINAPI", None),
      ("WIN32", None),
      ("_WINDOWS", None),
      ("_MBCS", None),
      ("_CRT_SECURE_NO_WARNINGS", None),
      ("NDEBUG", None)])
  else:
    commonDefines.append(("HAVE_UNISTD_H", None))
  if cxxCompiler == "GNU":
    commonDefines.append(("NTA_COMPILER_GNU", None))
  elif cxxCompiler == "Clang":
    commonDefines.append(("NTA_COMPILER_CLANG", None))
  elif cxxCompiler == "MSVC":
    commonDefines.extend([
      ("NTA_COMPILER_MSVC", None),
      ("CAPNP_LITE", "1"),
      ("_VARIADIC_MAX", "10"),
      ("NOMINMAX", None)])

  commonIncludeDirs = [
    os.path.join(REPO_DIR, "external", platform + bitness, "include"),
    os.path.join(REPO_DIR, "external", "common", "include"),
    os.path.join(REPO_DIR, "extensions"),
    REPO_DIR,
    os.path.join(nupicCoreReleaseDir, "include"),
    pythonIncludeDir,
    numpyIncludeDir]

  if cxxCompiler == "MSVC":
    commonCompileFlags = [
      "/TP",
      "/Zc:wchar_t",
      "/Gm-",
      "/fp:precise",
      "/errorReport:prompt",
      "/W3",
      "/WX-",
      "/GR",
      "/Gd",
      "/GS-",
      "/Oy-",
      "/EHs",
      "/analyze-",
      "/nologo"]
    commonLinkFlags = [
      "/NOLOGO",
      "/SAFESEH:NO",
      "/NODEFAULTLIB:LIBCMT",
      "/LIBPATH:" + pythonPrefix + "/libs",
      "/LIBPATH:" + nupicCoreReleaseDir + "/lib"]
    if bitness == "32":
      commonLinkFlags.append("/MACHINE:X86")
    else:
      commonLinkFlags.append("/MACHINE:X" + bitness)
  else:
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
      "-O2"]
    commonLinkFlags = [
      "-m" + bitness,
      "-fPIC",
      "-L" + nupicCoreReleaseDir + "/lib",
      # for Cap'n'Proto serialization
      "-lkj",
      "-lcapnp",
      "-lcapnpc",
      # optimization (safe defaults)
      "-O2"]
  if platform == DARWIN_PLATFORM:
    commonCompileFlags.append("-stdlib=libc++")

  # Optimizations
  if cmdOptions is not None and getCommandLineOption("optimizations-native", cmdOptions):
    if cxxCompiler != "MSVC":
      commonCompileFlags.extend([
        "-march=native",
        "-O3"])
      commonLinkFlags.append("-O3")
  if cmdOptions is not None and getCommandLineOption("optimizations-lto", cmdOptions):
    if cxxCompiler != "MSVC":
      commonCompileFlags.extend([
        "-fuse-linker-plugin",
        "-flto-report",
        "-fuse-ld=gold",
        "-flto"])
      commonLinkFlags.append("-flto")

  commonLibraries = [
    pythonLib,
    "nupic_core",
    "gtest",
    "kj",
    "capnp",
    #"capnpc",
    ]
  if platform in UNIX_PLATFORMS:
    commonLibraries.append("dl")
    if platform == LINUX_PLATFORM:
      commonLibraries.append("pthread")
  elif platform in WINDOWS_PLATFORMS:
    commonLibraries.extend([
      "oldnames",
      "psapi",
      "ws2_32",
      "shell32",
      "advapi32"])

  pythonSupportSources = [
    os.path.join("extensions", "py_support", "NumpyVector.cpp"),
    os.path.join("extensions", "py_support", "PyArray.cpp"),
    os.path.join("extensions", "py_support", "PyHelpers.cpp"),
    os.path.join("extensions", "py_support", "PythonStream.cpp")]

  extensions = []

  libDynamicCppRegion = Extension(
    "nupic." + getLibPrefix(platform) + "cpp_region",
    extra_compile_args=commonCompileFlags,
    define_macros=commonDefines,
    extra_link_args=commonLinkFlags,
    export_symbols=None,
    include_dirs=commonIncludeDirs,
    libraries=commonLibraries,
    sources=pythonSupportSources +
      [
        os.path.join("extensions", "cpp_region", "PyRegion.cpp"),
        os.path.join("extensions", "cpp_region", "unittests", "PyHelpersTest.cpp")
       ])
  extensions.append(libDynamicCppRegion)

  #
  # SWIG
  #
  swigDir = os.path.join(REPO_DIR, "external", "common", "share", "swig", "3.0.2")
  swigExecutable = (
    os.path.join(REPO_DIR, "external", platform + bitness, "bin", "swig")
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
    "-I" + os.path.join(swigDir, "python"),
    "-I" + swigDir]
  for define in commonDefines:
    item = "-D" + define[0]
    if define[1]:
      item += "=" + define[1]
    swigFlags.append(item)
  for includeDir in commonIncludeDirs:
    item = "-I" + includeDir
    swigFlags.append(item)

  wrapAlgorithms = generateSwigWrap(
    swigExecutable,
    swigFlags,
    os.path.join("nupic", "bindings", "algorithms.i")
  )
  libModuleAlgorithms = Extension(
    "nupic.bindings._algorithms",
    extra_compile_args=commonCompileFlags,
    define_macros=commonDefines,
    extra_link_args=commonLinkFlags,
    include_dirs=commonIncludeDirs,
    libraries=commonLibraries,
    sources=pythonSupportSources + [wrapAlgorithms])
  extensions.append(libModuleAlgorithms)

  wrapEngineInternal = generateSwigWrap(
    swigExecutable,
    swigFlags,
    os.path.join("nupic", "bindings", "engine_internal.i")
  )
  libModuleEngineInternal = Extension(
    "nupic.bindings._engine_internal",
    extra_compile_args=commonCompileFlags,
    define_macros=commonDefines,
    extra_link_args=commonLinkFlags,
    include_dirs=commonIncludeDirs,
    libraries=commonLibraries,
    sources=pythonSupportSources + [wrapEngineInternal])
  extensions.append(libModuleEngineInternal)

  wrapMath = generateSwigWrap(
    swigExecutable,
    swigFlags,
    os.path.join("nupic", "bindings", "math.i")
  )
  libModuleMath = Extension(
    "nupic.bindings._math",
    extra_compile_args=commonCompileFlags,
    define_macros=commonDefines,
    extra_link_args=commonLinkFlags,
    include_dirs=commonIncludeDirs,
    libraries=commonLibraries,
    sources=pythonSupportSources + [
      wrapMath,
      os.path.join("nupic", "bindings", "PySparseTensor.cpp")
    ])
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
    nupicCoreLocalPackage = (os.path.join(nupicCoreSourceDir, "nupic_core-"
                             + nupicCoreCommitish + "-" + platform + bitness + ".tar.gz"))
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
        raise Exception("Failed to download nupic.core tarball from %s! "
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
    versionHpp = os.path.join(
      nupicCoreReleaseDir, "include", "nupic", "Version.hpp"
    )
    with open(versionHpp, "r") as fileObj:
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
  protoSourceDir = glob.glob(os.path.join(nupicCoreReleaseDir, "include", "nupic", "proto"))[0]
  protoTargetDir = os.path.join(REPO_DIR, "nupic", "bindings", "proto")
  if not os.path.exists(protoTargetDir):
    os.makedirs(protoTargetDir)
  for fileName in glob.glob(protoSourceDir + os.pathsep + "*.capnp"):
    shutil.copy(fileName, protoTargetDir)

  return nupicCoreReleaseDir



def postProcess():
  buildDir = glob.glob(
    REPO_DIR + "/build/lib.*/"
  )[0]

  # Copy binaries located at nupic.core dir into source dir
  print ("Copying binaries from " + nupicCoreReleaseDir + "/bin" + " to "
         + REPO_DIR + "/bin...")
  if not os.path.exists(os.path.join(REPO_DIR, "bin")):
    os.makedirs(os.path.join(REPO_DIR, "bin"))
  shutil.copy(
    os.path.join(nupicCoreReleaseDir, "bin", 
      ("py_region_test" + getExecutableExtension(platform))
    ), 
    os.path.join(REPO_DIR, "bin")
  )
  # Copy cpp_region located at build dir into source dir
  if platform in WINDOWS_PLATFORMS:
    # By default, shared libs use "pyd" extension in Windows
    os.rename(
      os.path.join(buildDir, "nupic", (getLibPrefix(platform) + "cpp_region.pyd")),
      os.path.join(buildDir, "nupic", (getLibPrefix(platform) + "cpp_region.dll"))
    )
  shutil.copy(
    os.path.join(
      buildDir, 
      "nupic", 
      (getLibPrefix(platform) + "cpp_region" + getSharedLibExtension(platform))
    ),
    os.path.join(REPO_DIR, "nupic")
  )

options = getCommandLineOptions()
platform, bitness = getPlatformInfo()
cxxCompiler = getCompilerInfo()

if platform == DARWIN_PLATFORM and not "ARCHFLAGS" in os.environ:
  raise Exception("To build NuPIC in OS X, you must "
                  "`export ARCHFLAGS=\"-arch x86_64\"`.")
elif platform in WINDOWS_PLATFORMS and not "VS90COMNTOOLS" in os.environ:
  raise Exception("To build NuPIC in Windows, you must "
                  "`set VS90COMNTOOLS=%VS140COMNTOOLS%`.")

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
