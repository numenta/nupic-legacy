
permutations = dict(
                dataSetPackage = ['firstOrder'],

                iterationCountTest = [1000],

                spNumActivePerInhArea = [1],
                
                tpNCellsPerCol = [1],
                
                tpInitialPerm = [0.11],
                tpPermanenceInc = [0.10],
                tpGlobalDecay = [0.10],
                tpMaxAge = [5, 10, 20, 50, 100],   
                tpPAMLength = [1],
                )

report = ['overallTime',
          '.*:inputPredScore_burnIn1',
          '.*:ngram:inputPredScore_n1_burnIn1',
          ]
          
optimize = 'postProc_confidenceTest_baseline:inputPredScore_burnIn1'

