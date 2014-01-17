#!/usr/bin/env python
#
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
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
#

import os
import sys
import glob
import string
import shutil
import re
import logging

# Provide access to python build modules
mydir = os.path.abspath(os.path.dirname(__file__))
builddir = os.path.normpath(os.path.join(mydir, os.pardir))
# allows us to import build system modules
sys.path.insert(0, builddir)
# allows us to import helpers
sys.path.insert(0, mydir)
# allows us to import buildinfo files
sys.path.insert(0, ".")
import pybuild.utils as utils
from pybuild.arch import getArch

# Globals
test_list = None
allowedTemplateTypes = [
  'app', 'app_with_python', 'python_binding',  'copy_files',
  'python_binding_with_documentor', 'static_lib', 'dynamic_lib']
log = logging.getLogger("gen")
# Super detailed. debug must also be set
superdebug = False

def _dependencyCompare(project1, project2):
  if project1 in project2.dependencies:
    # project2 uses/depends on project1 -> project1 < project2
    if superdebug: log.debug("%s uses %s" % (project2.path, project1.path))
    return -1
  if project2 in project1.dependencies:
    # project1 uses/depends on project1 -> project1 > project1
    if superdebug: log.debug("%s uses %s" % (project1.path, project2.path))
    return 1
  # If neither is dependent on the other, compare lexicographically
  if superdebug: log.debug("%s (%s) and %s (%s) are independent" % (project1.path, [l.path for l in project1.dependencies], project2.path, [l.path for l in project2.dependencies]))
  return 0

def depSort(listToSort, compare):
  remainingItems = listToSort
  sortedList = []
  while len(remainingItems) > 0:
    # Find the first "smallest" element (not greater than any other element)
    for i in remainingItems:
      smallerItems = [k for k in remainingItems if compare(k, i) < 0]
      if len(smallerItems) == 0:
        sortedList.insert(0,i)
        remainingItems.remove(i)
        break
  return sortedList

def defaultFileCollector(project_dir, regexp=None):
  """Collect selectively source and header files under the project dir

  Used by most projects to dynamically collect their source and header
  files. Doesn't recurse into subdirs.
  """
  source_files = []
  header_files = []
  ignoreRegexp = re.compile(".*_private_.*")

  for ext_list, file_list in ((('.cpp', '.c', '.S'), source_files),
                              (('.hpp', '.h'), header_files)):
    for ext in ext_list:
      files = glob.glob(os.path.join(project_dir, '*' + ext))
      if regexp:
        files = [f for f in files if regexp.match(os.path.splitext(f)[0])]
      files = [f for f in files if not ignoreRegexp.match(os.path.basename(f))]
      file_list += files

  return (header_files, source_files)




