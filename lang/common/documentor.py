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

"""Extract documentation from C++ header files

The documentor scans Python files (later other languages) and looks for
references to specially formatted (YAML) C++ comments in the NuPIC 2 object model
header files. It then extracts the C++ comments, parses the YAML into a
dictionary that contains information like method name, description, arguments
and return value. It then generates a correponding Python documentation block
and writes a post-processed Python source file where the place holder
reference to the C++ documentation is replaced with the generated documentation.

The final artifact is a file in the same directory as the source file with a
"doc." prefix. For example, running documentor on lang/py/__init__.py creates
lang/py/engine/doc.__init__.py
"""

import os
import sys
import re
from pprint import pprint as pp
import operator

scriptDir = os.path.dirname(__file__)
externalDir = os.path.abspath(os.path.join(scriptDir, '../../external'))
pybuildDir = os.path.abspath(os.path.join(scriptDir, '../../build_system/pybuild'))
langPyDir = os.path.abspath(os.path.join(scriptDir, '../py'))

# Get the architecture first
sys.path = [os.path.join(pybuildDir)] + sys.path
import arch
a = arch.getArch()

# Get yaml from external (it is not installed)
pythonVersion = '%d.%d' % sys.version_info[:2]
sys.path = [os.path.join(externalDir, a,
            'lib/python%s/site-packages' % pythonVersion)] + sys.path
import yaml

# Restore sys.path
sys.path = sys.path[2:]

# The directory that contains the NuPIC 2 C++ object model
baseDir = os.path.abspath(os.path.join(scriptDir, '../../nta/engine'))
assert os.path.isdir(baseDir)

def getBlock(lines):
  """Clean the C++ comments and parse the YAML to a dictionary"""
  # Verify that all lines start with // at the same position
  assert len(lines) > 0
  pos = lines[0].index('//')
  for line in lines[1:]:
    assert line.index('//') == pos
    
  # Remove C++ comment and preceding whitespace
  lines = [line[pos+2:] for line in lines]
  text = ''.join(lines)
  try:
    block = yaml.load(text)
  except Exception, e:
    print text
    print
  return block

def getDocBlocks(filename):
  """Get all the YAML doc blocks in a C++ header file
  
  Parse the file and collect all the text blocks are surround by the
  "@doc:begin" and "@doc:end" delimiters. Remove the C++ commants from
  each block.

  Parse the YAML of each block into a standard Python dictionary. Store each
  doc dictionary in the result dict where the key is the name of the doc block
  and the value is the parsed YAML dictionary
  """
  blocks = {}
  filename = os.path.join(baseDir, filename) +  '.hpp'
  if not os.path.isfile(filename):
    raise Exception('No such file:' + filename)
  
  block_starts = []
  block_ends = []
  lines = open(filename).readlines()
  lookFor = 'begin'
  for i, line in enumerate(lines):
    if '@doc:begin' in line:
      if lookFor != 'begin':
        assert False
      block_starts.append(i)
      lookFor = 'end'
    elif '@doc:end' in line:
      if lookFor != 'end':
        assert False
      block_ends.append(i)
      lookFor = 'begin'
      
  # Verify matched pairs of @doc:begin and @doc:end with no overlaps
  if len(block_starts) != len(block_ends):
    raise Exception('Block starts and ends mismatch. Make sure every @doc:begin has a matching @doc:end') 
  for i in range(len(block_starts)):
    assert block_starts[i] < block_ends[i]
    
  for i in range(1, len(block_starts)):
    assert block_starts[i] > block_ends[i-1]
    
  block_boundaries = zip(block_starts, block_ends)
  # Get the doc block
  for i, (start, end) in enumerate(block_boundaries):
    block = getBlock(lines[start+1:end])
    name = block['name']
    blocks[(filename, name)] = block
    
  return blocks
  
