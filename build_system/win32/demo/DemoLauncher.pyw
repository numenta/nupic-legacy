from __future__ import with_statement
import os
import sys

python_version = '%d.%d' % sys.version_info[:2]
def main(argv):
  python_path = os.path.abspath('install\lib\python%s\site-packages' %
                                python_version)

  try:
    PYTHONPATH = os.environ['PYTHONPATH'].split(os.pathsep)
    print 'os.environ[\'PYTHONPATH\']'
    print '------------------------'
    print os.environ['PYTHONPATH']
    print    
  except KeyError:
    PYTHONPATH = []
    
  os.environ['NTA_ROOTDIR'] = os.path.abspath('install')
  sys.path.insert(1, os.path.abspath('install\lib\python%s\site-packages' %
                                     python_version))
  
  print 'sys.path (before removing PYTHONPATH)'
  print '-------------------------------------'
  print '\n'.join(sys.path)
  print
  
  sys.path = [p for p in sys.path  if p not in PYTHONPATH]
  try:
    del os.environ['PYTHONPATH']
  except KeyError:
    pass

  print 'sys.path (after removing PYTHONPATH)'
  print '-------------------------------------'
  print '\n'.join(sys.path)
  print

  assert os.path.exists(sys.path[1])
  assert os.path.exists(sys.path[1] + r'\enthought\__init__.py')
  
  import Demo
  Demo.main(argv=argv, demoMode=True)

if __name__=='__main__':
  argv = sys.argv[1:]
  if '--log' in argv:
    argv.remove('--log')
    with open('log.txt', 'w') as f:
      sys.stdout = f
      main(argv)
  else:
    main(argv)    
