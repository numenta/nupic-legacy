
permutations = dict(
                dataSetPackage = ['secondOrder0'],

                iterationCountTrain = [250, 500, 1000, 1500],
                iterationCountTest = [250, 500],
                
                spNumActivePerInhArea = [5],
                
                tpNCellsPerCol = [5], 

                tpInitialPerm = [0.11, 0.21, 0.31, 0.41],
                tpPermanenceInc = [0.05, 0.10],
                tpGlobalDecay = [0.05, 0.10],
                tpMaxAge = [50, 75, 100, 200, 300],   
                )

report = ['overallTime',
          'postProc_confidenceTest_baseline:inputPredScore_burnIn1',
          'postProc_confidenceTest_baseline:ngram:inputPredScore_n2_burnIn1',
          ]
          
optimize = 'postProc_confidenceTest_baseline:inputPredScore_burnIn1'



def filter(perm):
  """ This function can be used to selectively filter out specific permutation
  combinations. It is called for every possible permutation of the variables
  in the permutations dict. It should return True for valid a combination of 
  permutation values and False for an invalid one. 
  
  Parameters:
  ---------------------------------------------------------
  perm: dict of one possible combination of name:value 
                pairs chosen from permutations.
  """
  
  
  if perm['tpPermanenceInc'] != perm['tpGlobalDecay']:
    return False
    
  return True
  
          


