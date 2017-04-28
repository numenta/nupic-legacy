import csv
import datetime
import os
import yaml
from itertools import islice

from nupic.frameworks.opf.model_factory import ModelFactory

_NUM_RECORDS = 3000
_EXAMPLE_DIR = os.path.dirname(os.path.abspath(__file__))
_INPUT_FILE_PATH = os.path.join(_EXAMPLE_DIR, os.pardir, "data", "gymdata.csv")
_PARAMS_PATH = os.path.join(_EXAMPLE_DIR, os.pardir, "params", "model.yaml")



def createModel():
  with open(_PARAMS_PATH, "r") as f:
    modelParams = yaml.safe_load(f)
  return ModelFactory.create(modelParams)



def runHotgym(numRecords):
  model = createModel()
  model.enableInference({"predictedField": "consumption"})
  with open(_INPUT_FILE_PATH) as fin:
    reader = csv.reader(fin)
    headers = reader.next()
    reader.next()
    reader.next()

    results = []
    for record in islice(reader, numRecords):
      modelInput = dict(zip(headers, record))
      modelInput["consumption"] = float(modelInput["consumption"])
      modelInput["timestamp"] = datetime.datetime.strptime(
        modelInput["timestamp"], "%m/%d/%y %H:%M")
      result = model.run(modelInput)
      bestPredictions = result.inferences["multiStepBestPredictions"]
      allPredictions = result.inferences["multiStepPredictions"]
      oneStep = bestPredictions[1]
      oneStepConfidence = allPredictions[1][oneStep]
      fiveStep = bestPredictions[5]
      fiveStepConfidence = allPredictions[5][fiveStep]

      result = (oneStep, oneStepConfidence * 100,
                fiveStep, fiveStepConfidence * 100)
      print "1-step: {:16} ({:4.4}%)\t 5-step: {:16} ({:4.4}%)".format(*result)
      results.append(result)
    return results


if __name__ == "__main__":
  runHotgym(_NUM_RECORDS)
