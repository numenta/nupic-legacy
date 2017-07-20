# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2014, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Affero Public License for more details.
#
# You should have received a copy of the GNU Affero Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------

"""
Template file used by the OPF Experiment Generator to generate the actual
description.py file by replacing $XXXXXXXX tokens with desired values.
"""

from nupic.frameworks.opf.exp_description_api import ExperimentDescriptionAPI

from nupic.frameworks.opf.exp_description_helpers import (
  updateConfigFromSubConfig,
  applyValueGettersToContainer,
  DeferredDictLookup)

from nupic.frameworks.opf.htm_prediction_model_callbacks import *
from nupic.frameworks.opf.metrics import MetricSpec
from nupic.frameworks.opf.opf_utils import (InferenceType,
                                            InferenceElement)
from nupic.support import aggregationDivide

from nupic.frameworks.opf.opf_task_driver import (
                                            IterationPhaseSpecLearnOnly,
                                            IterationPhaseSpecInferOnly,
                                            IterationPhaseSpecLearnAndInfer)


# Model Configuration Dictionary:
#
# Define the model parameters and adjust for any modifications if imported
# from a sub-experiment.
#
# These fields might be modified by a sub-experiment; this dict is passed
# between the sub-experiment and base experiment
#
#
# NOTE: Use of DEFERRED VALUE-GETTERs: dictionary fields and list elements
#   within the config dictionary may be assigned futures derived from the
#   ValueGetterBase class, such as DeferredDictLookup.
#   This facility is particularly handy for enabling substitution of values in
#   the config dictionary from other values in the config dictionary, which is
#   needed by permutation.py-based experiments. These values will be resolved
#   during the call to applyValueGettersToContainer(),
#   which we call after the base experiment's config dictionary is updated from
#   the sub-experiment. See ValueGetterBase and
#   DeferredDictLookup for more details about value-getters.
#
#   For each custom encoder parameter to be exposed to the sub-experiment/
#   permutation overrides, define a variable in this section, using key names
#   beginning with a single underscore character to avoid collisions with
#   pre-defined keys (e.g., _dsEncoderFieldName2_N).
#
#   Example:
#      config = dict(
#        _dsEncoderFieldName2_N = 70,
#        _dsEncoderFieldName2_W = 5,
#        dsEncoderSchema = [
#          base=dict(
#            fieldname='Name2', type='ScalarEncoder',
#            name='Name2', minval=0, maxval=270, clipInput=True,
#            n=DeferredDictLookup('_dsEncoderFieldName2_N'),
#            w=DeferredDictLookup('_dsEncoderFieldName2_W')),
#        ],
#      )
#      updateConfigFromSubConfig(config)
#      applyValueGettersToContainer(config)
config = {
    # Type of model that the rest of these parameters apply to.
    'model': "HTMPrediction",

    # Version that specifies the format of the config.
    'version': 1,

    # Intermediate variables used to compute fields in modelParams and also
    # referenced from the control section.
    'aggregationInfo': {   'fields': [   ('numericFieldNameA', 'mean'),
                      ('numericFieldNameB', 'sum'),
                      ('categoryFieldNameC', 'first')],
        'hours': 0},

    'predictAheadTime': None,

    # Model parameter dictionary.
    'modelParams': {
        # The type of inference that this model will perform
        'inferenceType': 'TemporalNextStep',

        'sensorParams': {
            # Sensor diagnostic output verbosity control;
            # if > 0: sensor region will print out on screen what it's sensing
            # at each step 0: silent; >=1: some info; >=2: more info;
            # >=3: even more info (see compute() in py/regions/RecordSensor.py)
            'verbosity' : 0,

            # Example:
            #     dsEncoderSchema = [
            #       DeferredDictLookup('__field_name_encoder'),
            #     ],
            #
            # (value generated from DS_ENCODER_SCHEMA)
            'encoders': {
              'timestamp': dict(fieldname='timestamp', type='DateEncoder',timeOfDay=(5,5)),
              'attendeeCount': dict(fieldname='attendeeCount', type='ScalarEncoder',
                name='attendeeCount', minval=0, maxval=270,
                clipInput=True, w=5, resolution=10, forced=True),
              'consumption': dict(fieldname='consumption',type='ScalarEncoder',
                name='consumption', minval=0,maxval=115,
                clipInput=True, w=5, resolution=5, forced=True),
            },

            # A dictionary specifying the period for automatically-generated
            # resets from a RecordSensor;
            #
            # None = disable automatically-generated resets (also disabled if
            # all of the specified values evaluate to 0).
            # Valid keys is the desired combination of the following:
            #   days, hours, minutes, seconds, milliseconds, microseconds, weeks
            #
            # Example for 1.5 days: sensorAutoReset = dict(days=1,hours=12),
            #
            # (value generated from SENSOR_AUTO_RESET)
            'sensorAutoReset' : None,
        },

        'spEnable': True,

        'spParams': {
            # SP diagnostic output verbosity control;
            # 0: silent; >=1: some info; >=2: more info;
            'spVerbosity' : 0,

            'globalInhibition': 1,

            # Number of cell columns in the cortical region (same number for
            # SP and TM)
            # (see also tpNCellsPerCol)
            'columnCount': 2048,

            'inputWidth': 0,

            # SP inhibition control (absolute value);
            # Maximum number of active columns in the SP region's output (when
            # there are more, the weaker ones are suppressed)
            'numActiveColumnsPerInhArea': 20,

            'seed': 1956,

            # potentialPct
            # What percent of the columns's receptive field is available
            # for potential synapses. At initialization time, we will
            # choose potentialPct * (2*potentialRadius+1)^2
            'potentialPct': 0.5,

            # The default connected threshold. Any synapse whose
            # permanence value is above the connected threshold is
            # a "connected synapse", meaning it can contribute to the
            # cell's firing. Typical value is 0.10. Cells whose activity
            # level before inhibition falls below minDutyCycleBeforeInh
            # will have their own internal synPermConnectedCell
            # threshold set below this default value.
            # (This concept applies to both SP and TM and so 'cells'
            # is correct here as opposed to 'columns')
            'synPermConnected': 0.1,

            'synPermActiveInc': 0.1,

            'synPermInactiveDec': 0.01,
        },

        # Controls whether TM is enabled or disabled;
        # TM is necessary for making temporal predictions, such as predicting
        # the next inputs.  Without TM, the model is only capable of
        # reconstructing missing sensor inputs (via SP).
        'tmEnable' : True,

        'tmParams': {
            # TM diagnostic output verbosity control;
            # 0: silent; [1..6]: increasing levels of verbosity
            # (see verbosity in nupic/trunk/py/nupic/research/backtracking_tm.py and backtracking_tm_cpp.py)
            'verbosity': 0,

            # Number of cell columns in the cortical region (same number for
            # SP and TM)
            # (see also tpNCellsPerCol)
            'columnCount': 2048,

            # The number of cells (i.e., states), allocated per column.
            'cellsPerColumn': 8,

            'inputWidth': 2048,

            'seed': 1960,

            # Temporal Pooler implementation selector (see _getTPClass in
            # CLARegion.py).
            'temporalImp': 'cpp',

            # New Synapse formation count
            # NOTE: If None, use spNumActivePerInhArea
            #
            # TODO: need better explanation
            'newSynapseCount': 15,

            # Maximum number of synapses per segment
            #  > 0 for fixed-size CLA
            # -1 for non-fixed-size CLA
            #
            # TODO: for Ron: once the appropriate value is placed in TM
            # constructor, see if we should eliminate this parameter from
            # description.py.
            'maxSynapsesPerSegment': 32,

            # Maximum number of segments per cell
            #  > 0 for fixed-size CLA
            # -1 for non-fixed-size CLA
            #
            # TODO: for Ron: once the appropriate value is placed in TM
            # constructor, see if we should eliminate this parameter from
            # description.py.
            'maxSegmentsPerCell': 128,

            # Initial Permanence
            # TODO: need better explanation
            'initialPerm': 0.21,

            # Permanence Increment
            'permanenceInc': 0.1,

            # Permanence Decrement
            # If set to None, will automatically default to tpPermanenceInc
            # value.
            'permanenceDec' : 0.1,

            'globalDecay': 0.0,

            'maxAge': 0,

            # Minimum number of active synapses for a segment to be considered
            # during search for the best-matching segments.
            # None=use default
            # Replaces: tpMinThreshold
            'minThreshold': 12,

            # Segment activation threshold.
            # A segment is active if it has >= tpSegmentActivationThreshold
            # connected synapses that are active due to infActiveState
            # None=use default
            # Replaces: tpActivationThreshold
            'activationThreshold': float("nan"),

            'outputType': 'normal',

            # "Pay Attention Mode" length. This tells the TM how many new
            # elements to append to the end of a learned sequence at a time.
            # Smaller values are better for datasets with short sequences,
            # higher values are better for datasets with long sequences.
            'pamLength': 1,
        },

        'clParams': {
            'regionName' : 'SDRClassifierRegion',

            # Classifier diagnostic output verbosity control;
            # 0: silent; [1..6]: increasing levels of verbosity
            'verbosity' : 0,

            # This controls how fast the classifier learns/forgets. Higher values
            # make it adapt faster and forget older patterns faster.
            'alpha': 0.001,

            # This is set after the call to updateConfigFromSubConfig and is
            # computed from the aggregationInfo and predictAheadTime.
            'steps': '1',


        },

        'trainSPNetOnlyIfRequested': False,
    },


}
# end of config dictionary


