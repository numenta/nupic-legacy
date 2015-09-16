
control = {
  # The environment that the current model is being run in
  "environment": $ENVIRONMENT,

  # [optional] A sequence of one or more tasks that describe what to do with the
  # model. Each task consists of a task label, an input spec., iteration count,
  # and a task-control spec per opfTaskSchema.json
  #
  # NOTE: The tasks are intended for OPF clients that make use of OPFTaskDriver.
  #       Clients that interact with OPF Model directly do not make use of
  #       the tasks specification.
  #
  "tasks":[
    {
      # Task label; this label string may be used for diagnostic logging and for
      # constructing filenames or directory pathnames for task-specific files, etc.
      'taskLabel' : "OnlineLearning",


      # Input stream specification per
      # py/nupic/frameworks/opf/jsonschema/stream_def.json.
      'dataset' : $DATASET_SPEC,

      # Iteration count: maximum number of iterations.  Each iteration corresponds
      # to one record from the (possibly aggregated) dataset.  The task is
      # terminated when either number of iterations reaches iterationCount or
      # all records in the (possibly aggregated) database have been processed,
      # whichever occurs first.
      #
      # iterationCount of -1 = iterate over the entire dataset
      'iterationCount' : $ITERATION_COUNT,


      # Task Control parameters for OPFTaskDriver (per opfTaskControlSchema.json)
      'taskControl' : {

        # Iteration cycle list consisting of opftaskdriver.IterationPhaseSpecXXXXX
        # instances.
        'iterationCycle' : [
          #IterationPhaseSpecLearnOnly(1000),
          IterationPhaseSpecLearnAndInfer(1000, inferenceArgs=$INFERENCE_ARGS),
          #IterationPhaseSpecInferOnly(10),
        ],

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

        # Callbacks for experimentation/research (optional)
        'callbacks' : {
          # Callbacks to be called at the beginning of a task, before model iterations.
          # Signature: callback(<reference to OPF Model>); returns nothing
          'setup' : [],

          # Callbacks to be called after every learning/inference iteration
          # Signature: callback(<reference to OPF Model>); returns nothing
          'postIter' : [],

          # Callbacks to be called when the experiment task is finished
          # Signature: callback(<reference to OPF Model>); returns nothing
          'finish' : []
        }
      } # End of taskControl
    }, # End of task

  ]
}



descriptionInterface = ExperimentDescriptionAPI(modelConfig=config,
                                                control=control)