def testFileCollector(search_dirs, includePlugins, project_dir):
  """Collect all the plugins and unittests source and header files

  Used by testeverything only. Scans the entire code tree for unittests
  directories and then collectes all the files. It collectes also all the
  files in the testeverything dir itself.
  """
  save_dir = os.getcwd()
  os.chdir(project_dir)
  source_files = []
  header_files = []
  unittest_dirs = []

  # Collect files from all unittests directories
  if test_list:
    test_regexp = re.compile(test_list)
  else:
    test_regexp = None
  for search_dir in search_dirs:
    for (path, dirs, files) in os.walk(os.path.join('../..', search_dir)):
      for d in dirs:
        if os.path.exists(os.path.join(path, d, ".build_system_ignore")):
          dirs.remove(d)
      if os.path.basename(path) == 'unittests':
        (h, s) = defaultFileCollector(os.path.normpath(path),
                             test_regexp)
        source_files.extend(s)
        header_files.extend(h)

  # prepare everything_headers.hpp
  headers = []
  for f in header_files:
    headers.append('#include "%s"' % f)

  headers = sorted(headers)
  text = '\n'.join(headers + [''])

  headers_filename = os.path.join(project_dir, 'everything_headers.hpp')
  if os.path.exists(headers_filename):
    curr_text = open(headers_filename).read()
  else:
    curr_text = None

  if curr_text is None or text != curr_text:
    log.info('%s has been modified' % headers_filename)
    open(headers_filename, 'w').write(text)

  # prepare everything_addtests.hpp
  add_tests = []
  for f in source_files:  
    test_name = os.path.splitext(os.path.basename(f))[0]
    if test_name == 'TesterTest': # special case
      continue
    add_tests.append('ADD_TEST(%s)' % test_name)

  add_tests = sorted(add_tests)
  text = ';\n'.join(add_tests + [''])
  addtests_filename = os.path.join(project_dir, 'everything_addtests.hpp')
  if os.path.exists(addtests_filename):
    curr_text = open(addtests_filename).read()
  else:
    curr_text = None
  if curr_text is None or text != curr_text:
    log.info('%s has been modified' % addtests_filename)
    open(addtests_filename, 'w').write(text)

  # get files of testeverything itself
  (h, s) = defaultFileCollector(project_dir)
  header_files.extend(h)
  source_files.extend(s)

  if includePlugins:
    # Wart alert!
    # Get necessary files from the plugins
    # Ideally we would just be able to link with plugin libraries,
    # but we can't, so we recompile for TestEverything.
    # It would also be nice to generate these lists automatically.
    # We could do that, but we'd bring in a bunch of stuff
    # that isn't needed for testeverything.
    source_files += \
      [
        r'../../plugins/TestPlugin/ReferenceNode2.cpp',
        r'../../plugins/TestPlugin/TestNode2.cpp',
        r'../../plugins/TestPlugin/Real2IntConverter.cpp',
        r'../../plugins/BasicPlugin/VectorFile.cpp',
        r'../../plugins/LearningPlugin/Zeta1Node.cpp',
        r'../../plugins/LearningPlugin/Zeta1SpatialPoolerNode.cpp'
      ]

    header_files += \
      [
        r'../../plugins/TestPlugin/ReferenceNode2.hpp',
        r'../../plugins/TestPlugin/TestNode2.hpp',
        r'../../plugins/TestPlugin/Real2IntConverter.hpp',
        r'../../plugins/BasicPlugin/VectorFile.hpp',
        r'../../plugins/LearningPlugin/Zeta1Node.hpp',
        r'../../plugins/LearningPlugin/Zeta1SpatialPoolerNode.hpp'
      ]


  os.chdir(save_dir)
  return (header_files, source_files)

from functools import partial
nupicTestFileCollector = partial(testFileCollector, ['nta'], False)

