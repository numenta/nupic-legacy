import csv
import datetime
from itertools import islice

from nupic.frameworks.opf.modelfactory import ModelFactory

import model_params

_NUM_RECORDS = 3000
_INPUT_FILE_PATH = "../data/gymdata.csv"

def createModel():
  return ModelFactory.create(model_params.MODEL_PARAMS)

def runHotgym():
  model = createModel()
  model.enableInference({'predictedField': 'consumption'})
  with open (_INPUT_FILE_PATH) as fin:
    reader = csv.reader(fin)
    headers = reader.next()
    reader.next()
    reader.next()
    for record in islice(reader, _NUM_RECORDS):
      modelInput = dict(zip(headers, record))
      modelInput["consumption"] = float(modelInput["consumption"])
      modelInput["timestamp"] = datetime.datetime.strptime(
          modelInput["timestamp"], "%m/%d/%y %H:%M")
      result = model.run(modelInput)
      bestPredictions = result.inferences['multiStepBestPredictions']
      allPredictions = result.inferences['multiStepPredictions']
      oneStep = bestPredictions[1]
      oneStepConfidence = allPredictions[1][oneStep]
      fiveStep = bestPredictions[5]
      fiveStepConfidence = allPredictions[5][fiveStep]

      print("1-step: {:16} ({:4.4}%)\t5-step: {:16} ({:4.4}%)".format(oneStep, oneStepConfidence*100, fiveStep, fiveStepConfidence*100))



if __name__ == "__main__":
  runHotgym()