# Adjust base config dictionary for any modifications if imported from a
# sub-experiment
updateConfigFromSubConfig(config)


# Compute predictionSteps based on the predictAheadTime and the aggregation
# period, which may be permuted over.
if config['predictAheadTime'] is not None:
  predictionSteps = int(round(aggregationDivide(
      config['predictAheadTime'], config['aggregationInfo'])))
  assert (predictionSteps >= 1)
  config['modelParams']['clParams']['steps'] = str(predictionSteps)


# Adjust config by applying ValueGetterBase-derived
# futures. NOTE: this MUST be called after updateConfigFromSubConfig() in order
# to support value-getter-based substitutions from the sub-experiment (if any)
applyValueGettersToContainer(config)



control = dict(

  environment = 'opfExperiment',

# [optional] A sequence of one or more tasks that describe what to do with the
# model. Each task consists of a task label, an input spec., iteration count,
# and a task-control spec per opfTaskSchema.json
#
# NOTE: The tasks are intended for OPF clients that make use of OPFTaskDriver.
#       Clients that interact with OPFExperiment directly do not make use of
#       the tasks specification.
#
  tasks = [
    {
      # Task label; this label string may be used for diagnostic logging and for
      # constructing filenames or directory pathnames for task-specific files, etc.
      'taskLabel' : "OnlineLearning",

      # Input stream specification per py/nupicengine/cluster/database/StreamDef.json.
      #
      'dataset' : {
        'info': 'test_NoProviders',
        'version': 1,

        'streams': [
          {
            'columns': ['*'],
            'info': 'my gym.csv dataset',
            'source': 'file://extra/gym/gym.csv',
            'first_record': 0,
            'last_record': 4000
          }
        ],

        # TODO: Aggregation is not supported yet by run_opf_experiment.py
        #'aggregation' : config['aggregationInfo']
      },

      # Iteration count: maximum number of iterations.  Each iteration corresponds
      # to one record from the (possibly aggregated) dataset.  The task is
      # terminated when either number of iterations reaches iterationCount or
      # all records in the (possibly aggregated) database have been processed,
      # whichever occurs first.
      #
      # iterationCount of -1 = iterate over the entire dataset
      'iterationCount' : -1,


      # Task Control parameters for OPFTaskDriver (per opfTaskControlSchema.json)
      'taskControl' : {

        # Iteration cycle list consisting of opf_task_driver.IterationPhaseSpecXXXXX
        # instances.
        'iterationCycle' : [
          #IterationPhaseSpecLearnOnly(1000),
          IterationPhaseSpecLearnAndInfer(1000, dict(predictedField="consumption")),
          #IterationPhaseSpecInferOnly(10),
        ],

        'metrics' :[
          MetricSpec(metric='rmse',
                     field="consumption",
                     inferenceElement=InferenceElement.prediction),
        ],

        # Callbacks for experimentation/research (optional)
        'callbacks' : {
          # Callbacks to be called at the beginning of a task, before model iterations.
          # Signature: callback(<reference to OPFExperiment>); returns nothing
          'setup' : [],

          # Callbacks to be called after every learning/inference iteration
          # Signature: callback(<reference to OPFExperiment>); returns nothing
          'postIter' : [],

          # Callbacks to be called when the experiment task is finished
          # Signature: callback(<reference to OPFExperiment>); returns nothing
          'finish' : []
        }
      } # End of taskControl
    }, # End of task
  ]
)



descriptionInterface = ExperimentDescriptionAPI(modelConfig=config,
                                                control=control)
