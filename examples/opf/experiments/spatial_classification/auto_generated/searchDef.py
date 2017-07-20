# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Affero Public License for more details.
#
# You should have received a copy of the GNU Affero Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------


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
