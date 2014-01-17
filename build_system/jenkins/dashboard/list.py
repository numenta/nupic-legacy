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
  print "<br>\nlatest_stable_build:"
  print status.getLastStableBuild(arch)
  print "\n<br>"
  print """<DIV STYLE="overflow: auto; width: 1500px; height: 1200; 
            border-left: 0px gray solid; border-bottom: 0px gray solid; 
            padding:0px; margin: 0px"> """
  print "<table border=1>"
  if arch == "Darwin":
    perfsys = "perf-darwin86.numenta.com"
    print """ <thead> <tr bgcolor="#CCFFFF"> <th>Tag</th> <th>Date</th> <th>Author</th> <th>Build</th> <th>Standard Tests</th>
              <th>Acceptance Tests</th> <th>Performance Tests</th></tr> </thead> <tbody> """
  else:
    perfsys = "perf-linux64"
    print """ <thead> <tr bgcolor="#CCFFFF"> <th>Tag</th> <th>Date</th> <th>Author</th> <th>Build</th> <th>Standard Tests</th>
              <th>Acceptance Tests</th> <th>Performance Tests</th><th>Push to S3</th><th>AWS Tests</th></tr> </thead> <tbody> """

  nBuilds = min(100, len(allbuilds))
  for i in xrange(0, nBuilds):
      build = ""
      tests = ""
      acctests = ""
      perftests = ""
      deploy = ""
      awstests = ""
      tag = allbuilds[i].rstrip()
      # Is build in progress?
      if tag in builds_inprogress:
        build = "inprogress"
      else:
        if tag in builds_fail:
          build = "fail"
          tests = ""
          acctests = ""
          perftests = ""
          awstests = ""
        else:
          build = "pass"
          if tag in tests_inprogress:
            tests = "inprogress"
          elif tag in tests_done:
            tests = "pass"
            if tag in tests_fail:
              tests = "fail"
          if tag in acctests_inprogress:
            acctests = "inprogress"
          elif tag in acctests_done:
            acctests = "pass"
            if tag in acctests_fail:
              acctests = "fail"
          if tag in perftests_inprogress:
            perftests = "inprogress"
          elif tag in perftests_done:
            perftests = "pass"
            if tag in perftests_fail:
              perftests = "fail"
          if tag in deploy_inprogress:
            deploy = "inprogress"
          elif tag in deploy_done:
            deploy = "pass"
            if tag in deploy_fail:
              deploy = "fail"
          if tag in awstests_inprogress:
            awstests = "inprogress"
          elif tag in awstests_done:
            awstests = "pass"
            if tag in awstests_fail:
              awstests = "fail"

      url = "%s/%s_%s.tgz" % (buildurl, tag, arch)
      taginfo = "%s/%s/info" %(rooturl, tag)
      buildlog_url = "%s/%s/build_%s.out" % (rooturl, tag, arch)
      standardlog_url = "%s/%s/standard.out" % (rooturl, tag)
      shortlog_url = "%s/%s/short.out" % (rooturl, tag)
      acceptancelog_url = "%s/%s/acceptance.out" % (rooturl, tag)
      perflog_url = "%s/%s/PerfTestResults_%s.txt" % (rooturl, tag, perfsys)
      awslog_url = "%s/%s/ClusterTestResults.txt" % (rooturl, tag)
      deploylog_url = "%s/%s/deploy.out" % (rooturl, tag)

      statuses_print = {}
      print '<tr>'

      statuses_print['tag'] = '<td><a href="%s"><img height=20px width=20px src="%s/info.png"></img></a><a href="%s">%s</a></td>' % (taginfo,rooturl, tag, tag)
      statuses_print['date'] = '<td>%s</td>' %status.getDate(os.path.join(tag,"info"))
      statuses_print['author'] = '<td>%s</td>' %status.getAuthor(os.path.join(tag,"info"))
      if build == "inprogress":
        statuses_print['build'] = '<td class="%s">%s</td>' % (build, "In Progress")
      else:
        statuses_print['build'] = '<td class="%s"><a href="%s">%s</a><a href="%s"><img height=20px width=20px src="%s/download.png"></img></a></td>' % (build, buildlog_url, "Log", url, rooturl)

      statuses_print['push'] = '<td><img height=20px width=20px src="%s/big-red-button.jpg"></img></td>' %rooturl

      if tests == "inprogress":
        statuses_print['tests'] = '<td class="%s">%s</td>' % (tests, "In Progress")
      elif tests == "pass" or tests == "fail":
        statuses_print['tests'] = '<td class="%s"><a href="%s">%s</a></td>' % (tests, standardlog_url, "Log")
      else:
        statuses_print['tests'] = '<td class="%s">' % ("")

      if acctests == "inprogress":
        statuses_print['acctests'] = '<td class="%s">%s</td>' % (acctests, "In Progress")
      elif acctests == "pass" or acctests == "fail":
        statuses_print['acctests'] = '<td class="%s"><a href="%s">%s</a><a href="%s">%s</a></td>' % (acctests, shortlog_url, " Short   |", acceptancelog_url, "    Acceptance ")
      else:
        statuses_print['acctests'] = '<td class="%s">' % ("")

      if perftests == "inprogress":
        statuses_print['perftests'] = '<td class="%s">%s</td>' % (perftests, "In Progress")
      elif perftests == "pass" or perftests == "fail":
        statuses_print['perftests'] = '<td class="%s"><a href="%s">%s</a></td>' % (perftests, perflog_url, "Log")
      else:
        statuses_print['perftests'] = '<td class="%s">' % ("")

      if deploy == "inprogress":
        statuses_print['deploy'] = '<td class="%s">%s</td>' % (deploy, "In Progress")
      elif deploy == "pass" or deploy == "fail":
        statuses_print['deploy'] = '<td class="%s">%s</td>' % (deploy, deploy.upper())
      else:
        statuses_print['deploy'] = '<td class="%s">' % ("")

      if awstests == "inprogress":
        statuses_print['awstests'] = '<td class="%s">%s</td>' % (awstests, "In Progress")
      elif awstests == "pass" or awstests == "fail":
        statuses_print['awstests'] = '<td class="%s"><a href="%s">%s</a></td>' % (awstests, awslog_url, "Log")
      else:
        statuses_print['awstests'] = '<td class="%s">' % ("")

      print statuses_print['tag']
      print statuses_print['date']
      print statuses_print['author']
      print statuses_print['build']
      print statuses_print['tests']
      print statuses_print['acctests']
      print statuses_print['perftests']
      if arch == "Linux":
        print statuses_print['deploy']
        print statuses_print['awstests']

      print '</tr>'
  print '</table>'
  print '</div>'


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

print "Content-Type: text/html"
print
print "<head>"
print "<title>Jenkins Dashboard</title>"
print "<meta http-equiv='refresh' content='60'>"
print '<link rel="stylesheet" type="text/css" href="mystyle.css" />'
print "</head>"
print "<body>"

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


rooturl = "http://data.corp.numenta.com/jenkins"
buildurl = "http://data.corp.numenta.com/jenkins/builds"
statusurl="http://data.corp.numenta.com/jenkins/status"

print '<h2>Linux Builds <a href="http://172.16.190.210:8080">- Jenkins</a></h2>'
currentTime = datetime.datetime.fromtimestamp(time.time())
print "Last updated: " + str(currentTime)
printTable('Linux')

print '<h2>Darwin Builds <a href="http://172.16.190.219:8080">- Jenkins</a></h2>'
printTable('Darwin')

print "</tbody>"
print "</body>"
