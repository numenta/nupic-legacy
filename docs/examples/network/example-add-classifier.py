clParams = modelParams["clParams"]
network.addRegion("classifier", "py.SDRClassifierRegion", json.dumps(clParams))