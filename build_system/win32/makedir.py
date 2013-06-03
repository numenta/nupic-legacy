import os
import sys
if len(sys.argv) != 2:
    for i in sys.argv:
        print "argument: '%s'" % i
    raise Exception("makedir.py takes a single argument")
dir = sys.argv[1]
if os.path.isdir(dir):
    print "Directory '%s' already exists\r\n" % dir
else:
    os.makedirs(dir)
    print "Created %s\r\n" % dir


