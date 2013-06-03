import os
import sys
import traceback
import config
import installer
import threading
import time
import pythoncom
import shutil
import  wx
import  wx.wizard as wiz

from SingleInstance import singleInstance
open('loggggg.txt', 'w').write('*************')
def out(s):
  #open('~/Documents/loggggg.txt', 'a').write(str(s) + '\n')
  open('loggggg.txt', 'a').write(str(s) + '\n')
  print str(s)

try:
  # This is the directory that PyInstaller unpacks all the binary files into
  out('Getting binary dir')
  binary_dir = os.environ['_MEIPASS2']
except KeyError:
  # If there is no such environment variable it means it NupicInstaller.pyw
  # runs outside of the installer. This mode is useful during development
  # and the binary dir in this case is just the source directory.
  binary_dir = os.path.dirname(os.path.abspath(__file__))
except Exception, e:
  out(str(e))

out('binary dir: ' + os.path.abspath(binary_dir))

#----------------------------------------------------------------------
def errorHandler(func):
  """Error handling decorator

  This decorator wraps each decorated method
  in a try-except block that calls self.onFailure()
  in case of an exception. This decorator should be applied naturally
  just to methods of classes that have a an a proper onFailure() method.

  Note that SystemExit is re-raised (raised as a result of sys.exit())
  """
  def decorated(*args, **kwds):
    try:
      return func(*args, **kwds)
    except SystemExit:
      raise
    except Exception, e:
      target = args[0]
      # Thread classes have a sink attribute that should be called
      if hasattr(target, 'sink'):
        target = target.sink
      target.onFailure(e)
  return decorated

