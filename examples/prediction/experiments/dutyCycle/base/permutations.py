
permutations = dict(
                iterationCount      = [50000],
                spPeriodicStats     = [0],
                #spCoincCount = [200, 300, 400, 500],
                #spNumActivePerInhArea = [3, 5, 7, 9, 11],
                spSynPermInactiveDec = [0.005, 0.01, 0.02, 0.04],
                )


report = ['overallTime',
          '.*classificationSamples.*',
          '.*classificationAccPct.*',
          '.*tpFitnessScore.*',
          '.*outputRepresentationChangePctAvg.*',
          '.*unusedCellsCount.*',
          ]
