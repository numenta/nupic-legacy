#!/bin/bash
RM="rm -rvf"
#RM="ls"
TMP=$HOME/Jenkins/Builds
DAYS=7
find $TMP -maxdepth 1 -mtime +$DAYS  | xargs $RM
