#
# The .buildinfo file contains information about builds created by the 
# Numenta automatic build system (autobuild). 
# If we're running under an autobuild, or have previously built into this 
# installation directory, the file will already exist. 
# Otherwise it will not exist and we need to create it. 
# 
import os
import sys
dir = sys.argv[1]
print "Checking for .buildinfo file in '%s'" % dir
file = os.path.join(dir, ".buildinfo")
if not os.path.exists(file):
    if not os.path.exists(dir):
        print "Creating directory %s" % dir
        os.makedirs(dir)
    open(file, "w").write("DEVELOPER BUILD\n")
    print "Created %s" % file
else:
    print "%s already exists. Not creating." % file
