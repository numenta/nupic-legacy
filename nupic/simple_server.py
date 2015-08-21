#! /usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2015, Numenta, Inc.  Unless you have an agreement
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
"""
A simple web server for interacting with NuPIC.
Note: Requires web.py to run (install using '$ pip install web.py')
"""
import os
import sys
# The following loop removes the nupic package from the
# PythonPath (sys.path). This is necessary in order to let web
# import the built in math module rather than defaulting to
# nupic.math
while True:
  try:
    sys.path.remove(os.path.dirname(os.path.realpath(__file__)))
  except:
    break

import datetime
import json
import web

from nupic.frameworks.opf.modelfactory import ModelFactory



g_models = {}



urls = (
    # Web UI
    "/models", "ModelHandler",
    r"/models/([-\w]*)", "ModelHandler",
    r"/models/([-\w]*)/run", "ModelRunner",
)



class ModelHandler(object):

  def GET(self):
    """
    /models

    returns:
    [model1, model2, model3, ...] list of model names
    """
    global g_models
    return json.dumps({"models": g_models.keys()})


  def POST(self, name):
    """
    /models/{name}

    schema:
    {
      "modelParams": dict containing model parameters
      "predictedFieldName": str
    }

    returns:
    {"success":name}
    """
    global g_models

    data = json.loads(web.data())
    modelParams = data["modelParams"]
    predictedFieldName = data["predictedFieldName"]

    if name in g_models.keys():
      raise web.badrequest("Model with name <%s> already exists" % name)

    model = ModelFactory.create(modelParams)
    model.enableInference({'predictedField': predictedFieldName})
    g_models[name] = model

    return json.dumps({"success": name})



class ModelRunner(object):

  def POST(self, name):
    """
    /models/{name}/run

    schema:
      {
        predictedFieldName: value
        timestamp: %m/%d/%y %H:%M
      }
      NOTE: predictedFieldName MUST be the same name specified when
            creating the model.

    returns:
    {
      "predictionNumber":<number of record>,
      "anomalyScore":anomalyScore
    }
    """
    global g_models

    data = json.loads(web.data())
    data["timestamp"] = datetime.datetime.strptime(
        data["timestamp"], "%m/%d/%y %H:%M")

    if name not in g_models.keys():
      raise web.notfound("Model with name <%s> does not exist." % name)

    modelResult = g_models[name].run(data)
    predictionNumber = modelResult.predictionNumber
    anomalyScore = modelResult.inferences["anomalyScore"]

    return json.dumps({"predictionNumber": predictionNumber,
                       "anomalyScore": anomalyScore})



web.config.debug = False
app = web.application(urls, globals())



if __name__ == "__main__":
  app.run()
