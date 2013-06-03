import os, sys

if sys.platform.startswith('win'):
  print 'This script cannot be run on Windows'
  sys.exit(1)

file_dir = os.path.abspath(os.path.abspath(sys.argv[0]))
trunk_dir = os.path.normpath(os.path.join(os.path.dirname(file_dir), '../..'))

bindings_dir = os.path.join(trunk_dir, 'nta/python/bindings')

for d in ('math', 'algorithms', 'network'):
  os.chdir(os.path.join(bindings_dir, d))
  os.system('. doc.sh')

