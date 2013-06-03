import os
import sys
import win32com.client

def _getAuthorizedApplications():
  fw = win32com.client.Dispatch('HNetCfg.FwMgr')
  p = fw.LocalPolicy.CurrentProfile
  aa = p.AuthorizedApplications

  return aa

def _authorizeApplication(filename, enable):
  assert(os.path.isfile(filename))
  aa = _getAuthorizedApplications()

  # If app is already in the list authorize it
  for a in aa:
    if a.ProcessImageFileName == filename:
      a.Enabled = enable
      return

  # Add the app with proper the proper enable value
  a = win32com.client.Dispatch('HNetCfg.FwAuthorizedApplication')
  a.Name = os.path.basename(filename)
  a.ProcessImageFileName = filename
  a.IpVersion = 2
  a.Scope = 0
  a.RemoteAddresses = '*'
  a.Enabled = enable

  aa.Add(a)


def allow(filename):
  _authorizeApplication(filename, True)

def block(filename):
  _authorizeApplication(filename, False)

def remove(filename):
  aa = _getAuthorizedApplications()
  for a in aa:
    if a.ProcessImageFileName == filename:
      aa.Remove(a)
      return

def list():
  aa = _getAuthorizedApplications()
  for a in aa:
    print '-' * 20
    print 'Name:', a.Name
    print 'Filename:', a.ProcessImageFileName
    print 'IpVersion:', a.IpVersion
    print 'Scope:', a.Scope
    print 'Enabled:', a.Enabled
