
permutations = dict(
                iterationCount      = [50000],
                spPeriodicStats     = [500],
                #encodingFieldStyleA = ['contiguous', 'sdr'],
                #encodingFieldWidthA = [50],
                #encodingFieldWidthB = [50],
                #encodingOnBitsA     = [11],
                #encodingOnBitsB     = [5],
                numAValues          = [2, 10, 25, 50],
                numBValues          = [2, 10, 25, 50],
                b0Likelihood        = [0, 0.90],
                #spSynPermInactiveDec = [0.0, 0.005],
                )


report = ['overallTime',
          '.*classificationSamples.*',
          '.*classificationAccPct.*',
          '.*tpFitnessScore.*',
          '.*outputRepresentationChangePctAvg.*',
          '.*unusedCellsCount.*',
          ]

