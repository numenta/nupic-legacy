#!/usr/bin/python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------

# Warning -- this code is yucky. It is just a quick hack to make it easier to see
# build status.

import cgi
import cgitb
import os
import time
import datetime


def printTable(arch):
  builds_inprogress = status.getBuildsInOrder(os.path.join(statusdir, 'build_%s_inprogress' %arch))
  tests_inprogress = status.getBuildsInOrder(os.path.join(statusdir, 'test_%s_inprogress' %arch))
  acctests_inprogress = status.getBuildsInOrder(os.path.join(statusdir, 'acctest_%s_inprogress' %arch))
  perftests_inprogress = status.getBuildsInOrder(os.path.join(statusdir, 'perftest_%s_inprogress' %arch))
  deploy_inprogress = status.getBuildsInOrder(os.path.join(statusdir, 'upload_%s_inprogress' %arch))
  awstests_inprogress = status.getBuildsInOrder(os.path.join(statusdir, 'awstest_%s_inprogress' %arch))

  builds_done = status.getBuildsInOrder(os.path.join(statusdir, 'build_%s_done' %arch))
  tests_done = status.getBuildsInOrder(os.path.join(statusdir, 'test_%s_done' %arch))
  acctests_done = status.getBuildsInOrder(os.path.join(statusdir, 'acctest_%s_done' %arch))
  perftests_done = status.getBuildsInOrder(os.path.join(statusdir, 'perftest_%s_done' %arch))
  deploy_done = status.getBuildsInOrder(os.path.join(statusdir, 'upload_%s_done' %arch))
  awstests_done = status.getBuildsInOrder(os.path.join(statusdir, 'awstest_%s_done' %arch))

  builds_fail = status.getBuildsInOrder(os.path.join(statusdir, 'build_%s_fail' %arch))
  tests_fail = status.getBuildsInOrder(os.path.join(statusdir, 'test_%s_fail' %arch))
  acctests_fail = status.getBuildsInOrder(os.path.join(statusdir, 'acctest_%s_fail' %arch))
  perftests_fail = status.getBuildsInOrder(os.path.join(statusdir, 'perftest_%s_fail' %arch))
  deploy_fail = status.getBuildsInOrder(os.path.join(statusdir, 'upload_%s_fail' %arch))
  awstests_fail = status.getBuildsInOrder(os.path.join(statusdir, 'awstest_%s_fail' %arch))

  allbuilds = builds_inprogress + builds_done

  nBuilds = min(20, len(allbuilds))

  # Return the first N builds with Pass/Fail status and failure reason
  resultStr = '{ "nupic": [\n'
  for i in xrange(0, nBuilds):
      awstests = ""
      tag = allbuilds[i].rstrip()
      
      # AWS status
      awsStatus = None
      if tag in awstests_done:
        awsStatus = "pass"
        if tag in awstests_fail: awsStatus = "fail"
          
      # standard test status
      standardSstatus = None
      if tag in tests_done:
        standardSstatus = "pass"
        if tag in tests_fail: standardSstatus = "fail"
        
      # Acceptance test status
      acceptanceStatus = None
      if tag in acctests_done:
        acceptanceStatus = "pass"
        if tag in acctests_fail: acceptanceStatus = "fail"

      # Overall status is NA if none of the tests have run
      # PASS if all the tests passed, FAIL if any of the tests failed
      overallStatus = "NA"
      reason = "NA"
      if awsStatus == "pass" and standardSstatus == "pass" and \
        acceptanceStatus == "pass":
        overallStatus = "PASS"

      if awsStatus == "fail":
        overallStatus = "FAIL"
        reason = "AWS Test"

      if standardSstatus == "fail":
        overallStatus = "FAIL"
        reason = "Standard"
      if acceptanceStatus == "fail":
        overallStatus = "FAIL"
        reason = "Acceptance"
      

      statuses_print = {}

      statuses_print['tag'] = tag

      if i>0: resultStr += ",\n"
      resultStr += '["' + statuses_print['tag'] + '",'
      resultStr += '"' + overallStatus + '","' + reason + '"]'

  resultStr +=  "\n]}\n"
  print resultStr


