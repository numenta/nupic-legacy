from nupic.engine import Network
from nupic.regions.AnomalyLikelihoodRegion import AnomalyLikelihoodRegion
import json

# Config field for TPRegion
TP_PARAMS = {
    "anomalyMode": 1,
    "verbosity": 0,
    "columnCount": 2048,
    "cellsPerColumn": 32,
    "inputWidth": 2048,
    "seed": 1960,
    "temporalImp": "cpp",
    "newSynapseCount": 20,
    "maxSynapsesPerSegment": 32,
    "maxSegmentsPerCell": 128,
    "initialPerm": 0.21,
    "permanenceInc": 0.1,
    "permanenceDec": 0.1,
    "globalDecay": 0.0,
    "maxAge": 0,
    "minThreshold": 9,
    "activationThreshold": 12,
    "outputType": "normal",
    "pamLength": 3,
}

SP_PARAMS = {
    "spVerbosity": _VERBOSITY,
    "spatialImp": "cpp",
    "globalInhibition": 1,
    "columnCount": 2048,
    # This must be set before creating the SPRegion
    "inputWidth": 0,
    "numActiveColumnsPerInhArea": 40,
    "seed": 1956,
    "potentialPct": 0.8,
    "synPermConnected": 0.1,
    "synPermActiveInc": 0.0001,
    "synPermInactiveDec": 0.0005,
    "maxBoost": 1.0,
}


n = Network()

n.addRegion("tpRegion", "py.TPRegion", json.dumps(TP_PARAMS))
n.addRegion("anomaly", "py.AnomalyLikelihoodRegion", json.dumps({}))

