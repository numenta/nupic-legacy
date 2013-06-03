import os
import sys

name = "unix"
template_suffix = 'Makefile.am'
linesep = "\n"
sep = "/"

# A template for a source or header file entry
file_template = '%s \\'

# A template for a project reference entry
reference_template = '%s/lib%s.a \\'

def getProjectName(project):
  """Return the name of the project. Note: project names may not be unique on unix side. Not used on unix side"""
  return os.path.basename(project.dir)

def getProjectfileName(project):
  return os.path.join(project.dir, 'Makefile.am')

def getGUID(project):
    return ''

def getReference(project, relativeRootDir, raw):
  """Given a project name for a static library project, returns 
  a string referring to the library that can be embedded in the project file

  The references will be used to construct the list of static libraries
  that need to be linked to the final executable or dynamic library

  raw is ignored on unix -- the raw references is the same as the processed reference -- 
  a relative path to the library. 
  """
  

  # Use sep instead of os.path.join since we want forward slashes in makefiles
  r = reference_template % (relativeRootDir + sep + project.path, project.name)
                            
  return r

def getEmptyReferences(raw):
  return ['\\']

def postProcessBuildFile(build_file):
  """Remove trailing backslash followed by an empty line and lines with just a backslash

  """
  # get rid of backslash only lines
  result = build_file.replace('\n\\\n', '\n')

  # get rid of trailing back slash
  result = result.replace('\\\n\n', '\n\n')

  return result

def getIgnoreString():
  """Return a string that will mark files tha should be ignored

  Filenames that include the ignore string will not be collected during
  the source files or header files collection process
  """
  return 'win_'

def postProjectsGeneration():
  """Generate the solution file

  This function is called after all the project files
  have been generated
  """
  pass
