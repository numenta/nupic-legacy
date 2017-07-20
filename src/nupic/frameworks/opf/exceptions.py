


class HTMPredictionModelException(Exception):
  """
  Base exception class for
  :class:`~nupic.frameworks.opf.htm_prediction_model.HTMPredictionModel`
  exceptions.

  :param errorString: (string) Error code/msg: e.g., "Invalid request
                      object."
  :param debugInfo: (object) An optional sequence of debug information; must
                    be convertible to JSON; pass None to ignore.
"""
  def __init__(self, errorString, debugInfo=None):
    super(HTMPredictionModelException, self).__init__(errorString, debugInfo)
    self.errorString = errorString
    self.debugInfo = debugInfo
    return



class HTMPredictionModelInvalidArgument(HTMPredictionModelException):
  """
  Raised when a supplied value to a method is invalid.
  """
  pass



class HTMPredictionModelInvalidRangeError(HTMPredictionModelException):
  """
  Raised when supplied ranges to a method are invalid.
  """
  pass
