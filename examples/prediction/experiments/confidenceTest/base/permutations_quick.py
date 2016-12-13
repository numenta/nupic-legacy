
permutations = dict(
                dataSetPackage = ['secondOrder1'],

                iterationCountTrain = [10, 25, 50, 100],
                iterationCountTest = [150],
                evalTrainingSetNumIterations = [0],
                
                spNumActivePerInhArea = [5],
                
                temporalImp = ['py'],
                tpNCellsPerCol = [4], 

                tpInitialPerm = [0.11, 0.31, 0.51],
                tpPermanenceInc = [0.10],
                tpGlobalDecay = [0.10],
                tpMaxAge = [1, 3, 5, 7, 15],   
                )

report = ['overallTime',
          'postProc_confidenceTest_baseline:inputPredScore_burnIn1',
          ]
          
optimize = 'postProc_confidenceTest_baseline:inputPredScore_burnIn1'



