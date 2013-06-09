#!/usr/bin/env python2

def flip(input, output):
  lines = input.readlines()
  for line in lines:
    if line.startswith("## "): print >>output, line[3:].rstrip()
    elif line.startswith("#"): print >>output, line.rstrip()
    else: print >>output, "##", line.rstrip()

if __name__ == "__main__":
  import sys
  input = file(sys.argv[1])
  output = file(sys.argv[2], "w")
  flip(input, output)

