control = {
  # The environment that the current model is being run in
  "environment": $ENVIRONMENT,

  # Input stream specification per py/nupic/frameworks/opf/jsonschema/stream_def.json.
  #
  'dataset' : $DATASET_SPEC,

  # Iteration count: maximum number of iterations.  Each iteration corresponds
  # to one record from the (possibly aggregated) dataset.  The task is
  # terminated when either number of iterations reaches iterationCount or
  # all records in the (possibly aggregated) database have been processed,
  # whichever occurs first.
  #
  # iterationCount of -1 = iterate over the entire dataset
  'iterationCount' : $ITERATION_COUNT,


  # A dictionary containing all the supplementary parameters for inference
  "inferenceArgs":$INFERENCE_ARGS,

  # Metrics: A list of MetricSpecs that instantiate the metrics that are
  # computed for this experiment
  'metrics':[
    $METRICS
  ],

  # Logged Metrics: A sequence of regular expressions that specify which of
  # the metrics from the Inference Specifications section MUST be logged for
  # every prediction. The regex's correspond to the automatically generated
  # metric labels. This is similar to the way the optimization metric is
  # specified in permutations.py.
  'loggedMetrics': $LOGGED_METRICS,
}



descriptionInterface = ExperimentDescriptionAPI(modelConfig=config,
                                                control=control)
