#!/bin/bash
# Turn on optimization for runtime and tools library builds.
for file in nta/runtime/Makefile nta/client/comm/Makefile nta/client/object_model/Makefile nta/client/session/Makefile nta/client/utils/Makefile nta/ipc/ipcserial/Makefile nta/ipc/ipcmpi/Makefile
do
  if [ ! -e $file ] ; then
      echo "ERROR: file $file does not exist"
      exit 1
  fi
  cat $file | sed 's/^#am__append_1/am__append_1/' | sed 's/^am__append_2 = -O0/am__append_2 = /' > $file.new
  diff $file  $file.new 2>&1 > /dev/null
  if [ $? == 0 ] ; then
    echo "File $file was not changed"
  else
    cp $file $file.orig
    cp $file.new $file
    echo "Patched $file"
  fi
done
