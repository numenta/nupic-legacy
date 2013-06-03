import utils
import os
import logging
import sys
import time

# Maintain the ability to do everything via subversion commands for now
usingPysvn = True
try:
  import pysvn
except:
  usingPysvn = False

log = logging.getLogger("svn")
baseurl = "https://neocortex.numenta.com/svn/Numenta/"

def initlog(verbose = False) :
  """Perform basic log initialization. Used by
  calling modules that don't use the logging module themselves"""
  if verbose:
    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout, 
                        format="%(levelname)-7s %(message)s")
    logging.getLogger('').setLevel(logging.DEBUG)
  else:
    logging.basicConfig(level=logging.INFO, stream=sys.stdout, 
                        format="%(levelname)-7s %(message)s")
    logging.getLogger('').setLevel(logging.INFO)

# pysvn requires that we explicitly decide whether to trust
# a server. This callback function always says yes
def _ssl_server_trust_prompt(trust_dict):
  # return values mean:
  # 1. use a username and password
  # 2. accepted failures allowed
  # 3. don't save the certificate
  return (True, 0, False)

def checkout(dir, repo="trunk", revision="HEAD", incremental=False, keepLocalMods=False):
  """
  Check out a repository. 
  Makes sure that the disk version is completely in sync. 
  @param repo The name of the respository. Appended to https://neocortex.numenta.com/svn/Numenta
  @param revision Integer revision number or "HEAD"
  @param incremental If True, the directory must exist and must be a checkout
         of the same repo (though possibly at a different revision and with local mods)
  @param keepLocalMods If True, local modifications are kept, that is, anything that shows
         up as "M" or "S" with "svn status". But the repository is updated to the specified 
         version. If keepLocalMods is True, incremental must be true. 
  """

  log.info("checkout: checking out repo '%s' at revision '%s' incremental: %s keepLocalMods: %s", 
           repo, revision, incremental, keepLocalMods)
  if keepLocalMods == True and incremental == False:
    log.error("checkout: request to keep local modifications with a non-incremental checkout")
    raise Exception()

  if not usingPysvn:
    checkoutNoPysvn(dir, 
                    repo=repo,
                    revision=revision,
                    incremental=incremental, 
                    keepLocalMods=keepLocalMods)
    return

  url = baseurl + repo

  client = pysvn.Client()
  client.callback_ssl_server_trust_prompt = _ssl_server_trust_prompt
  # convert revision specification to pysvn Revision
  if type(revision) == type(str()):
    if revision == "HEAD":
      svnrev = pysvn.Revision(pysvn.opt_revision_kind.head)
    else:
      # if revision does not represent an int, the conversion will throw an exception
      svnrev = pysvn.Revision(pysvn.opt_revision_kind.number, int(revision))
  elif type(revision) == type(5):
      svnrev = pysvn.Revision(pysvn.opt_revision_kind.number, revision)
  else:
    log.error("checkout: bad type for revision specification: %s", type(revision))
    raise Exception()

  if incremental:
    if not os.path.exists(dir) or not os.path.isdir(dir):
      log.error("checkout: %s does not exist or is not a directory", dir);
      raise Exception()
    try:
      info = client.info(dir)
    except:
      log.error("checkout: unable to get svn info from directory %s", dir)
      raise Exception()
    if info["url"] != url:
      log.error("checkout: subversion url does not match for directory %s", dir)
      log.error("checkout: expected: %s", url)
      log.error("checkout: got: %s", info["url"])
      raise Exception()

    clean(dir, doCleanup=(not keepLocalMods))
    log.info("Updating tree to revision %s", revision)
    client.update(dir, recurse=True, revision=svnrev, ignore_externals=True)
    if not keepLocalMods:
      try:
        # Throws an exception if it is not completely clean
        verify(dir)
      except:
        log.warn("Verification of repository failed. Trying one more clean/update cycle")
        clean(dir, doCleanup=True)
        log.info("Updating tree to revision %s", revision)
        client.update(dir, recurse=True, revision=svnrev, ignore_externals=True)
        verify(dir)
        
        
  else:
    # not incremental
    if os.path.exists(dir):
      log.error("checkout: directory %s already exists. Full checkout requested", dir)
      raise Exception()
    log.info("Doing fresh checkout of repo '%s' into directory '%s'", 
             repo, revision)
    client.checkout(url, dir, recurse=True, revision=svnrev, ignore_externals=True)



