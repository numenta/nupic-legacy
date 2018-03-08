tmParams = modelParams["tmParams"]
network.addRegion("TM", "py.TMRegion", json.dumps(tmParams))