class Project(object):
  def __init__(self, dir):
    self.dir = dir

    # Name of project is name of dir.
    # Name of build file on windows may not be project_name.vcproj (see win32name)
    self.name = os.path.basename(dir)

    # These may be set later in this method
    self.templateType = None
    self.fileCollector = defaultFileCollector

    # A list of immediate dependencies from the buildinfo file.
    self.initialDependencies = list()

    # Created in _generateProject()
    self.generated = False
    self.generationStarted = False
    self.dependencies = list()        # A list of project objects. Includes all dependencies
    self.win32name = self.name        # windows project name may be different from dir name
    self.buildFile = None             # text of the buildile we are generating. saved if changed
    self.guid = None                  # windows guid from buildinfo.py
    self.source_files = None          # lists of source files we reference in the build file
    self.header_files = None

    # Our "path" is the path to the directory relative to the root
    # of the source tree, in a canonical format (forward slashes)
    # It's a bit messy to reconstruct this path. We walk up from
    # our directory, prepending to path, and stopping if we appear
    # to be in the root of the source tree
    path = ""
    components = dir.split(os.path.sep)
    components.reverse()
    rootdir = dir
    for component in components:
      rootdir = os.path.dirname(rootdir)
      if path == "":
        path = component
      else:
        path = component + "/" + path
      if os.path.isdir(os.path.join(rootdir, "build_system")):
        break
    if not os.path.isdir(os.path.join(rootdir, "build_system")):
      raise Exception("Unable to find root directory for %s" % dir)
    self.path = path

    # @todo buildFile is associated with single architecture. fix
    savePath = os.getcwd()
    os.chdir(dir)

    # get templateType (required), guid (required),
    # initialDependencies (desired), fileCollector (optional) from file
    try:
      settings = __import__("buildinfo")
    except Exception, e:
      raise Exception("Unable to import buildinfo in directory %s: %s" % (dir, e))
    buildinfoFilename = os.path.abspath(settings.__file__)

    if settings.__dict__.has_key("templateType"):
      self.templateType = settings.templateType
      if self.templateType not in allowedTemplateTypes:
        raise Exception("Invalid template type %s specified for project %s. Allowed values are %s" % (self.templateType, self.path, allowedTemplateTypes))
    else:
      raise Exception("No template type specified in file %s" % buildinfoFilename)

    if settings.__dict__.has_key("guid"):
      self.guid = settings.guid
    elif self.templateType != "header_only":
      raise Exception("No guid specified for file %s" % buildinfoFilename)

    if settings.__dict__.has_key("fileCollector"):
      f = settings.fileCollector
      if type(f) == type(defaultFileCollector):
        self.fileCollector = f
      elif type(f) == type(str()):
        if globals().has_key(f):
          self.fileCollector = globals()[f]
        else:
          raise Exception("file collector %s specified in %s does not exist" % (f, buildinfoFilename))
      else:
        raise Exception("file collector unknown type %s specified in %s" % (type(f), buildinfoFilename))

    if settings.__dict__.has_key("dependencies"):
      self.initialDependencies = settings.dependencies
    else:
      if self.templateType != "header_only":
        log.warn("Warning: project file %s has no dependencies" % buildinfoFilename)

    if settings.__dict__.has_key("win32name"):
      self.win32name = settings.win32name

    # all projects but nupic.algorithms have a standard value for SWIGTypeTable
    # To avoid specifying it in all buildinfo.py files, set it explicitly here if unset
    if not settings.__dict__.has_key("swigTypeTable"):
      self.swigTypeTable = "_nupic_" + os.path.basename(self.dir)
    else:
      self.swigTypeTable = settings.swigTypeTable

    del sys.modules["buildinfo"]
    os.chdir(savePath)

