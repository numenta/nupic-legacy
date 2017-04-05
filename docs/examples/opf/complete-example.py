import csv
import datetime
import yaml
from itertools import islice

from nupic.frameworks.opf.modelfactory import ModelFactory

_NUM_RECORDS = 3000
_INPUT_FILE_PATH = '../data/gymdata.csv'
_PARAMS_PATH = '../params/model.yaml'
_OUTPUT_FILE_PATH = 'predictions.csv'

def createModel():
  with open(_PARAMS_PATH, 'r') as f:
    model_params = yaml.safe_load(f)
  return ModelFactory.create(model_params)

def runHotgym():
  model = createModel()
  model.enableInference({'predictedField': 'consumption'})
  with open (_INPUT_FILE_PATH) as fin:
    with open(_OUTPUT_FILE_PATH, 'w') as of:

      reader = csv.reader(fin)
      headers = reader.next()
      reader.next()
      reader.next()

      writer = csv.writer(of)
      writer.writerow(['input', 'prediction', 'confidence'])

      for record in islice(reader, _NUM_RECORDS):
        modelInput = dict(zip(headers, record))
        modelInput['consumption'] = float(modelInput['consumption'])
        modelInput['timestamp'] = datetime.datetime.strptime(
            modelInput['timestamp'], '%m/%d/%y %H:%M')
        result = model.run(modelInput)
        bestPredictions = result.inferences['multiStepBestPredictions']
        allPredictions = result.inferences['multiStepPredictions']
        oneStep = bestPredictions[1]
        oneStepConfidence = allPredictions[1][oneStep]
        fiveStep = bestPredictions[5]
        fiveStepConfidence = allPredictions[5][fiveStep]

        writer.writerow(['%.5f' % modelInput['consumption'],
                         '%.5f' % oneStep,
                         '%.5f' % oneStepConfidence])
        print('1-step: {:16} ({:4.4}%)\t'
              '5-step: {:16} ({:4.4}%)'.format(oneStep,
                                               oneStepConfidence*100,
                                               fiveStep,
                                               fiveStepConfidence*100))

if __name__ == '__main__':
  runHotgym()
