debug = '$Debug'
python_version = '$PythonVersion'
full_python_version = '$FullPythonVersion'
nupic_version = '$NupicVersion'
wx_version = '$WxVersion'

title = 'NuPIC %s Installer' % nupic_version

titleFontSize=18
textFontSize=10

success_color = 'green'
error_color = 'red'
warning_color = 'yellow'

start_title = 'Welcome to the NuPIC %s install wizard' % nupic_version
start_message = """\
The installer will perform the following actions:

  * Install Python %s (if needed)
  * Install wxPython %s (if needed)
  * Install NuPIC files
  * Install NuPIC's license (if one is not installed already)
  * Add Python to your PATH (if needed)
  * Add NuPIC's libraries to PYTHONPATH
  * Add NTA environment variable that points to Nupic's installation folder
  * Add NuPIC's runtime engine to the firewall exception list
  * Open a command prompt Window in the vision folder

If a previous version of NuPIC is installed the installer will update
all the environment variables to point to the new version.

The installation requires administrator privileges.
""" % (full_pythonVersion, wx_version)

select_install_folder_title = 'Select NuPIC Installation Folder'
select_install_folder_message = """\
The installer will create under the folder you select a sub-folder
named 'nupic-%s'. NuPIC will be installed under this sub-folder.                       
""" % nupic_version                        

select_install_folder_warning = """\
Warning: the installation folder already exists.
The installer will overwrite its contents. 

You may select a different folder.\
"""

install_files_title = 'Installing NuPIC Files...'
#install_files_message = """\
#Select NuPIC's installation folder.
#The installer will create under the installation folder
#a sub-folder named: 'nupic-%s'                       
#""" % nupic_version                        

install_license_title = 'Install NuPIC license'
install_license_message_1 = """\
Select NuPIC's license file.

If you haven't received a license file by email contact support@numenta.com.
The installer will copy the license file to the proper location.

Note: the license filename must end with 'license.cfg' (e.g. proper-license.cfg)
"""

install_license_message_2 = """\
You already have a license file installed.

You may select to install a different license file.

If you haven't received a license file by email contact support@numenta.com.
The installer will copy the license file to the proper location.

Note: the license filename must end with 'license.cfg' (e.g. proper-license.cfg)
"""

success_title = 'Installation completed successfully'
success_message = """\
NuPIC is installed in %s

The installer  will open a command prompt
window in the vision project folder.

Type 'python2 RunExperiment.py experiments\fdr\horizontalCL\autoperf\quick'
and press <ENTER> to validate your installation.
"""

failure_title = 'Installation Failed'
failure_message = """\
Installation failed.

Error description: %s
"""

remove_dir_message = """\
Installation folder %s is not empty.

The installer will remove its existing contents.
You should backup your data and programs before proceeding
with the installation.

Do you wish to install NuPIC into %s?

Press 'YES' to proceed with the installation
Press 'NO'  to select a different installation folder
Press 'CANCEL' to cancel the installation altogether
"""

remove_dir_failure_message = """\
Unable to remove directory '%s'.

Please close all other programs and try again."""

if __name__=='__main__':
  import NupicInstaller
  NupicInstaller.main()
