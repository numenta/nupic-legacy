#!/bin/bash
RM="rm -rvf"
TMP=/tmp
DAYS=2
for f in testoutput archive-rename external.
do
  find $TMP -name $f.\* -type d -mtime +$DAYS  | xargs $RM
done

# testit_dir may be read only
for f in testit_dir
do
  find $TMP -name $f.\* -type d -mtime +$DAYS  | xargs chmod -R ugo+w
  find $TMP -name $f.\* -type d -mtime +$DAYS  | xargs $RM
done

find ~buildaccount/autobuild/builds  -name build.\* -maxdepth 1 -mtime +$DAYS  | xargs $RM
find ~buildaccount/autobuild/installs  -name install\* -maxdepth 1 -mtime +$DAYS | xargs $RM
find ~buildaccount/autobuild/releases  -name r\* -maxdepth 1 -mtime +$DAYS  | xargs $RM