def clean(dir,  doCleanup=True):
  """Find all entries that are not supposed to be there and delete them.
  If doCleanup == True, actually does the cleanup, otherwise reports what
  is found. 
  End result should be that "svn status --no-ignore" shows missing files but
  no extra files."""


  if doCleanup:
    log.info("Cleaning up subversion repo in dir '%s'", dir)
  else:
    log.info("Reporting bad files in dir '%s'", dir)

  if not usingPysvn:
    cleanNoPysvn(dir,  doCleanup)
    return

  client = pysvn.Client()
  client.callback_ssl_server_trust_prompt = _ssl_server_trust_prompt
  statusList = client.status(dir, recurse=True, get_all=True, update=False,ignore=False,ignore_externals=True)

  for item in statusList:
    if not item.is_versioned:
      # don't both notifying about completely routine files
      if (not item.path.endswith(".pyc") and 
          not item.path.endswith("Makefile.am") and 
          not item.path.endswith(".vcproj") and 
          not item.path.endswith("project.manifest") and
          not item.path.endswith("Makefile.in")):
        log.info("clean: Found unversioned item '%s'", item.path)
      if doCleanup:
        utils.remove(item.path)
      continue
    if item.is_locked:
      log.error("clean: Encountered locked item '%s'. Cleanup subversion tree manually", item.path)
      raise Exception()
    if item.is_switched:
      log.info("clean: Found switched item '%s'", item.path)
      if doCleanup:
        utils.remove(item.path)
      continue
    # Look carefully at item status. 
    # Text status only -- ignore property status for now
    status = item.text_status
    if status == pysvn.wc_status_kind.normal:
      # this is what we want. Needs no special treatment
      pass
    elif (status == pysvn.wc_status_kind.none or 
          status == pysvn.wc_status_kind.unversioned or 
          status == pysvn.wc_status_kind.external):
      # should have handled unversioned files above
      log.error("clean: Encountered object '%s' with unexpected status '%s'", item.path, status)
      raise Exception()
    elif (status == pysvn.wc_status_kind.added or
          status == pysvn.wc_status_kind.deleted or
          status == pysvn.wc_status_kind.replaced or
          status == pysvn.wc_status_kind.modified or
          status == pysvn.wc_status_kind.merged or 
          status == pysvn.wc_status_kind.conflicted or
          status == pysvn.wc_status_kind.obstructed or
          status == pysvn.wc_status_kind.ignored):
      log.info("clean: Found modified item '%s' with status '%s'", item.path, status)
      if doCleanup:
        utils.remove(item.path)
    elif (status == pysvn.wc_status_kind.missing or
          status == pysvn.wc_status_kind.incomplete):
      log.info("svnUPdate: Found missing/incomplete item '%s'", item.path)
    else:
      log.error("clean: unknown status %s for item %s", status, item.path)
      raise Exception()


def verify(dir):
  """Make sure that a repo is completely clean, with everything up to date
  Throws an exception if there is anything wrong"""

  if not usingPysvn:
    verifyNoPysvn(dir)
    return

  client = pysvn.Client()
  client.callback_ssl_server_trust_prompt = _ssl_server_trust_prompt
  statusList = client.status(dir, recurse=True, get_all=True, update=False,ignore=False,ignore_externals=True)

  for item in statusList:
    if (not item.is_versioned):
      log.error("verify: Found unversioned item '%s'", item.path)
      raise Exception()
    if item.is_locked:
      log.error("verify: Encountered locked item '%s'. Clean subversion tree manually", item.path)
      raise Exception()
    if item.is_switched:
      log.info("verify: Found switched item '%s'", item.path)
      raise Exception()
    
    status = item.text_status
    if status != pysvn.wc_status_kind.normal:
      log.error("verify: Encountered object '%s' with unexpepcted status '%s'", item.path, status)

            

def getRevision(dir):
  if not usingPysvn:
    return getRevisionNoPysvn(dir)
  
  client = pysvn.Client()
  client.callback_ssl_server_trust_prompt = _ssl_server_trust_prompt
  info = client.info(dir)
  rev = int(info.revision.number)
  return rev

def getHeadRevision(dir):
  if not usingPysvn:
    return getHeadRevisionNoPysvn(dir)
  
  client = pysvn.Client()
  client.callback_ssl_server_trust_prompt = _ssl_server_trust_prompt
  info = client.info(dir)
  url = info.url
  info = client.info2(url, pysvn.Revision(pysvn.opt_revision_kind.head), recurse=False)
  rev = int(info[0][1].last_changed_rev.number)
  return rev


