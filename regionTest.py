from nupic.engine import Network
from nupic.algorithms.anomaly_likelihood import AnomalyLikelihood
import json

with open('myout', 'r') as f:
  read_data = f.read()

records = read_data.split('\n')

anomaly = AnomalyLikelihood()
for record in records:
  record = record.split(',')
  print "{},{}".format(float(record[2]), 
    anomaly.anomalyProbability(float(record[1]), float(record[2])))

# n.addRegion("tpRegion", "py.TPRegion", json.dumps(TP_PARAMS))
# n.addRegion("anomaly", "py.AnomalyLikelihoodRegion", json.dumps({}))