def getDocPlaceHolders(filename):
  """Get all the doc place holders in a Python source file
  
  The format of a doc reference is: "@doc:place_holder(Filename.XXX)" where
  'Filename' stands for the name of the C++ header file and 'XXX' stands for
  the doc block ID (usually the method name).
  
  Return a dict of { (filename, id):[(line #, indent), ..., [(line #, indent)],...}
  
  Note that the stored line # (i) is the line number in the source Python
  file and marls the location of the place holder so there is no need to
  search for it again when its time to replace it.
  """
  result = {}
  for i, line in enumerate(open(filename).readlines()):
    # Update the global last class whenever encountering a class definition
    # Note that the classes are prepended, which means the class definitionss
    # are stored in reverse order. This is useful because the scanning needs
    # to find the last class before a property definition
    match = classRegex.match(line)
    if match:
      classes.insert(0, (i, match.groups()[0]))
      
    # Iterate over the two kinds of place holders. The 'skip'
    # is the length of the place holder (e.g. len('@doc:place_holder(') == 18)
    if '.description' in line:
      print
    for token, skip in \
      (('@doc:place_holder(', 18),  
       ('@property:place_holder(', 23)):    
      start = line.find(token)
      if start == -1:
        continue
    
      indent = start # Keep the indentation of the placeholder
      start += skip 
      end = line.index(')', start)
      blockID = line[start:end].strip()
      try:
        inputFile, id = blockID.split('.')
      except:
        raise Exception('Unable to parse block identifier: "%s". Are you missing a dot?' % blockID)  
      
      key = (inputFile, id)
      if key in result:
        result[key].append((i, indent))
      else:
        result[key] = [(i, indent)]
    
  return result
    
def generatePythonComment(d, indent):
  """Generate a Python comment text from a doc block
  
  Make sure to indent the comment text so it aligns nicely based on
  the original location of the place_holder tag and also make sure that long
  lines that wrap take the indentation into account.  
  """
  whitespace = ' ' * indent
  comment = ''
  assert 'summary' in d
  summary = d['summary'].replace('\n', '\n' + whitespace)
  comment += whitespace + summary + '\n\n'
  if 'arguments' in d:
    arguments = d['arguments']
    if isinstance(arguments, list):
      comment += whitespace + 'Arguments:\n'
      for x in arguments:
        k, v = x.items()[0]
        # Give arguments two extra spaces of indentation
        v = v.replace('\n', '\n' + '    ' + whitespace)
        comment += whitespace + '  %s: \n' % k
        comment += whitespace + '    %s\n' % v
  
  if 'return' in d:
    ret = d['return'].replace('\n', '\n  ' + whitespace)
    comment += whitespace + 'Return:\n'
    comment += whitespace + '  %s\n' % ret
  
  comment += '\n'
  return comment

# Compile regexs only once

# A regex to find the block ID of a property place holder
propRegex = re.compile('(.*)(@property:place_holder\([^\)]+\))(.*)')

# A regex to find the class name of a class definition
classRegex = re.compile('^class (.+)(\(.*\)):')

# The classes list contains pairs of line numbers in the Python input file
# and class names that are defined in these lines.
# This is necessary when documenting properties to figure out
# to what class they belong to.
classes = []

def generatePropertyDoc(d, line, access):
  """Embeds the d['return'] in the provided line.
  
  It replaces the @property:place_holder(XXX).
  Also add 'read-only' or 'read-write' appropriately 
  """
  assert 'return' in d
  
  match = propRegex.match(line)
  assert match is not None
  pre = match.groups()[0]
  post = match.groups()[2]
  
  # Replace single quotes with escaped quotes
  text = d['return'].replace("'", r"\'")
  return '%s%s [%s]%s\n' % (pre, text, access, post)
    
def getPropertyAccess(lines, index, installDir):
  """Figure out if the property is read-only, write-only or read-write
  
  """
  # Try to parse the line of the place holder or the previous lines becuase
  # sometimes the 'doc' argument is placed on its own line
  originalIndex = index
  propName = lines[index].split(' = property(')[0]
  while propName == lines[index]:
    index -= 1
    if index < 0:
      raise Exception('@property:place_holder without a property on line: %d' %
                      originalIndex)
    propName = lines[index].split(' = property(')[0]
        
  propName = propName.strip()
  for i, className in classes:
    if i < index:
      lastClass = className
      break
    
  if lastClass is None:
    raise Exception('There is no class definition before property: ' + propName)
  
  try:
    sys.path = [langPyDir, installDir] + sys.path
    cmd = 'from engine import %s; prop = %s.%s'  % (className, className, propName)
    exec(cmd)
  except:
    print 'Documentor failed!!!!'
    print 'Command:', cmd
    print 'Unable to import __init__.py. Bailing out... :-('
    print 'sys.path'
    print '--------'
    print '\n'.join(sys.path)
    sys.exit()
    
  finally:
    sys.path = sys.path[2:]
  
  if not prop:
    raise Exception('Unable get property: %s.%s' % (className, propName))
  # Check if the property has fget, fset or both
  if prop.fget and prop.fset:
    return 'read-write'
  elif prop.fget:
    return 'read-only'
  elif prop.fset:
    return 'write-only'
  else:
    raise Exception('Property %s.%s has no getter and no setter' %
                    (className, propName))
  
