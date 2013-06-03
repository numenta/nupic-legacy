from __future__ import with_statement
import os
import sys

python_version = '%d.%d' % sys.version_info[:2]

def main():
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
    
  script_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
  package_dir = os.path.join(script_dir, 'install/lib/python%s/site-packages' %
                             python_version)
  vita_dir = os.path.join(package_dir, 'vitamind')
  ffmpeg_dir = os.path.join(script_dir, 'install/lib/ffmpeg')
  opencv_dir = os.path.join(package_dir, 'opencv')
  videoclip_dir = os.path.join(vita_dir, 'videoClipLib')
  os.path.join
  os.environ['PATH'] += [opencv_dir, ffmpeg_dir, videoclip_dir]
  os.environ['PYTHONPATH'] += [vita_dir]

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

  import PeopleTrackingDemo
  PeopleTrackingDemo.main()

if __name__=='__main__':
  argv = sys.argv[1:]
  with open('log.txt', 'w', buffering=False) as f:
    sys.stdout = f
    if '--log' in argv:
      sys.argv.remove('--log')

    main()