class Generator(object):
  def __init__(self, root_dir, helper, extraSubstitutions=None):
    self.rootDir = root_dir
    self.helper = helper
    self.ignore = helper.getIgnoreString()
    self.projects = dict()
    self._populateProjectList()
    self.extraSubstitutions = extraSubstitutions

  def generateProjects(self):
    for p in self.projects.values():
      self._generateProject(p)

  def _populateProjectList(self):
    """Populates the list of projects to be generated
    """
    for (path,dirs,files) in os.walk(self.rootDir, topdown=True):
      # prune
      if ".svn" in dirs:
        dirs.remove(".svn")
      for d in dirs:
        if os.path.exists(os.path.join(path, d, ".build_system_ignore")):
          dirs.remove(d)
      if "buildinfo.py" in files:
        print path
        project = Project(path)
        if self.projects.has_key(project.path):
          raise Exception("_populateProjectList: found more than project of path '%s'" % path)
        self.projects[project.path] = project

  def _processFileList(self, file_list):

    """Use relative paths for files in the same directory;
    convert filenames to native format"""

    def getProperPath(f):
      if os.path.isabs(f):
        return os.path.basename(f)
      return f

    # Filter out filenames that contain the ignore string
    if self.ignore:
      file_list = [f for f in file_list if not self.ignore in f]

    # Convert absolute pathnames to filenames in the current directory
    file_list = [getProperPath(f) for f in file_list]

    return file_list

  def _formatFileList(self, file_list):

    """Convert a file list to a text fragment

    The text fragment will be embedded in the generated
    build file (as either source files or header files).
    It relies on the helper file template
    """

    # Make sure paths have "/" on unix and "\" on windows
    file_list = [l.replace("\\", self.helper.sep) for l in file_list]
    file_list = [l.replace("/", self.helper.sep) for l in file_list]

    # Format the filenames using the file template
    file_list = [self.helper.file_template % f for f in file_list]

    # Convert from a list of strings to a single big string of lines
    file_list = self.helper.linesep.join(file_list)

    return file_list

  def _getReferences(self, project, raw=False):
    """Collect project references recursuvely

    The references are based on the dependencies
    of the project, which are stored in project.dependencies
    """

    dependencies = project.dependencies
    references = []
    for p in dependencies:
      if (p.templateType == "static_lib" or 
          p.templateType == "static_lib_install" or
          p.templateType == "static_lib2"):
        if superdebug: log.debug("adding reference for project %s" % (p.path))
        r = self.helper.getReference(p, self._getRelativeRootDir(project.path), raw)
        references.append(r)

    if not references:
      references = self.helper.getEmptyReferences(raw)

    return references

  def _getRelativeRootDir(self, relativePath):
    # break both to tokens. Project paths have "/" -- they are not filesystem pathnames
    tokens = relativePath.split("/")
    depth = len(tokens)
    relativeRootDir = self.helper.sep.join(['..'] * depth)

    return relativeRootDir

  def _generateProject(self, project):
    if project.generated:
      return

    if project.generationStarted:
      raise Exception("Circular dependency: project %s being regenerated!" % project.path)

    project.generationStarted = True

    # Collect source and header files first
    # get basic list of files
    (project.header_files, project.source_files) = project.fileCollector(project.dir)
    # Create a big string that is a list of files
    # with appropriate line separate. (filename + trailing backslash
    # for Makefiles, XML element for vcproj


    project.source_files = self._processFileList(project.source_files)
    project.header_files = self._processFileList(project.header_files)

    # Convert lists to a single string for use in build files
    source_file_string = self._formatFileList(project.source_files)
    header_file_string = self._formatFileList(project.header_files)


    # Make sure our dependencies are valid
    for dep in project.initialDependencies:
      if not self.projects.has_key(dep):
        raise Exception("Project %s depends on project %s which was not found" % (project.path, dep))

    dependencies = [self.projects[dep] for dep in project.initialDependencies]

    if superdebug: log.debug("Initial dependencies for %s: %s" % (project.path, project.initialDependencies))

    # Make sure that everything we depend on already has dependencies generated
    # This is recursive. It terminates as long as we have no circular dependencies
    # (and some "leaf" projects have no dependencies)
    # @todo detect circular dependency
    for dep in dependencies:
      if dep.generated:
        continue
      self._generateProject(dep)

    project.generated = True

    # Generate dependencies recursively.
    # If we get here, all of the projects we depend on will have their dependencies generated
    for projectWeUse in dependencies:
      if superdebug: log.debug("indirect dependencies of %s are %s" % (dep.path, [l.path for l in projectWeUse.dependencies]))
      for indirectDependency in projectWeUse.dependencies:
        if indirectDependency not in dependencies:
          if superdebug: log.debug("adding indirect dependency %s" % indirectDependency.path)
          dependencies.append(indirectDependency)
        else:
          if superdebug: log.debug("indirect dependency %s already exists" % indirectDependency.path)

    # At this point we have all the dependencies, but
    # but they are not in the right order.

    project.dependencies = dependencies
    if superdebug: log.debug("Initial full dependencies for %s: %s" % (project.path, [l.path for l in project.dependencies]))

    project.dependencies = depSort(project.dependencies, _dependencyCompare)

    log.debug("Final Dependencies for %s: %s" % (project.path, [l.path for l in project.dependencies]))


    # Prepare project references (a.k.a dependencies)
    # This is a list of references to the projects we depend on,
    # in a format suitable for the build file, e.g.
    # -L../../../nta/foundation/libfoundation.a for Makefiles
    # Order is important. If A uses B then we want A to come before B in the refs
    references = self._getReferences(project)

    # Convert from a list of strings to a single big string of lines
    references = self.helper.linesep.join(references)


    # Raw references is a list of references (libraries) in a format
    # suitable for combine_libs.py
    rawReferences = self._getReferences(project, True)
    rawReferences = " ".join(rawReferences)


    # These should be part of the Project class, but right now the Project constructor doesn't know about helpers
    # projectFilename is the full path to the project file. e.g. the Makefile.am or foundation.vcproj file.
    # dirName is the full path to the project directory
    # @todo projectName and dirName are normally the same but may be different for python bindings
    projectName = self.helper.getProjectName(project)
    dirName = os.path.basename(project.dir)

    # Distance of project dir from root dir (relative depth)
    # This is important for the Makefile.am templates for static
    # libraries that are used by projects in different relative depths
    # so it can be hard-coded into the template
    relativeRootDir = self._getRelativeRootDir(project.path)

    # Python may be or 2.5 or 2.6
    pythonVersion = sys.version[:3]
    assert pythonVersion in ('2.5', '2.6', '2.7')
    
    pythonVersionNum = pythonVersion[:3:2]
    
    # Visual Studio Version
    if pythonVersion == '2.5':
      visualStudioVersion = '8.00' # Visual Studio 2005 for Python 2.5
    else:
      visualStudioVersion = '9.00' # Visual Studio 2008 for Python 2.6

    # Prepare substitution dictionary
    d = dict(RelativeRootDir=relativeRootDir,
             DirName=dirName,
             ProjectName=projectName,
             SourceFiles=source_file_string,
             HeaderFiles=header_file_string,
             References=references,
             RawReferences=rawReferences,
             Win32BuildDir="$(SolutionDir)\\win32build",
             Win32InstallDir="$(NTAX_INSTALL_DIR)",
             Win32PythonDir="$(NTAX_PYTHON_DIR)",
             VisualStudioVersion=visualStudioVersion,
             SWIGTypeTable=project.swigTypeTable,
             PythonVersion=pythonVersion,
             PythonVersionNum=pythonVersionNum)

    if self.extraSubstitutions is not None:
      for (key, value) in self.extraSubstitutions.iteritems():
        d[key] = value


    # Generate build file from project template
    # (using PEP-292 string.Template substitution)
    baseDir = os.path.join(mydir, "templates")
    templateFilename = project.templateType + "_template." + self.helper.template_suffix
    templateFile = os.path.join(baseDir, templateFilename)
    log.debug("Using template %s for project %s" % (templateFilename, project.name))
    template = string.Template(open(templateFile).read())
    try:
      buildFile = template.substitute(d)
    except Exception, e:
      raise Exception("Error doing template substitution on %s: %s" % (templateFile, e))

    # Get GUID if necessary
    guid = project.guid

    # Substitute the GUID (possible in 2nd phase because it relies on
    # the first substitution in order to find an exisitng .vcproj file (if any)
    buildFile = buildFile % { 'GUID':guid }

    # Post-process the entire file
    buildFile = self.helper.postProcessBuildFile(buildFile)

    project.buildFile = buildFile

  def saveProjects(self, save, delete_manifest_file):

    for p in self.projects.values():
      # Save the manifest file for all projects except the post_build project
      if p.templateType != "copy_files":
        manifestPath = os.path.join(p.dir, "project.manifest")
        if delete_manifest_file and os.path.exists(manifestPath):
          os.remove(manifestPath)
          existing_names = []
        else:
          if os.path.exists(manifestPath):
            f = open(manifestPath)
            existing_names = f.readlines()
            f.close()
            existing_names = [name.strip() for name in existing_names]
          else:
            existing_names = []


        # write names to the file if they aren't already there.
        f = open(manifestPath, "a")
        for name in p.header_files + p.source_files:
          name = os.path.join(p.path, name)
          if name not in existing_names:
            # paths in manifest file must be relative to the root
            print >> f, name
        # always include the project file!
        print >> f, os.path.join(p.path, os.path.basename(self.helper.getProjectfileName(p)))
        f.close()


      # Save build file only if modified
      filename = self.helper.getProjectfileName(p)
      if os.path.exists(filename):
        text = open(filename).read()
      else:
        text = None

      if p.buildFile is None:
        if text is None:
          log.info("   NOFILE %s" % p.path)
        else:
          log.warn("WARNING: No build file generated for project %s but one already exists" % p.path)
        continue
      elif text is not None:
        if text != p.buildFile:
          log.info("  CHANGED %s" % filename)
        else:
          log.debug("UNCHANGED %s" % filename)
      else:
        log.info("      NEW %s" % filename)


      # Save build file file if necessary and different
      if save and text != p.buildFile:
        open(filename, 'w').write(p.buildFile)

    log.info("Processed %d projects" % len(self.projects))

  def postGeneration(self):
    self.helper.postProjectsGeneration()


