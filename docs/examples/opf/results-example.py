result = model.run(modelInput)
bestPredictions = result.inferences['multiStepBestPredictions']
allPredictions = result.inferences['multiStepPredictions']
oneStep = bestPredictions[1]
fiveStep = bestPredictions[5]
# Confidence values are keyed by prediction value in multiStepPredictions.
oneStepConfidence = allPredictions[1][oneStep]
fiveStepConfidence = allPredictions[5][fiveStep]

result = (oneStep, oneStepConfidence * 100,
          fiveStep, fiveStepConfidence * 100)
print "1-step: {:16} ({:4.4}%)\t 5-step: {:16} ({:4.4}%)".format(*result)
