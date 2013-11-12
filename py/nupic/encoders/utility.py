
from nupic.encoders.multi import MultiEncoder as ME

class UtilityEncoder(MultiEncoder):
  """UtilityEncoder act transparently; use input and apply it to encoder, 
     in addition, provide a new field utility (aka \'usefulness\'/goodness/fitness/evaluation) of the input"""
  
  def __init__(self, encoder, feval, utility, name='encoding'):
    """param encoder: original encoder, accepts input; 
       param feval: an evaluation function: must handle all inputs from input, util=feval(input);
       param utility: encoder, maps output of feval to some values. Must take all outputs of feval"""
    if not(isinstance(encoder,Encoder) and isinstance(feval, function) and isinstance(utility, Encoder)):
      raise Exception("must provide an encoder and a function that takes encoder's output and transforms to utility encoder's input")

    super(UtilityEncoder,self).__init__()

    self.addEncoder(name, encoder)
    self.addEncoder('utility', utility)
    
    self._utility = utility
    self._encoder = encoder
    self._feval = feval
    self._offset = encoder.width()
    self._parent = super(UtilityEncoder, self)

  def encodeIntoArray(self, input, output)
    """on original input, compute utility and append it as "input" for processing"""
    util = self._feval(input)
    merged_input = [input, util]
    self._parent.encodeIntoArray(merged_input,output)

  def decode(self, encoded, parentFieldNames=''):
    """takes the extended input from above, and recovers back values for orig input and utility"""

    # the question is, whether to break "reflexivness" A==decode(encode(A)) and return two values: decoded & utility
    (decoded,util) = self._parent.decode(encoded, parentFieldNames)
  
    #or to override decode() -raise Exception() and use def decode(encoded, parentFieldNames, utility) and pass it by param.

    
    