#----------------------------------------------------------------------
class BaseWizardPage(wiz.PyWizardPage):
  """Base class of all wizard pages

  - Creates a vertical sizer
  - Adds a title and a static line
  - Define an addControl method that allows adding more
    controls to the vertical sizer
  """
  def __init__(self, parent, title):
    super(BaseWizardPage, self).__init__(parent)
    self.prev = None
    self.next = None
    self.parent = parent
    self.sizer=wx.BoxSizer(wx.VERTICAL)

    horiz_sizer = wx.BoxSizer(wx.HORIZONTAL)
    image_path = os.path.join(binary_dir, 'numenta.png')
    image = wx.Image(image_path, wx.BITMAP_TYPE_PNG)
    w, h = image.GetWidth(), image.GetHeight()
    scale_factor = 0.4
    w *= scale_factor
    h *= scale_factor
    image = image.Scale(w, h, wx.IMAGE_QUALITY_HIGH)
    image.SetMaskColour(255, 255, 255)

    bitmap = image.ConvertToBitmap()
    top_bitmap = wx.StaticBitmap(self, -1, bitmap, size = (w,h))

    image_path = os.path.join(binary_dir, 'numenta_logo.png')
    image = wx.Image(image_path, wx.BITMAP_TYPE_PNG)

    # Make the logo the same height as the scaled numenta image
    scale_factor = h / image.GetHeight()
    w, h = image.GetWidth(), image.GetHeight()
    w *= scale_factor
    h *= scale_factor
    image = image.Scale(w, h, wx.IMAGE_QUALITY_HIGH)
    image.SetMaskColour(255, 255, 255)
    bitmap = image.ConvertToBitmap()
    logo_bitmap = wx.StaticBitmap(self, -1, bitmap, size = (w,h))

    horiz_sizer.Add(logo_bitmap, 0, wx.ALIGN_CENTRE|wx.ALL,5)
    horiz_sizer.Add(top_bitmap, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

    title = wx.StaticText(self, -1, title)
    title.SetFont(wx.Font(config.titleFontSize, wx.SWISS, wx.NORMAL, wx.BOLD))

    self.sizer.Add(horiz_sizer, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
    self.sizer.Add(title, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
    self.sizer.Add(wx.StaticLine(self, -1), 0, wx.EXPAND|wx.ALL, 5)
    self.font = wx.Font(config.textFontSize, wx.SWISS, wx.NORMAL, wx.NORMAL)

    # Should be implemented by subclass to add custom controls
    self.populate()

    self.SetSizerAndFit(self.sizer)

  @errorHandler
  def addControl(self, control, proportion=0, font=None):
    self.sizer.Add(control, proportion, wx.EXPAND|wx.ALL, 5)
    if type(control) in (wx.StaticText, wx.TextCtrl):
      if font:
        control.SetFont(font)
      else:
        control.SetFont(self.font)

  @errorHandler
  def addLabel(self, proportion=1, multiLine=True):
    style = wx.TE_READONLY|wx.NO_BORDER
    if multiLine:
      style |= (wx.TE_MULTILINE | wx.TE_NO_VSCROLL)
    label = wx.TextCtrl(self, -1, '', style=style)
    label.SetBackgroundColour(self.GetBackgroundColour())
    self.addControl(label, proportion)
    return label

  def populate(self):
    """Override in subclasses to add more controls

    Use the addControl() method to add more controls
    to the sizer
    """
    pass

  def onShow(self):
    self.enableNext()

  def disableNext(self):
    self.parent.FindWindowById(wx.ID_FORWARD).Disable()

  def enableNext(self):
    self.parent.FindWindowById(wx.ID_FORWARD).Enable()

  def disablePrev(self):
    self.parent.FindWindowById(wx.ID_BACKWARD).Disable()

  def enablePrev(self):
    self.parent.FindWindowById(wx.ID_BACKWARD).Enable()

  def SetNext(self, next):
    self.next = next

  def SetPrev(self, prev):
    self.prev = prev

  def GetNext(self):
    return self.next

  def GetPrev(self):
    return self.prev

  def onFailure(self, exception):
    """Handles any exception raised during installation

    It is hooked up using the errorHandler decorator.
    This method will be called by this decorator whenever a method decorated
    with @errorHandler raises an unhandled exception.

    onFailure() collects the exception information using its internal
    formatExceptionInfo() function and uses wx.CallAfter(handleFailure_).
    This guarantuees that even exceptions raised in a thread will be handled
    in the main thread. The raising thread should be done by then.
    """
    def collectExceptionInfo(maxTBlevel=10):
      """Collects exception class, the exception description and traceback"""
      cla, exc, trbk = sys.exc_info()
      excName = cla.__name__
      try:
        excArgs = exc.__dict__["args"]
      except KeyError:
        excArgs = "<no args>"
      excTb = traceback.format_tb(trbk, maxTBlevel)
      return (excName, excArgs, excTb)

    exceptionInfo = collectExceptionInfo()
    out('Exception class: ' + str(exceptionInfo[0]))
    out('Exception arguments: ' + str(exceptionInfo[1]))
    tb = ''.join(exceptionInfo[2])
    out('Exception traceback:')
    out(tb)

    error_message = config.failure_message % str(exception)
    wx.CallAfter(self._handleFailure, error_message)

  def _handleFailure(self, error_message):
    """Unified error handling

    Shows an error message box and exits. The error handling
    infrastructure makes sure it is called only on the main thread
    after all threads are done.
    """
    wx.MessageBox(error_message,
                  'NuPIC Installation Failed',
                  wx.OK | wx.ICON_ERROR)

    sys.exit(1)

#----------------------------------------------------------------------

class StartPage(BaseWizardPage):
  def __init__(self, parent):
    super(StartPage, self).__init__(parent, config.start_title)

  @errorHandler
  def populate(self):
    self.addControl(wx.StaticText(self, -1, config.start_message))

  @errorHandler
  def onNext(self):
    installer.installPython(config.python_version, binary_dir)
    print 'Done installing Python'
    installer.installWx(config.python_version, config.wx_version, binary_dir)
    print 'Done installing Wx'

#----------------------------------------------------------------------

class SelectInstallationFolderPage(BaseWizardPage):
  def __init__(self, parent):
    self.folder = None
    super(SelectInstallationFolderPage, self).__init__(parent,
                                                       config.select_install_folder_title)

  def checkInstallationFolder(self, folder):
    if os.path.isfile(folder):
      raise Exception("Installation folder '%s' is a file!" % folder)
    if os.path.isdir(folder):
      self.warning.Value = config.select_install_folder_warning
      self.warning.BackgroundColour = config.warning_color
    else:
      self.warning.Value = ''
      self.warning.BackgroundColour = self.parent.BackgroundColour
      self.warning.Refresh()

  @errorHandler
  def populate(self):
    text = wx.StaticText(self, -1, config.select_install_folder_message)
    self.addControl(text, proportion=1)

    panel = wx.Panel(self, -1)

    sizer=wx.BoxSizer(wx.HORIZONTAL)
    label = wx.StaticText(panel, -1, 'Installation Folder: ')
    sizer.Add(label, 0, wx.ALIGN_LEFT|wx.ALL, 3)

    self.warning = self.addLabel(proportion=0)
    if 'NTAX_INSTALL_DIR' in os.environ:
      initialFolder = os.environ['NTAX_INSTALL_DIR']
      if not 'nupic-' in initialFolder:
        initialFolder = os.path.join(initialFolder,
                                 'nupic-%s' % config.nupic_version)
    else:
      initialFolder = os.path.join(installer.getProgramFilesDir(), 'Numenta',
                                 'nupic-%s' % config.nupic_version)

    initialFolder = os.path.normpath(initialFolder)
    self.folder = wx.TextCtrl(panel, -1, initialFolder)
    self.folder.SetEditable(False)
    sizer.Add(self.folder, 1, wx.EXPAND|wx.ALL, 3)

    button = wx.Button(panel, -1, '...', size=(30,20))
    self.Bind(wx.EVT_BUTTON, self.onBrowse, button)
    sizer.Add(button, 0, wx.ALIGN_RIGHT|wx.ALL, 3)

    panel.SetSizerAndFit(sizer)
    self.addControl(panel)

    self.checkInstallationFolder(initialFolder)

  @errorHandler
  def onBrowse(self, evt):
    dlg = wx.DirDialog(self, "Select a directory:",
                      style=wx.DD_DEFAULT_STYLE
                       | wx.DD_DIR_MUST_EXIST
                       #| wx.DD_CHANGE_DIR

                       )
    if self.parent.installDir:
      initialPath = os.path.dirname(self.parent.installDir)
    elif 'NTAX_INSTALL_DIR' in os.environ:
      initialPath = os.environ['NTAX_INSTALL_DIR']
    else:
      initialPath = 'c:/nta/install'
      initialPath = installer.getProgramFilesDir()
    dlg.SetPath(initialPath)

    # If the user selects OK, then we process the dialog's data.
    # This is done by getting the path data from the dialog - BEFORE
    # we destroy it.
    if dlg.ShowModal() == wx.ID_OK:
      self.parent.installDir = os.path.join(dlg.GetPath(),
                                            'nupic-%s' % config.nupic_version)
      self.folder.SetValue(self.parent.installDir)
      self.enableNext()

    # Only destroy a dialog after you're done with it.
    dlg.Destroy()
    self.checkInstallationFolder(self.folder.Value)

  @errorHandler
  def onNext(self):
    self.parent.installDir = self.folder.Value

  @errorHandler
  def onShow(self):
    if self.parent.installDir:
      self.folderValue = self.parent.installDir

    self.checkInstallationFolder(self.folder.Value)


#----------------------------------------------------------------------

class InstallNupicThread(threading.Thread):
  def __init__(self,
               binary_dir,
               install_dir,
               sink):
    threading.Thread.__init__(self)
    self.binaryDir = binary_dir
    self.installDir = install_dir
    self.sink = sink
    self.cancelEvent = threading.Event()

  def cancel(self):
    """Cancel the operation of the current thread

    Set the cancel event that the actual thread code is supposed to check
    using isCancelled() (oe actually through the shouldAbort() closure
    defined in the run() method
    """
    self.cancelEvent.set()

  def isCancelled(self):
    """Has the thread been cancelled?
    """
    return self.cancelEvent.isSet()

  @errorHandler
  def run(self):
    """The thread run function

    * Define a shouldAbort closure (if thread is cancelled from GUI)
    * Invoke installer.installNupic and pass the closure and the sink

    The installer.installNupic will check the closure and invoke the sink's
    callback functions. The sink is the InstllFilesPage and the
    callback functions are: onUpdate, onFailure, onCancel and onComplete.

    The thread is done when installNupic returns. It doesn't care about what
    happens. It is all taken care off by the sink.

    Note the explicit CoInitialize() and UnCoInitialize() calls surrounding the
    actual call to installNupic(). This is required since every thread
    needs a separate initialization/uninitialization of the COM libraries.
    """
    def shouldAbort():
      return self.isCancelled()

    pythoncom.CoInitialize()
    out('nupic_Version: ' + config.nupic_version)
    installer.installNupic(config.nupic_version,
                           config.python_version,
                           self.binaryDir,
                           self.installDir,
                           shouldAbort,
                           self.sink)
    
    pythoncom.CoUninitialize()
    print 'InstallNupicThread is done.'

class InstallFilesPage(BaseWizardPage):
  def __init__(self, parent):
    self.folder = None
    self.bytes = 0
    super(InstallFilesPage, self).__init__(parent, config.install_files_title)

  def logMessage(self, s):
    wx.CallAfter(self._log, s)
  def _log(self, s):
    self.log.Value = s

  @errorHandler
  def populate(self):
    self.text = self.addLabel(proportion=0, multiLine=False)
    self.text.Value = 'Calculating total compressed size...'
    #text = wx.StaticText(self, -1, 'Calculating total compressed size...')
    #self.addControl(text)

    self.currentFile = wx.TextCtrl(self, -1, '', style=wx.TE_READONLY)
    self.currentFile.SetEditable(False)
    font = wx.Font(config.textFontSize-2, wx.SWISS, wx.NORMAL, wx.NORMAL)
    self.addControl(self.currentFile, font=font)

    self.progressGauge = wx.Gauge(self, -1, 100, (0,0), (1, 25))
    self.progressGauge.SetBezelFace(3)
    self.progressGauge.SetShadowWidth(3)
    self.addControl(self.progressGauge)

    self.log = self.addLabel(proportion=0, multiLine=False)

  # installer callbacks
  def onComplete(self):
    #self.SetNext(page5)
    self.logMessage("Done. Click 'Next' to continue")
    self.enableNext()

  def onCancel(self):
    print 'cancelled'

  @errorHandler
  def updateProgress(self, filename, bytes, total_bytes):
    if not self.installerThread.isCancelled():
      if bytes == 0:
        self.text.Value = 'Extracting:'
      self.currentFile.SetValue(filename)
      self.bytes += bytes
      self.progressGauge.SetValue(self.bytes * 100 / total_bytes)

  def onUpdate(self, filename, bytes, total_bytes):
    if not self.installerThread.isCancelled():
      wx.CallAfter(self.updateProgress, filename, bytes, total_bytes)

  # Wizard callbacks

  @errorHandler
  def onShow(self):
    self.disablePrev()
    self.disableNext()
    self.installerThread = InstallNupicThread(binary_dir,
                                              self.parent.installDir,
                                              self)
    self.installerThread.start()

  @errorHandler
  def onCancelClick(self):
    self.installerThread.cancel()
    self.installerThread.join()
    assert not self.installerThread.isAlive()
    print 'onCancelClick() is done'

#----------------------------------------------------------------------

class CheckLicenseThread(threading.Thread):
  def __init__(self,
               install_dir,
               filename,
               sink):
    threading.Thread.__init__(self)
    self.filename = filename
    self.installDir = install_dir
    self.sink = sink

  @errorHandler
  def run(self):
    """The thread run function

    * Check the license file is really a file
    * Check it ends with 'license.cfg'
    * Run it through the runtime engine
    * Call the onComplete() callback on the GUI thread (via wx.CallAfter)

    """
    installer.out('CheckLicenseThread.run()')
    #sys_path = sys.path
    #sys.path.insert(0, os.path.join(self.installDir, 'lib', config.python_version))
    #installer.out(sys.path)
    #from nupic.bindings.network import LicenseInfo
    #installer.out('LicenseInfo imported successfully')
    #sys.path = sys_path

    valid = False
    message = ''
    a_file = os.path.isfile(self.filename)
    if not a_file:
      message = 'License file must be a file!'
    proper_filename = self.filename.endswith('license.cfg')
    if not proper_filename:
      message = "License file must end with 'license.cfg'."

    else:
      validate_license_cmd = os.path.join(binary_dir, 'validate_license.exe')
      assert os.path.isfile(validate_license_cmd)
      print validate_license_cmd
      assert os.path.isfile(validate_license_cmd)
      proper_license, message = installer.validateLicenseFile(validate_license_cmd,
                                                     self.filename,
                                                     binary_dir,
                                                     config.python_version)
      self.sink.logMessage(validate_license_cmd)
      valid = a_file and proper_filename and proper_license

    self.sink.logMessage('installer.validateLicenseFile() completed. valid = %s' % valid)
    wx.CallAfter(self.sink.onComplete, valid, message)

class InstallLicensePage(BaseWizardPage):
  def __init__(self, parent):
    self.file = None
    self.licenseFile = None
    self.thread = None
    super(InstallLicensePage, self).__init__(parent, config.install_license_title)

  def logMessage(self, s):
    wx.CallAfter(self._log, s)
  def _log(self, s):
    self.log.Value = self.log.Value + os.linesep + s

  @errorHandler
  def populate(self):
    self.licenseFile = 'No License'#installer.findLicenseFile()
    #if not self.licenseFile:
    #  license_message = config.install_license_message_1
    #else:
    #  license_message = config.install_license_message_2
    license_message = 'No License!!!'

    self.message = wx.StaticText(self, -1, license_message)
    self.addControl(self.message, proportion=1)

    self.log = self.addLabel(proportion=0, multiLine=False)

    panel = wx.Panel(self, -1)
    sizer=wx.BoxSizer(wx.HORIZONTAL)
    label = wx.StaticText(panel, -1, 'License File: ')
    sizer.Add(label, 0, wx.ALIGN_LEFT|wx.ALL, 3)

    self.file = wx.TextCtrl(panel, -1, self.licenseFile, style=wx.TE_READONLY)
    self.file.SetEditable(False)
    self.file.SetBackgroundColour(self.BackgroundColour)
    self.file.Bind(wx.EVT_TEXT, self.onFileSelect)
    sizer.Add(self.file, 1, wx.EXPAND|wx.ALL, 3)

    self.button = wx.Button(panel, -1, '...', size=(30,20))
    self.Bind(wx.EVT_BUTTON, self.onBrowse, self.button)
    sizer.Add(self.button, 0, wx.ALIGN_RIGHT|wx.ALL, 3)

    panel.SetSizerAndFit(sizer)
    self.addControl(panel)

    self.textColor = self.GetForegroundColour()

  @errorHandler
  def onComplete(self, valid, message):
    if valid:
      self.enableNext()
      self.file.BackgroundColour = config.success_color
      self.log.Value = 'License is valid.'
      # Copy license to user's common files directory
      license_dir = installer.getLicenseDir()
      if not os.path.isdir(license_dir):
        os.makedirs(license_dir)
      target_path = os.path.join(license_dir, os.path.basename(self.licenseFile))
      if target_path != self.licenseFile:
        print 'Copying license file %s to %s' % (self.licenseFile, target_path)
        shutil.copyfile(self.licenseFile, target_path)
        assert os.path.isfile(target_path)
    else:
      self.file.BackgroundColour = config.error_color
      self.log.Value = 'Invalid license: ' + message
      self.disableNext()
    self.file.Refresh()

  def validateLicense(self):
    self.disableNext();
    self.log.Value = 'Validating license. Please wait...'
    self.file.Refresh()
    self.log.Refresh()
    self.button.Disable()
    self.thread = CheckLicenseThread(self.parent.installDir, self.licenseFile, self).start()
    self.button.Enable()

  @errorHandler
  def onFileSelect(self, evt):
    self.licenseFile = evt.GetString()
    self.validateLicense()

  @errorHandler
  def onBrowse(self, evt):
    dlg = wx.FileDialog(self, "Select a file:",
                      style=wx.FD_DEFAULT_STYLE
                       | wx.FD_FILE_MUST_EXIST
                       )

    initialPath = ''
    dlg.SetPath(initialPath)

    # If the user selects OK, then we process the dialog's data.
    # This is done by getting the path data from the dialog - BEFORE
    # we destroy it.
    if dlg.ShowModal() == wx.ID_OK:
      self.licenseFile = dlg.GetPath()
      self.file.Value = self.licenseFile

    # Only destroy a dialog after you're done with it.
    dlg.Destroy()

  def onShow(self):
    self.disablePrev();
    self.disableNext();
    if self.licenseFile:
      self.validateLicense()

#----------------------------------------------------------------------

class SuccessPage(BaseWizardPage):
  def __init__(self, parent):
    super(SuccessPage, self).__init__(parent, config.success_title)

  def populate(self):
    self.message = self.addLabel()

  def onShow(self):
    self.disablePrev();
    self.message.Value = config.success_message % self.parent.installDir

    print self.message.Value

  @errorHandler
  def onNext(self):
    #pass
    installer.openVisionDir(self.parent.installDir)


#----------------------------------------------------------------------
class NupicInstallerWizard(wiz.Wizard):
  def __init__(self, title, side_image):
    super(NupicInstallerWizard, self).__init__(None, -1, title, side_image)
    wiz.EVT_WIZARD_PAGE_CHANGING(self, self.GetId(), self.onPageChanging)
    wiz.EVT_WIZARD_PAGE_CHANGED(self, self.GetId(), self.onPageChanged)
    wiz.EVT_WIZARD_CANCEL(self, self.GetId(), self.onCancel)
    self.installDir = None
    print 'Wizard created'

  def onPageChanging(self, evt):
    page = evt.GetPage()
    if evt.Direction:
      if hasattr(page, 'onNext'):
        page.onNext()
    else:
      if hasattr(page, 'onPrev'):
        page.onPrev()

  def onPageChanged(self, evt):
    page = evt.GetPage()
    if hasattr(page, 'onShow'):
      page.onShow()

  def onCancel(self, evt):
    cancel_message = 'Are you sure you want to cancel the NuPIC %s installation?'
    rc = wx.MessageBox(cancel_message % config.nupic_version,
                  'NuPIC %s Installer' % config.nupic_version,
                  wx.YES| wx.NO | wx.ICON_QUESTION)

    if rc == wx.NO:
      evt.Veto()
      return

    # Ok, let's cancel. First hide the window
    self.Hide()
    page = evt.GetPage()
    # Pages that has onCancelClick interact with threads
    # and need to know when 'cancel' was clicked
    if hasattr(page, 'onCancelClick'):
      page.onCancelClick()

    # Now, remove the install directory
    print 'Removing', self.installDir
    if os.path.isdir(self.installDir):
      assert 'nupic' in self.installDir
      shutil.rmtree(self.installDir)
      assert not os.path.exists(self.installDir)
    print 'Removed', self.installDir

    # Restore the environment variables
    installer.restoreEnvironment()
    sys.exit()


#----------------------------------------------------------------------

class App(wx.App):
  def __init__(self):
    #log_file = os.path.join(installer.getDocumentsDir(),
    #                        'nupic.installer.log.txt')
    #wx.App.__init__(self, redirect=True, filename=log_file)
    wx.App.__init__(self, redirect=False)

@singleInstance('NupicInstaller')
def main():
    app = App()
    out('App created')
    image_path = os.path.join(binary_dir, 'nupic.png')
    out('1' * 20)
    image = wx.Image(image_path, wx.BITMAP_TYPE_PNG)
    out('2' * 20)
    w, h = image.GetWidth(), image.GetHeight() * 1.15
    out('3' * 20)
    image = image.Scale(w, h, wx.IMAGE_QUALITY_HIGH)
    out('4' * 20)
    side_bitmap = image.ConvertToBitmap()
    out('5' * 20)  
    wizard = NupicInstallerWizard(config.title, side_bitmap)
    out('Wizard created')
    try:
      icon = wx.Icon(os.path.join(binary_dir, 'setup.ico'), wx.BITMAP_TYPE_ICO)
      wizard.SetIcon(icon)
    except Exception, e:
      out(str(e))

    page1 = StartPage(wizard)
    page2 = SelectInstallationFolderPage(wizard)
    page3 = InstallFilesPage(wizard)
    page4 = InstallLicensePage(wizard)
    page5 = SuccessPage(wizard)

    # Set the initial order of the pages
    page1.SetNext(page2)
    page2.SetPrev(page1)
    page2.SetNext(page3)
    page3.SetPrev(page2)
    # Skip license checking for NuPIC 2
    #page3.SetNext(page4)
    #page4.SetPrev(page3)
    #page4.SetNext(page5)
    page3.SetNext(page5)
    wizard.GetPageAreaSizer().Add(page1)

    out('Running wizard')
    if not wizard.RunWizard(page1):
      # Wait for all threads to complete
      while (threading.activeCount() > 1):
        time.sleep(1)
      out('Wizard was cancelled')
    else:
      out('Wizard completed successfully')

    wizard.Destroy()
    out('Wizard destroyed')
    app.MainLoop()
    out('Done!')

if __name__=='__main__':
  try:
    out('Alright !!!!')
    main()
  finally:
    # This is necessary because PyInstaller executables tend to relaunch
    # themselves multiple times without it
    out('About to sys.exsit...')
    sys.exit(0)