def usage():
  usageMessage = \
"""

Usage:
python buildfile_gen.py --rootdir=<root dir>
                           [--platform=<platform>]
                           [--save]
                           [--testlist=<regexp>]

--rootdir (mandatory): the root directory of the code tree

--platform (optional): the platform to generate build files for. It defaults
to sys.platform, but if specified allows cross-generating such as generating
Windows .vcproj files on a unix machine (necessary for auto build integration).
To generate Windows .vcproj specify 'win32'. Anything else will result in
Makefile.am generation.

--save (optional): if '--save' is specified the generated project files
will replace the exisitng ones. The default is not to save and just to generate
the projects and verify if they are different.

--testlist (optional): if '--testlist' is specified testeverything will link only
the unit tests whose filenames match the regular expression.
"""
  print usageMessage
  sys.exit(1)


def generate_buildfiles(rootdir, save_project_files, extraSubstitutions=None):

  # @todo Get rid of globals. Refactor to do it all in one pass
  for helper_name in ["makefile_helper"]:
    helper = __import__(helper_name)
    log.info("Generating build files for %s" % helper.name)

    g = Generator(rootdir, helper, extraSubstitutions)
    g.generateProjects()
    if helper_name == "vcproj_helper":
      delete_manifest_file = True
    else:
      delete_manifest_file = False
    g.saveProjects(save_project_files, delete_manifest_file)
    g.postGeneration()

  log.info('Done generating build files for %s' % helper.name)

