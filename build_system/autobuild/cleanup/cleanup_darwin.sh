#!/bin/bash
RM="rm -rvf"
TMP=/tmp
DAYS=3

# builds/installs are in /autobuild/fs{1,2} on darwin86
#find ~buildaccount/autobuild/builds  -name build.\* -maxdepth 1 -mtime +$DAYS  | xargs $RM
#find ~buildaccount/autobuild/installs  -name install\* -maxdepth 1 -mtime +$DAYS | xargs $RM
find ~buildaccount/autobuild/releases  -name r\* -maxdepth 1 -mtime +$DAYS  | xargs $RM

# on darwin87 most other files are in /autobuild/fs{1,2} not in /tmp so don't clean them up
