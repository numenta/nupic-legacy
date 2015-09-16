


class CLAModelException(Exception):
  """ base exception class for cla model exceptions """
  def __init__(self, errorString, debugInfo=None):
    """
    Parameters:
    -----------------------------------------------------------------------
    errorString:    Error code/msg: e.g., "Invalid request object."
    debugInfo:      An optional sequence of debug information; must be
                     convertible to JSON; pass None to ignore
    """
    super(CLAModelException, self).__init__(errorString, debugInfo)
    self.errorString = errorString
    self.debugInfo = debugInfo
    return



class CLAModelInvalidArgument(CLAModelException):
  """
  Raised when a supplied value to a method is invalid.
  """
  pass



class CLAModelInvalidRangeError(CLAModelException):
  """
  Raised when supplied ranges to a method are invalid.
  """
  pass