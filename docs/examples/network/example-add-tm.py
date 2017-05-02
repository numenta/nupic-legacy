tmParams = modelParams["tmParams"]
network.addRegion("TM", "py.TPRegion", json.dumps(tmParams))