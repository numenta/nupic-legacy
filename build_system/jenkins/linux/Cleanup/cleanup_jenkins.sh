#!/bin/bash
RM="rm -rf"
#RM="ls"
DAYS=1
TMP=$HOME/Jenkins/Builds
find $TMP -maxdepth 1 -mtime +$DAYS  | xargs $RM
TMP=/tmp
find $TMP -maxdepth 1 -mtime +$DAYS  | xargs $RM