class JenkinsStatus:
  def isEmpty(self, filename):
    file = open(filename)
    lines = file.readlines()
    file.close()
    if len(lines) == 0:
      return True
    else:
      return False

  def isNotEmpty(self, filename):
    file = open(filename)
    lines = file.readlines()
    file.close()
    if len(lines) > 0:
      return True
    else:
      return False

  def isTagInList(self, tag, filename):
    file = open(filename)
    lines = file.readlines()
    file.close()
    if tag in lines:
      return True
    else:
      return False

  def removeTagFromFile(self, tag, filename, tmpfilename):
    file = open(filename)
    tmpfile = open(tmpfilename, 'w')
    lines = file.readlines()
    for line in lines:
      if tag not in line:
        print >> tmpfile, line
    file.close()
    tmpfile.close()

  def getLatestBuild(self, filename):
    file = open(filename)
    lines = file.readlines()
    file.close()
    lastLine = lines[len(lines)-1]
    return lastLine

  def getBuildsInOrder(self, filename):
    file = open(filename)
    lines = file.readlines()
    file.close()
    buildsList = []
    listLen = len(lines)
    while (listLen > 0):
      buildsList.append((lines[listLen-1]).rstrip())
      listLen = listLen - 1
    return buildsList
# Change to get last stable build

  def getLastStableBuild(self,arch):
    builds_done = self.getBuildsInOrder(os.path.join(statusdir, 'build_%s_done' %arch))
    tests_done = self.getBuildsInOrder(os.path.join(statusdir, 'test_%s_done' %arch))
    acctests_done = self.getBuildsInOrder(os.path.join(statusdir, 'acctest_%s_done' %arch))
    perftests_done = self.getBuildsInOrder(os.path.join(statusdir, 'perftest_%s_done' %arch))
    deploy_done = self.getBuildsInOrder(os.path.join(statusdir, 'upload_%s_done' %arch))
    awstests_done = self.getBuildsInOrder(os.path.join(statusdir, 'awstest_%s_done' %arch))

    builds_fail = self.getBuildsInOrder(os.path.join(statusdir, 'build_%s_fail' %arch))
    tests_fail = self.getBuildsInOrder(os.path.join(statusdir, 'test_%s_fail' %arch))
    acctests_fail = self.getBuildsInOrder(os.path.join(statusdir, 'acctest_%s_fail' %arch))
    perftests_fail = self.getBuildsInOrder(os.path.join(statusdir, 'perftest_%s_fail' %arch))
    deploy_fail = self.getBuildsInOrder(os.path.join(statusdir, 'upload_%s_fail' %arch))
    awstests_fail = self.getBuildsInOrder(os.path.join(statusdir, 'awstest_%s_fail' %arch))

    stableBuild = ""
    for tag in builds_done:
      if tag in builds_fail:
        continue
      if tag not in tests_done or tag in tests_fail:
        continue
      if tag not in acctests_done or tag in acctests_fail:
        continue
      if tag not in deploy_done or tag in deploy_fail:
        continue
      if tag not in awstests_done or tag in awstests_fail:
        continue
      stableBuild = tag
      break
    return stableBuild


  def getLatestUntestedBuild(self, tempStatusFile, testedBuilds):
    latestUntestedBuild = ""
    toTest = self.getBuildsInOrder(tempStatusFile)
    tested = self.getBuildsInOrder(testedBuilds)
    for x in toTest:
      if x not in tested:
        return x
    return latestUntestedBuild

  def getAuthor(self, filename):
    if os.path.exists(filename):
      file = open(filename)
      lines = file.readlines()
      file.close()
      if len(lines) < 3:
        return 0
      for line in lines:
        if "Author" in line:
          #return lines[3].strip('Date:   ')
          return line.strip('Author:   ')
    else:
      return "-"

  def getDate(self, filename):
    if os.path.exists(filename):
      file = open(filename)
      lines = file.readlines()
      file.close()
      if len(lines) < 3:
        return 0
      for line in lines:
        if "Date" in line:
          #return lines[2].strip('Date:   ')
          return line.strip('Date:   ')
    else:
      return "-"


cgitb.enable()
form = cgi.FieldStorage()

print "Content-Type: text/plain"
print 


allbuilds = list()

builds_inprogress = list()
builds_done = list()
builds_fail = ()

tests_inprogress = list()
tests_done = list()
tests_fail = list()

acctests_inprogress = list()
acctests_done = list()
acctests_fail = list()

perftests_inprogress = list()
perftests_done = list()
perftests_fail = list()

deploy_inprogress = list()
deploy_done = list()
deploy_fail = list()

awstests_inprogress = list()
awstests_done = list()
awstests_fail = list()


buildsdir = "/Volumes/big/www/jenkins/builds"
statusdir = "/Volumes/big/www/jenkins/status"

status = JenkinsStatus()


rooturl = "http://data/jenkins"
buildurl = "http://data/jenkins/builds"
statusurl="http://data/jenkins/status"

printTable('Linux')

