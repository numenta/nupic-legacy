#!/bin/sh
for i in *.cpp
do
  echo compiling $i
#   if [ "`uname`" = "Linux" -a "`uname -i`" = "x86_64" ] ; then
# hack for darwin64
  if [ "1" = "1" ] ; then
      echo building for 64-bit architecture
      g++ -fPIC -fvisibility=hidden -I../include -c $i
  else
      echo building for 32-bit architecture
      g++ -m32 -fPIC -fvisibility=hidden -I../include -c $i
  fi
      
done
ar cr libyaml.a *.o
ranlib libyaml.a
