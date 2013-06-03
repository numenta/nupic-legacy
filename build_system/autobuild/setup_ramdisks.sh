#!/bin/sh
#
#
# Set up ramdisks on darwin86 mac pro system
#

if [ "$1" != "-go" ] ;
then
   echo "Output of hdiutil info"
   hdiutil info
   echo
   echo "If disk2 and disk3 correspond to ramdisks, or don't exist, "
   echo "use the -go option to proceed. "
   exit 1
fi


NSECTORS=4000000
root=/autobuild

if [ ! -d $root ] ; then
  echo "Root directory $root does not exist. Please create it"
  exit 1
fi

echo "Unmounting ramdisks"
for FS in fs1 fs2
do
  if [ ! -d $root/$FS ] ; then
    echo "Directory $root/$FS does not exist"
    exit 1
  fi
  umount -f $root/$FS
done

echo "Destroying ramdisks"
hdiutil detach /dev/disk2
hdiutil detach /dev/disk3

hdiutil attach -nomount ram://$NSECTORS
disk=$(hdiutil info | tail -1)
disk=${disk:0:10}
if [ "$disk" != "/dev/disk2" ] ; then
  echo "Created disk '$disk' is not /dev/disk2!"
  exit 1
fi

if [ "$2" == "-cleanup" ] ; then
  echo "Done cleaning up. Not creating new filesystems"
  exit 0
fi

hdiutil attach -nomount ram://$NSECTORS
disk=$(hdiutil info | tail -1)
disk=${disk:0:10}
if [ "$disk" != "/dev/disk3" ] ; then
  echo "Created disk '$disk' is not /dev/disk2!"
  exit 1
fi

newfs_hfs /dev/disk2
newfs_hfs /dev/disk3

mount -t hfs -o nobrowse /dev/disk2 /autobuild/fs1
mount -t hfs -o nobrowse /dev/disk3 /autobuild/fs2