def generateDocumentedFile(inputFile, outputFile, docPlaceHolders, docBlocks):
  """Generate a documented Python file from a source file with docPlaceHolders"""
  
  # This is really the site-packages dir, Assumes the output file is nupic2/engine/__init__.py
  installDir = os.path.abspath(os.path.dirname(outputFile) + '/../..')
  
  out = ''
  
  # Convert place holders to a flat list of pairs
  placeHolders = []
  for k, v in docPlaceHolders.items():
    assert type(v) == list
    for p in v:
      placeHolders.append((k, p))
  
  # Sort place holders by location in source file
  placeHolders = sorted(placeHolders, key=lambda x: x[1][0])
  lines = open(inputFile).readlines()
  last = 0 # last source line to be processed 
  for (sourceFile, id), v in placeHolders:
    i = v[0] # The line in the source file of the placeholder
    #print 'last:', last, 'i:', i
    indent = v[1]
    
    # Verify that there are no dangling place holders
    for j, line in enumerate(lines[last:i]):
      if ('@doc:place_holder' in line) or ('@property:place_holder' in line):
        print j
        print line
        raise Exception('Undocumentored place holder: ' + line)

    # Add all the source lines up to the current place holder
    text = ''.join(lines[last:i])
    out += text
    
    last = i + 1
    # Replace the placeholder with proper generated comment
    try:
      block = docBlocks[(os.path.join(baseDir, sourceFile) +  '.hpp', id)]
    except KeyError:
      print 'Documentor Error - Block ID: %s.%s does not exist' % (sourceFile, id)
      sys.exit(1)
      
    line = lines[i]
    property = '@property:place_holder' in line
    if property:
      assert os.path.isdir(installDir)
      genText = generatePropertyDoc(block,
                                    line,
                                    getPropertyAccess(lines, i, installDir))
    else:
      genText = generatePythonComment(block, indent)
    
    out += genText
    
  out += ''.join(lines[last:])
  
  outputDir = os.path.dirname(outputFile)
  if not os.path.isdir(outputDir):
    os.makedirs(outputDir)
  open(outputFile, 'w').write(out)
  
def processFile(inputFile, outputFile):
  """Generate documentation for a Python file"""
  docPlaceHolders = getDocPlaceHolders(inputFile)
  assert docPlaceHolders, 'Source file: %s has no doc blocks' % inputFile
  
  headers = set()
  for v in docPlaceHolders:
    headers.add(v[0])
  
  docBlocks = {}
  for h in headers:
    docBlocks.update(getDocBlocks(h))
  
  inputFile = os.path.abspath(inputFile)
  generateDocumentedFile(inputFile, outputFile, docPlaceHolders, docBlocks)

def generateDocumentation(installDir):
  """Run documentor on lang/py/net/__init__.py
  
  Documentor will create a __init__.py that replaces all
  the documentation place holders with generated documentation blocks
  extracted from the C++ header files (see lang/common/documentor.py for
  more info).
  
  The output file will be generate as nupic.engine.__init__.py in the installDir
  """
  # Prepare all the paths and filenames
  scriptDir = os.path.dirname(__file__)
  trunkDir = os.path.abspath(os.path.join(scriptDir, '../..'))
  inputDir = os.path.join(trunkDir, 'lang/py/engine')
  pv = '%d.%d' % sys.version_info[:2]
  outputDir = os.path.join(installDir, 'lib/python%s/site-packages/nupic/engine' % pv)
  inputFile = os.path.join(inputDir, '__init__.py')
  outputFile = os.path.join(outputDir, '__init__.py')
  
  # Clean previous output file if exists.
  #if os.path.isfile(outputFile):
  #  os.remove(outputFile)

  processFile(inputFile, outputFile)
  
  # Verify the output file was created
  if not os.path.isfile(outputFile):
    raise Exception('Output file: %s was not generated from source file: %s' %
                    (inputFile, outputFile))
  
def test():
  outputFile = '../py/engine/gen.__init__.py'
  processFile('../py/engine/__init__.py', outputFile)
  print open(outputFile).read()
  
def main():
  if len(sys.argv) != 2:
    print "usage: %s install-dir" % sys.argv[0]
    print sys.argv
    sys.exit(1)  
  
  installDir = os.path.abspath(sys.argv[1])
  assert os.path.isdir(installDir)
  generateDocumentation(installDir)
  
if __name__=='__main__':
  main()
  #test()

