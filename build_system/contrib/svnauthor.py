#!/usr/bin/env python2

import sys
import subprocess
from xml.etree.ElementTree import parse

toCheck = []
args = []

supportedKeys = set(["author"])
for arg in sys.argv[1:]:
  handled = False
  speq = arg.split("=", 1)
  if arg.startswith("--") and (len(speq) > 1) and speq[0][2:] in supportedKeys:
    toCheck.append("%s == '%s'" % (speq[0][2:], speq[1]))
  else:
    args.append(arg)

cmd = ["svn", "log", "--xml"] + args
print " ".join(cmd)
p = subprocess.Popen(cmd, stdout=subprocess.PIPE)

x = parse(p.stdout)

retCode = p.wait()

if retCode != 0: raise RuntimeError("Failed: %d" % retCode)

def checkElement(expr, tag, text):
  x = {tag: text}
  result = False
  try:
    result = eval(expr, {}, x)
  except:
    pass
  return result

nEntries = 0
# Filter by author.
for i, entry in enumerate(x.getroot()):
  keepEntry = False
  for element in entry:
    for check in toCheck:
      keepEntry = keepEntry or checkElement(check, element.tag, element.text)

  if keepEntry:
    nEntries += 1
    print "=== %6d =========================" % i
    if "revision" in element.keys():
      print "Revision :", element.get("revision")
    for key in entry.keys():
      print key, entry.get(key)
    print "-------------------------------------"
    for element in entry:
      print element.tag, ":", element.text


print "=== %6d ============================" % nEntries
      
