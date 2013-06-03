import os
import sys
from ctypes import *
    
def singleInstance(pipe_name):
  """A decorator that makes sure only one app instance is running
  
  It tries to create a named pipe and if it fails it means another
  instance already created the pipe. The decorated function
  will be executed only if the pipe is created successfully
  """
  def createNamedPipe(pipe_name):
    
    PIPE_ACCESS_INBOUND = 1
    PIPE_TYPE_BYTE = 0
    MAX_INSTANCES = 1
    BUF_SIZE = 1
    NMPWAIT_USE_DEFAULT = 0
    INVALID_HANDLE_VALUE = -1
    
    # Added the required mumbo-jumbo to make it a valid pipe name
    # See: http://msdn.microsoft.com/en-us/library/aa365783(VS.85).aspx
    pipe_name = '\\\\.\\pipe\\' + pipe_name 
    hPipe = windll.kernel32.CreateNamedPipeA(pipe_name,
                                             PIPE_ACCESS_INBOUND,
                                             PIPE_TYPE_BYTE,
                                             MAX_INSTANCES,
                                             BUF_SIZE,
                                             BUF_SIZE,
                                             NMPWAIT_USE_DEFAULT,
                                             None)
    #if hPipe == -1:
    #  print windll.kernel32.GetLastError()
    return hPipe
  def decorated(func, *args, **kw):
    hPipe = -1
    try:
      # Create the pipe
      #print 'Decorator creating pipe...'
      hPipe = createNamedPipe(pipe_name)
      
      # If succeeded call the actual function
      if hPipe != -1:
        #print 'Pipe created successfully:', hPipe
        return func(*args, **kw)
      else:
        #print 'Failed to create pipe:', pipe_name
        pass
    except Exception, e:
      print e
      
    finally:
      # Close the handle for the single instance pipe if necessary      
      if hPipe != -1:
        #print 'Decorator closing pipe...'
        res = windll.kernel32.CloseHandle(hPipe)
        assert res == 1
      
  return decorated

#----------------------------------------------------------------------

#import time
#
#@singleInstance('NupicInstaller')
#def test():
#  print 'test() here'
#  hPipe = -1 # INVALID_HANDLE_VALUE
#  try:    
#    start = time.time()
#    i = 0
#    while time.time() < start + 10:
#      i += 1
#      print i
#      time.sleep(1)
#  
#    print 'Done.'  
#  except Exception, e:
#    print e
#
#if __name__=='__main__':
#  try:
#    test()
#  finally:
#    # This is necessary because PyInstaller executables tend to relaunch
#    # themselves multiple times without it
#    sys.exit(0)
