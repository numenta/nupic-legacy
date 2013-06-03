#!/usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have purchased from
# Numenta, Inc. a separate commercial license for this software code, the
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

# Clean up autobuilds on the data server
import os
import time
import sys

autobuildRoot="/Volumes/big/www/autobuild"
# directories on the exception list are not touched
exceptionList = ["r8101","r8500","r9726","r11234","r12610","r14634","r17595","r18186" #public releases \
                 ,"r6320","r7596","r9466","r11234","r13510","r16727","r18541","r19578","r20377","r21240" #npp releases \
                 , "r21002","r20502","r20001","r19500","r19000","r18500","r18007","r17504","r17001" #500th build \
                 , "r16500","r16002","r15502","r15002","r14502","r14000","r13500","r13322" #500th build \
                 , "r13004","r12504","r12000","r11400" #500th build \
                 ]
# only delete files older than the age cutoff -- 14 days
ageCutoff = 3600*24*14


def okToDelete(dir, filename):
    if not (f.endswith(".tgz") or
            f.endswith(".exe") or 
            f.endswith(".dmg") or
            f.endswith(".zip")):
        # print "Rejecting %s because it is the wrong type" % filename
        return False

    stat = os.stat(os.path.join(dir, filename))
    if time.time() - stat.st_mtime < ageCutoff:
        # print "Rejecting %s because it is too new" % filename
        return False

    return True



if __name__ == "__main__":

    os.chdir(autobuildRoot)
    doit = False
    if len(sys.argv) == 2 and sys.argv[1] == "-reallyDelete":
        doit = True
    print exceptionList

    for candidate in os.listdir("."):
        if not candidate.startswith("r"):
            continue
        if candidate in exceptionList:
            print "Skipping %s because it is in the exception list" % candidate

        files = os.listdir(candidate)
        files_to_delete = [f for f in files if okToDelete(candidate, f)]

        if not doit:
            if len(files_to_delete) > 0:
                print "Would delete %d: %s" % (len(files_to_delete), files_to_delete)
        else:
            for file in files_to_delete:
                print "Removing %s" % file
                os.remove(os.path.join(candidate, file))

