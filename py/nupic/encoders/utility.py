
from nupic.encoders.multi import MultiEncoder as ME

class UtilityEncoder(MultiEncoder):
  """UtilityEncoder act transparently; use input and apply it to encoder, 
     in addition, provide a new field utility (aka \'usefulness\'/goodness/fitness/evaluation) of the input"""
  
  def __init__(self, inputEncoder, feval, utilityEncoder, name='encoding'):
    """param inputEncoder: original encoder, accepts input; 
       param feval: an evaluation function: must handle all inputs from inputEncoder, its output must be acceptable by utilityEncoder; util=feval(input);
       param utilityEncoder: encoder, maps output of feval to some values. Must take all outputs of feval"""
    if not(isinstance(encoder,Encoder) and isinstance(feval, function) and isinstance(utility, Encoder)):
      raise Exception("must provide an encoder and a function that takes encoder's output and transforms to utility encoder's input")

    super(UtilityEncoder,self).__init__()

    self.addEncoder(name, inputEncoder)
    self.addEncoder('utility', utilityEncoder)
    
    self._utility = utilityEncoder
    self._encoder = inputEncoder
    self._feval = feval
    self._offset = encoder.width()
    self._parent = super(UtilityEncoder, self)

  def encodeIntoArray(self, input, output)
    """on original input, compute utility and append it as "input" for processing; 
       the feval function is applied before any encoding"""
    score = self._feval(input)
    merged_input = [input, score]
    self._parent.encodeIntoArray(merged_input,output)

  def decode(self, encoded, parentFieldNames=''):
    """takes the extended input from above, and recovers back values for orig input and utility"""
    return self._parent.decode(encoded, parentFieldNames)
  

  ######################################################################
  ## class specific methods: 
  def _appendToInput(input_orig, scode): 
    """appends the score (result of feval(input)) to the original input"""
    if isinstance(input_orig, dict): 
      input_orig["utility"]=score
    elif isinstance(input_orig, list): 
      input_orig.append(score)
    else:
      raise Exception("")    
    
