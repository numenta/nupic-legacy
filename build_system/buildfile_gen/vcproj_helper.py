import os
import sys
import glob
# import uuid

name = "win32"
template_suffix = 'vcproj'
linesep = "\r\n"
sep = "\\"

# A template for a source or header file entry
file_template = ' '*6 + '<File RelativePath="%s" />'

# A template for a project reference entry
reference_template = """\
    <ProjectReference
      ReferencedProjectIdentifier="%s"
      RelativePathToProject="./%s"
    />"""

def getProjectName(project):
  """Return the name of the project"""
  return project.win32name

def getProjectfileName(project):
  """Return the project filename (.vcproj file)
  """
  return os.path.join(project.dir, project.win32name + "." + template_suffix)



# Not currently used. GUIDs are pre-generated and in the buildinfo.py files
# def getGUID(project):
  #guid = '{00000000-0000-0000-0000-00000000}'
  #
  ##filename = getVcProjFilename(project)
  #filename = getProjectFilename(project.name)
  #if os.path.isfile(filename):
  #  lines = open(filename).readlines()
  #  for line in lines:
  #    if line.find('ProjectGUID="{') != -1:
  #      start = line.find('{');
  #      end = line.find('}');
  #      guid = line[start:end+1]
  #
  #return guid
#  return '{' + str(uuid.uuid4()) + '}'

def getReference(project, relativeRootDir, raw):
  """Returns a reference string that can be embedded in the project file

  Ignore the relativeRootDir parameter. All paths are relative to the root, 
  not relative to the referring project.
  """
  guid = project.guid

  if not raw:
    relativePath = project.path.replace('\\', '/')
    relativePath += '\%s.vcproj' % project.win32name
    r = reference_template % (guid, relativePath)
  else:
    r = project.name
    
  return r

def getEmptyReferences(raw):
  return []

def postProcessBuildFile(build_file):
  return build_file

def getIgnoreString():
  """Return a string that will mark files tha should be ignored

  Filenames that include the ignore string will not be collected during
  the source files or header files collection process
  """
  return 'unix_'

def postProjectsGeneration():
  """Generate the solution file

  This function is called after all the project files
  have been generated
  """
  pass
