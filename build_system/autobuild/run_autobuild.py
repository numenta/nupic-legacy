#!/usr/bin/env python

# Invokes autobuild.py after updating to make sure we have the latest version.
# Intended to be run from a cron script
# run_autbuild.py lives in build_sytem/autobuild
# svn and pythnon (the correct version) must be in $PATH
import sys
import os

mydir = sys.path[0]
buildsystemdir = os.path.abspath(os.path.join(mydir, os.pardir))
os.system("svn update %s" % buildsystemdir)
os.system("%s %s" % (sys.executable, os.path.join(mydir, "autobuild.py")))

