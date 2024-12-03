# Copyright 2013 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.


import os
  


def getSearch(rootDir):
  """ This method returns search description. See the following file for the
  schema of the dictionary this method returns:
    py/nupic/swarming/exp_generator/experimentDescriptionSchema.json
    
  The streamDef element defines the stream for this model. The schema for this
  element can be found at:
    py/nupicengine/cluster/database/StreamDef.json
    
  """
  
  # Form the stream definition
  dataPath = os.path.abspath(os.path.join(rootDir, 'datasets', 'scalar_1.csv'))
  streamDef = dict(
    version = 1, 
    info = "testSpatialClassification",
    streams = [
      dict(source="file://%s" % (dataPath), 
           info="scalar_1.csv",  
           columns=["*"],
           ),
      ],
  )

  # Generate the experiment description
  expDesc = {
    "environment": 'nupic',
    "inferenceArgs":{
      "predictedField":"classification",
      "predictionSteps": [0],
    },
    "inferenceType":  "MultiStep",
    "streamDef": streamDef,
    "includedFields": [
      { "fieldName": "field1",
        "fieldType": "float",
      },
      { "fieldName": "classification",
        "fieldType": "string",
      },
      { "fieldName": "randomData",
        "fieldType": "float",
      },
    ],
    "iterationCount": -1,
  }
  
  
  return expDesc