def getRevisionNoPysvn(dir):
  revisionnum = utils.backquote("svn info %s | grep Revision: | awk '{print $2}'" % dir)
  return int(revisionnum)

def getHeadRevisionNoPysvn(dir):
  revisionnum = utils.backquote("svn info -r HEAD %s | grep 'Last Changed Rev': | awk '{print $4}'" % dir)
  return int(revisionnum)

def verifyNoPysvn(dir):
  output = utils.runCommandCaptureOutput("svn status --no-ignore %s" % dir) 
  if output is None or len(output) > 0 :
    if output == None:
      log.error("svn status output is 'None'")
    else:
      log.error("svn status output is not clean")
      for l in output:
        log.error("  status output: %s" % l.strip())
      raise Exception()



def checkoutNoPysvn(dir, repo="trunk", revision="HEAD", incremental=False, keepLocalMods=False):
  url = baseurl + repo

  log.info("checkoutNoPysvn: checking out repo '%s' at revision '%s' incremental: %s keepLocalMods: %s", 
           repo, revision, incremental, keepLocalMods)

  if incremental:
    if not os.path.exists(dir) or not os.path.isdir(dir):
      log.error("checkout: %s does not exist or is not a directory", dir);
      raise Exception()
    try:
      actualUrl = utils.backquote("svn info %s | grep URL | awk '{print $2}'" % dir)
    except:
      log.error("checkout: unable to get svn info from directory %s", dir)
      raise Exception()
    if actualUrl != url:
      log.error("checkout: subversion url does not match for directory %s", dir)
      log.error("checkout: expected: %s", url)
      log.error("checkout: got: %s", actualUrl)
      raise Exception()

    clean(dir, doCleanup=(not keepLocalMods))
    log.info("Updating tree to revision %s", revision)
    utils.runCommand("svn update -r %s %s" % (revision, dir))
    if not keepLocalMods:
      try:
        # Throws an exception if it is not completely clean
        verify(dir)
      except:
        log.warn("Verification of repository failed. Trying one more clean/update cycle")
        clean(dir, doCleanup=True)
        log.info("Updating tree to revision %s", revision)
        utils.runCommand("svn update -r %s %s" % (revision, dir))
        verify(dir)
  else:
    # not incremental
    if os.path.exists(dir):
      log.error("checkout: directory %s already exists. Full checkout requested", dir)
      raise Exception()
    log.info("Doing fresh checkout of repo '%s' into directory '%s'", 
             repo, revision)
    utils.runCommand("svn checkout -r %s %s %s" % (revision, url, dir))
  

def cleanNoPysvn(dir,  doCleanup=True):
  if doCleanup == False:
    utils.runCommand("svn status --no-ignore %s" % dir)
  else:
    # Delete everythiung svn doesn't know about *except* for the top level directory, since svn can 
    # reports the top level directory as "!" (missing") if a sub-directory is missing. 
    # Use the xml format to avoid problems with spaces in filenames
    utils.runCommand("svn status --no-ignore --xml %s | grep -A1 entry | grep path= | awk -F= '{print $2}' | sed 's/>//' | grep -v \\\"%s\\\" | xargs rm -rvf" % (dir, dir), logOutputOnlyOnFailure=False)


def getLog(dir, rev1, rev2):
  
  if not usingPysvn:
    return getLogNoPysvn(dir, rev1, rev2)
    
  client = pysvn.Client()
  client.callback_ssl_server_trust_prompt = _ssl_server_trust_prompt
  logentries = client.log(dir, 
        pysvn.Revision(pysvn.opt_revision_kind.number, int(rev1)), 
        pysvn.Revision(pysvn.opt_revision_kind.number, int(rev2)))

  log = ""
  for entry in logentries:
    log += "-----------------------------------------------------------\n"
    log += "r%-10d | %-10s | %s\n" % (entry["revision"].number,  entry["author"], 
                                      time.asctime(time.localtime(entry["date"])))
    log += "%s\n" % entry["message"].strip()

  log += "-----------------------------------------------------------"
  return log

def getLogNoPysvn(dir, rev1, rev2):
  loglines = utils.runCommandCaptureOutput("svn log -r %d:%d %s" % (rev1, rev2, dir))
  log = ""
  for line in loglines:
    log += line
  return log

