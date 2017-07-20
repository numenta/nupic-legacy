
permutations = dict(
                iterationCount      = [50000],
                spPeriodicStats     = [0],
                #encodingFieldStyleA = ['contiguous', 'sdr'],
                encodingFieldWidthA = [256],
                encodingFieldWidthB = [256],
                
                encodingOnBitsA     = [5, 7, 9] + range(11, 40, 4) + range(43, 100, 8),
                encodingOnBitsB     = [5, 7, 9] + range(11, 40, 4) + range(43, 100, 8),
                
                numAValues          = [25],
                numBValues          = [25],
                b0Likelihood        = [0],
                
                #spSynPermInactiveDec = [0.0, 0.005],
                )


report = ['overallTime',
          '.*classificationSamples.*',
          '.*classificationAccPct.*',
          '.*tpFitnessScore.*',
          ]

