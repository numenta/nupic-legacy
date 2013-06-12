#!/usr/bin/env python2

import sys, os, subprocess
from xml.etree.ElementTree import parse
import cPickle
import Tkinter
import time
import math

class User(object):
  def __init__(self):
    pass

class UserDB(object):
  def __init__(self):
    self.users = {} # Map of shortname to user object.
  def update(self, shortname):
    if not shortname in self.users:
      self.users[shortname] = User()
    
class Revision(object):
  def __init__(self, revision, author, date, msg):
    self.revision = revision
    self.author = author
    self.date = date
    self.msg = msg
  def __str__(self):
    return "Revision: %s\n  Author: %s\n    Date: %s\n Message: %s" % \
      (self.revision, self.author, self.date, self.msg)
  def __repr__(self):
    return "Revision: %s\n  Author: %s\n    Date: %s\n Message: %s" % \
      (self.revision, self.author, self.date, self.msg)

def parseRevision(etreeObj):
  revision = None
  tags = {}
 
  assert etreeObj.tag == "logentry"
 
  if "revision" in etreeObj.keys():
    revision = etreeObj.get("revision")

  for sub in etreeObj:
    tags[sub.tag] = sub.text

  author = tags.get("author", None)
  date = tags.get("date", None)
  msg = tags.get("msg", None)
  return Revision(revision, author, date, msg)
  

def ensureList(x):
  if not hasattr(x, "__iter__"): return [x]
  else: return list(x)

def svnxml(cmd, args=[]):
  cmd = [svn, cmd, "--xml"] + ensureList(args)
  p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
  tree = parse(p.stdout)
  retCode = p.wait()
  if retCode != 0: raise RuntimeError("Failed: %d." % retCode)
  return tree

def getCurrentRevision():
  cmd = "info"
  args = ["-r", "HEAD"]
  tree = svnxml(cmd, args)
  revision = None
  for entry in tree.getroot():
    if entry.tag == "entry":
      if "revision" in entry.keys():
        assert revision is None
        revision = entry.get("revision")
  assert revision is not None
  revision = int(revision) # Read the revision string as a number.
  return revision

def getEntries(lastRevision, revision):
  cmd = "log"
  args = ["-r", "%s:%s" % (lastRevision, revision)]
  tree = svnxml(cmd, args)
  revisions = [parseRevision(entry) for entry in tree.getroot()]
  return revisions

class State(object):
  def __init__(self):
    self.lastRevision = None
    self.lastUpdate = []
    self.users = UserDB()

  def update(self):
    revision = getCurrentRevision()
    if self.lastRevision is None:
      self.lastRevision = revision
  
    if revision != self.lastRevision:
      entries = getEntries(self.lastRevision, revision)
  
      for entry in entries:
        self.users.update(entry.author)
  
      self.lastUpdate = entries
  
      self.lastRevision = revision

      return entries
    else:
      return []

def update(save):
  entries = state.update()
  for entry in entries:
    print entry