if __name__=='__main__':
  import getopt
  optionSpec = ["rootdir=", "platform=", "save", "testlist=", "win32BuildDir=", "win32InstallDir=", "win32PythonDir="]

  rootdir = None
  platform = getArch()
  extraSubstitutions = dict()

  try:
    (opts, args) = getopt.gnu_getopt(sys.argv[1:], "", optionSpec)
  except Exception, e:
    print "Error parsing command line: %s" % e
    usage()

  if len(args) > 0:
    usage()

  save_project_files = True
  for (option, val) in opts:
    if option == '--rootdir':
      rootdir = val
    elif option == '--save':
      save_project_files = True
    elif option ==  '--testlist':
      test_list = val
    elif option == "--win32InstallDir":
      extraSubstitutions["Win32InstallDir"] = val
    elif option == "--win32BuildDir":
      extraSubstitutions["Win32BuildDir"] = val
    elif option == "--win32PythonDir":
      extraSubstitutions["Win32PythonDir"] = val


  debug = False
  if debug:
    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout,
                        format="%(message)s")
    logging.getLogger('').setLevel(logging.DEBUG)
  else:
    logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                        format="%(message)s")
    logging.getLogger('').setLevel(logging.INFO)


  if rootdir == None:
    rootdir = os.path.normpath(os.path.join(mydir, os.pardir, os.pardir))
    log.info("Using root directory: %s" % rootdir)

  # Convenience. Allows use of "~" in pathnames and other things.
  rootdir = os.path.abspath(os.path.normpath(os.path.expanduser(rootdir)))

  generate_buildfiles(rootdir, save_project_files)
