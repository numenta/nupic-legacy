#! /usr/bin/env python
# ----------------------------------------------------------------------
#  Copyright (C) 2006,2007,2010 Numenta Inc. All rights reserved.
#
#  The information and source code contained herein is the
#  exclusive property of Numenta Inc. No part of this software
#  may be used, reproduced, stored or distributed in any form,
#  without explicit written authorization from Numenta Inc.
# ----------------------------------------------------------------------
#


import os
  

###############################################################################
def getSearch(rootDir):
  """ This method returns search description. See the following file for the
  schema of the dictionary this method returns:
    py/grokengine/frameworks/opf/expGenerator/experimentDescriptionSchema.json
    
  The streamDef element defines the stream for this model. The schema for this
  element can be found at:
    py/grokengine/cluster/database/StreamDef.json
    
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
    "environment": 'grok',
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