class WatchGUI(object):
  def __init__(self, state, save):
    self.state = state
    self.save = save
    self.gui = None
    self.text = None
    self.alpha = -1.0
    self.lastTime = 0
    self.lastCheck = 0
    self.title = ""

  def createWidgets(self, master, *args, **keywds):
    assert self.gui is None
    try:
      self.title = master.title()
    except:
      pass
    frame = Tkinter.Frame(master=master)
    scrollbar = Tkinter.Scrollbar(master=frame)
    scrollbar.pack(side=Tkinter.RIGHT, fill=Tkinter.Y)
    text = Tkinter.Text(master=frame, width=80, height=16, wrap=Tkinter.WORD)
    text.pack(side=Tkinter.LEFT, fill=Tkinter.BOTH)
    text.config(state=Tkinter.DISABLED)
    text.config(yscrollcommand=scrollbar.set)
    text.bind("<Button-1>", self.click)
    text.bind("<Enter>", self.click)
    scrollbar.config(command=text.yview)
    frame.pack()

    self.gui = master
    self.text = text

  def start(self):
    self.timeout()

  def click(self, *args):
    self.setAlpha(1.0)
    self.gui.update()

    entries = self.state.update()
    if entries:
      self.setEntries(entries)
    # Make readable.
    self.setAlpha(1.0)

  def setAlpha(self, alpha):
    if alpha != self.alpha:
      self.alpha = alpha
      # Blend from light yellow to light blue.
      red = 1.0 * alpha + 0.8 * (1.0 - alpha)
      green = 1.0 * alpha + 0.8 * (1.0 - alpha)
      blue = 1.0 * (1.0 - alpha) + 0.8 * (alpha)
      color = "#%02x%02x%02x" % \
        (int(255.0 * red), int(255.0 * green), int(255.0 * blue))

      self.text.config(bg=color)
      # self.text.update()

      minAlpha = 0.2
      finalAlpha = alpha * (1.0 - minAlpha) + minAlpha
      try:
        self.gui.attributes("-alpha", finalAlpha)
      except: # Ignore fancy features.
        pass

  def setEntries(self, entries):
    if self.text is not None: 
      self.text.config(state=Tkinter.NORMAL)
      self.text.delete("1.0", Tkinter.END)
      for entry in entries:
        self.text.insert(Tkinter.END, str(entry) + "\n")
      uptime = time.time() - launchTime
      days = uptime / (24.0 * 60.0 * 60.0)
      hours = (days - int(days)) * 24.0
      minutes = (hours - int(hours)) * 60.0
      seconds = (minutes - int(minutes)) * 60.0
      self.text.insert(
          Tkinter.END,
          "Uptime is %dd %dh %dm %.1fs." % 
          (int(days), int(hours), int(minutes), seconds)
        )
         
      self.text.config(state=Tkinter.DISABLED)

    if entries:
      titleString = "Revision %s" % entries[-1].revision
      if self.title: titleString = self.title + ": " + titleString
      self.gui.title(titleString)
    # State probably changed, save state.
    if self.save is not None:
      try:
        cPickle.dump(state, file(self.save, "wb"), 2)
      except Exception, e:
        print >>sys.stderr, "Failed to save:", e

    

  def timeout(self, *args):
    alpha = self.alpha
    curTime = time.time()
    elapsedTime = curTime - self.lastTime
  
    entries = [] 

    # Only check every minute.
    if (curTime - self.lastCheck) > 60.0:
      entries = self.state.update()
      self.lastCheck = curTime

    if entries:
      self.setEntries(entries)

      alpha = 1.0

    else:
      fadeRate = 2.0
      fade = math.exp(-fadeRate * (elapsedTime / 60.0))
      # Slowly fade away.
      alpha *= fade
      
    if self.gui is not None:
      self.setAlpha(alpha)

      # Set up the next update.
      seconds = 2.0
      self.gui.after(int(seconds * 1000), self.timeout)

    self.lastTime = curTime

  


if __name__ == "__main__":
  launchTime = time.time()

  import getopt

  setopts = {
      "svn": "svn",
      "save": ".watchsvn.pkl"
    }

  opts, args = getopt.getopt(sys.argv[1:], "g", 
      ["--" + opt + "=" for opt in setopts.keys()] + [])

  if len(args) == 1:
    os.chdir(args[0])
  elif len(args) > 1:
    raise RuntimeError("More than one path argument specified.")

  gui = False

  for opt in opts:
    if opt[0] in setopts:
      setopts[opt[0]] = opt[1]
    elif opt[0] == "-g":
      gui = True
    else:
      raise RuntimeError("Unexpected option: " + opt[0])
 
  locals().update(setopts) 

  state = State()
 
  if save is not None:
    try:
      state = cPickle.load(file(save, "rb"))
    except Exception, e:
      print >>sys.stderr, "No state:", e

  if gui:
    root = Tkinter.Tk()

    root.title(os.getcwd())
    # Try to set the title path on the Mac to quick get to the relevant dir.
    try:
      root.attributes("-titlepath", os.getcwd())
    except:
      try:
        root.attributes(titlepath=os.getcwd())
      except:
        pass

    watcher = WatchGUI(state, save)
    watcher.createWidgets(root)
    watcher.start()
    root.mainloop()

  else:
    update(state)

  if save is not None:
    cPickle.dump(state, file(save, "wb"), 2)

  




