# Get the bucket info for this input value for classification.
bucketIdx = scalarEncoder.getBucketIndices(consumption)[0]

# Run classifier to translate active cells back to scalar value.
classifierResult = classifier.compute(
  recordNum=count,
  patternNZ=activeCells,
  classification={
    "bucketIdx": bucketIdx,
    "actValue": consumption
  },
  learn=True,
  infer=True
)

# Print the best prediction for 1 step out.
probability, value = sorted(
  zip(classifierResult[1], classifierResult["actualValues"]),
  reverse=True
)[0]
print("1-step: {:16} ({:4.4}%)".format(value, probability * 100))
