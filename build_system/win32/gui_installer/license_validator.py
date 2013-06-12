import os
import sys
import win32api
import subprocess
#from nupic.bindings.network import LicenseInfo
#
#def validateLicenseFile(license_file):
#  """Validate the license file using the LicenseInfo binding
#
#  """
#  license = LicenseInfo.readLicense(license_file)
#  if license.status == LicenseInfo.valid:
#    raise Exception(license.message)

def validateLicenseFile(validate_license, license_file, output_file):
  """Validate the license file using validate_license.exe

  Executes the 'license' command. The output of a valid license
  will contain the string 'fileInfo:version    1.0'

  """
  f = open(output_file, 'w')
  validate_license = win32api.GetShortPathName(validate_license)
  license_file = win32api.GetShortPathName(license_file)

  cmd = [validate_license, license_file]
  startupinfo = subprocess.STARTUPINFO()
  startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
  print 'validateLicenseFile()', ' '.join(cmd)
  output = subprocess.Popen(cmd,
                       startupinfo=startupinfo,
                       stdout=subprocess.PIPE).communicate()[0]

  print 'output="%s"' % output

  status = output.split('\n')[-2]
  print 'status="%s"' % status

  if status.startswith('valid'):
    f.write('valid')
  else:
    f.write(status)

if __name__=='__main__':
  if not len(sys.argv) == 4:
    print 'Usage: python2 license_validator.py <validate_license_path> <license_file> <output_file>'
    sys.exit(1)
  
  for x in sys.argv[1:]:
    print x, os.path.isfile(x)
  validate_license_path, license_file, output_file = sys.argv[1:]
  
  validateLicenseFile(validate_license_path, license_file, output_file)
