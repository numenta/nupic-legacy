
permutations = dict(
                iterationCount      = [25000],
                spPeriodicStats     = [0],
                #spCoincCount = [200, 300, 400, 500],
                spNumActivePerInhArea = [9, 11, 13, 15, 17],
                tpActivationThresholds = [range(8,18)], 
                #spSynPermInactiveDec = [0.005, 0.01, 0.02, 0.04],
                )


report = ['overallTime',
          '.*classificationSamples.*',
          '.*classificationAccPct.*',
          '.*tpFitnessScore.*',
          ]
