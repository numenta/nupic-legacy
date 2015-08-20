# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
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
This script is a template for OPF description.py experiment description scripts.

Workflow: to create a new OPF description.py, start by branching this
template in source control. Branching via source control may make it easier to
integrate future template improvements into your description.py.
"""

from nupic.frameworks.opf.expdescriptionapi import ExperimentDescriptionAPI

from nupic.frameworks.opf.expdescriptionhelpers import (
  updateConfigFromSubConfig,
  applyValueGettersToContainer,
  DeferredDictLookup)

from nupic.frameworks.opf.predictionmetricsmanager import MetricSpec

from nupic.frameworks.opf.opftaskdriver import (
                                            IterationPhaseSpecLearnOnly,
                                            IterationPhaseSpecInferOnly,
                                            IterationPhaseSpecLearnAndInfer,
                                            InferenceSpecNonTemporal,
                                            InferenceSpecTemporal
                                            )




# ------------------------------------------------------------------------------
# Model Configuration Dictionary:
#
# Define the model parameters and adjust for any modifications if imported
# from a sub-experiment.
#
# These fields might be modified by a sub-experiment; this dict is passed between
# the sub-experiment and base experiment
#
#
# NOTE: Use of DEFERRED VALUE-GETTERs: dictionary fields and list elements
#   within the config dictionary may be assigned futures derived from the
#   ValueGetterBase class, such as DeferredDictLookup. This facility is
#   particularly handy for enabling substitution of values in the config
#   dictionary from other values in the config dictionary, which is needed by
#   permutation.py-based experiments. These values will be resolved during the
#   call to applyValueGettersToContainer(), which we call after the base
#   experiment's config dictionary is updated from the sub-experiment. See
#   ValueGetterBase and DeferredDictLookup for more details about value-getters.
#
#   For each custom encoder parameter to be exposed to sub-experiment/permutation
#   overrides, define a variable in this section, using key names beginning with a
#   single underscore character to avoid collisions with pre-defined keys (e.g.,
#   _dsEncoderFieldName2_N).
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
#

config = {
  
  # Type of model that the rest of these parameters apply to
  'model' : "CLA",


  ##############################################################################
  # Dataset Aggregation Parameters (for training and inference datasets)
  ##############################################################################

  # Time-based Dataset Aggregation rules;
  #
  # Usage details and additional options: see
  # nupic.data.aggregator.generateDataset()
  #
  # Aggregation presently begins at the start of the dataset. For every
  # aggregation period, the records within the period are coalesced into a
  # single record per rules specified via the aggregationInfo property.
  #
  # Value schema:
  #   {
  #     'periodUnit1':value1, 'periodUnit2':value2, ...,
  #     'fields':[('fieldNameA', aggFuncNameA), ('fieldNameB', aggFuncNameB)]
  #   }
  #
  # Aggregation period units: combination of 0 or more unit/value properties:
  #   [years months] | [weeks days hours minutes seconds milliseconds microseconds]
  # NOTE: years and months are mutually-exclusive with the other units.
  # Example2: hours=1, minutes=30,
  #
  # Aggregation is disabled if the aggregationInfo key is omitted or all
  # expressed period unit values evaluate to 0
  #
  # Aggregation fields: list of field-name/aggregationFunctionName tuples;
  # e.g.: ("consumpion", "mean").
  #
  # Supported function names: "first", "last", "mean", "sum" (per
  # nupic.data.aggregator.py)
  #
  # NOTE: Designated Sequence id, Reset, and Timestamp fields are included
  #      automatically if not specified in aggregation fields.
  #
  # Aggregation period can be permuted over, so is separated out
  # (generated from AGGREGATION_PERIOD)
  '__aggregationPeriod' : {   'days': 0,
    'hours': 0,
    'microseconds': 0,
    'milliseconds': 0,
    'minutes': 0,
    'months': 0,
    'seconds': 0,
    'weeks': 0,
    'years': 0},
  # (value generated from AGGREGATION_INFO)
  'aggregationInfo' : {
    'years': DeferredDictLookup('__aggregationPeriod', 'years'),
    'months': DeferredDictLookup('__aggregationPeriod', 'months'),
    'weeks': DeferredDictLookup('__aggregationPeriod', 'weeks'),
    'days': DeferredDictLookup('__aggregationPeriod', 'days'),
    'hours': DeferredDictLookup('__aggregationPeriod', 'hours'),
    'minutes': DeferredDictLookup('__aggregationPeriod', 'minutes'),
    'seconds': DeferredDictLookup('__aggregationPeriod', 'seconds'),
    'milliseconds': DeferredDictLookup('__aggregationPeriod', 'milliseconds'),
    'microseconds': DeferredDictLookup('__aggregationPeriod', 'microseconds'),
    'fields' : [
      # fieldname : aggregation function name
      ('numericFieldNameA', 'mean'),
      ('numericFieldNameB', 'sum'),
      ('categoryFieldNameC', 'first')
    ],
  },


  ##############################################################################
  # Sensor Region Parameters
  ##############################################################################

  # Sensor diagnostic output verbosity control;
  # if > 0: sensor region will print out on screen what it's sensing at each step
  # 0: silent; >=1: some info; >=2: more info; >=3: even more info
  # (see compute() in py/regions/RecordSensor.py)
  #
  'sensorVerbosity' : 0,

  # A dictionary specifying the period for automatically-generated resets from
  # a RecordSensor;
  #
  # None = disable automatically-generated resets (also disabled if all of the
  # specified values evaluate to 0).
  # Valid keys is the desired combination of the following:
  #   days, hours, minutes, seconds, milliseconds, microseconds, weeks
  #
  # Example for 1.5 days: sensorAutoReset = dict(days=1,hours=12),
  #
  'sensorAutoReset' : None,


  # Dataset Encoder consists of field encoders that convert dataset record fields
  # to the internal representations suitable for input to the Sensor Region.
  #
  # Each field encoder dict must have the following keys per
  # nupic.encoders.MultiEncoder (multi.py):
  #  1) data fieldname          ('fieldname')
  #  2) an encoder type         ('type')
  #  3) and the encoder params  (all other keys)
  #
  # See specific encoder modules (e.g., sdrcateogry.py, scalar.py,
  # date.py, etc.) for encoder type values and descriptions of their specific params.
  #
  # Schema that describes how to build the encoder configuration.
  #
  #   dsEncoderSchema: [encoderSpec1, encoderSpec2, ...]
  #   encoderSpec: dictionary of parameters describing the field encoder
  #
  # In this dsEncoderSchema example, the field name "Name1" is a timestamp,
  # "Name2" is a scalar quantity, and "Name3" is a category
  #
  'dsEncoderSchema' : [
    dict(fieldname='Name1', type='DateEncoder', timeOfDay=(5,5)),
    dict(fieldname='Name2', type='ScalarEncoder',
         name='Name2', minval=0, maxval=270, clipInput=True,
         n=70, w=5),
    dict(fieldname='Name3', type='SDRCategoryEncoder', name="Name3",
         n=DeferredDictLookup('claRegionNColumns'),
         w=DeferredDictLookup('spNumActivePerInhArea')),
  ],

  
  ##############################################################################
  # General CLA Region Parameters
  ##############################################################################

  # Number of cell columns in the cortical region (same number for SP and TP)
  # (see also tpNCellsPerCol)
  # Replaces: spCoincCount
  'claRegionNColumns' : 2048,
  

  ##############################################################################
  # Spatial Pooler (SP) Parameters (SP is always enabled in OPF)
  ##############################################################################

  # SP diagnostic output verbosity control;
  # 0: silent; >=1: some info; >=2: more info;
  #
  'spVerbosity' : 0,

  # Print/logs stats every N iterations; 0 = disable stats
  'spPrintStatsPeriodIter' : 0,

  # SP inhibition control (absolute value);
  # Maximum number of active columns in the SP region's output (when there are more,
  # the weaker ones are suppressed)
  #
  'spNumActivePerInhArea' : 40,

  # potentialPct
  # What percent of the columns's receptive field is available
  # for potential synapses. At initialization time, we will 
  # choose potentialPct * (2*potentialRadius+1)^2 
  'spCoincInputPoolPct' : 1.0,
  

  ##############################################################################
  # Temporal Pooler (TP) Parameters
  ##############################################################################

  # TP diagnostic output verbosity control;
  # 0: silent; [1..6]: increasing levels of verbosity
  # (see verbosity in nupic/trunk/py/nupic/research/TP.py and TP10X*.py)
  #
  'tpVerbosity' : 0,

  # Print stats every N iterations during training; 0 = disable stats
  # TODO Why aren't experiments configuring stats for the inference phase? It seems
  #   like SP stats are dumped by SP Pooler directly regardless of whether it's
  #   in training or inference phase.  (waiting for email from Ron)
  # TODO: In LPF, these were accumulated/printed via iter/final callbacks installed
  #       by LPF; solve in OPF.
  'tpTrainPrintStatsPeriodIter' : 0,

  # Controls whether TP is enabled or disabled;
  # TP is necessary for making temporal predictions, such as predicting the next
  # inputs.  Without TP, the model is only capable of reconstructing missing sensor
  # inputs (via SP).
  #
  'tpEnable' : True,
  
  # The number of cells (i.e., states), allocated per column
  #
  'tpNCellsPerCol' : 32,
  
  # Initial Permanence
  # TODO need better explanation
  #
  'tpInitialPerm' : 0.21,
  
  # Permanence Increment
  #
  'tpPermanenceInc' : 0.1,

  # Permanence Decrement
  # If set to None, will automatically default to tpPermanenceInc value
  #
  'tpPermanenceDec' : None,
  
  # Temporal Pooler implementation selector (see _getTPClass in CLARegion.py)
  #
  'tpImplementation' : 'cpp',

  # Maximum number of segments per cell
  #  > 0 for fixed-size CLA
  # -1 for non-fixed-size CLA
  #
  # TODO for Ron: once the appropriate value is placed in TP constructor, see if
  #  we should eliminate this parameter from description.py
  #
  'tpMaxSegmentsPerCell' : 128,
  
  # Segment activation threshold.
  # A segment is active if it has >= tpSegmentActivationThreshold connected
  # synapses that are active due to infActiveState
  # None=use default
  # Replaces: tpActivationThreshold
  'tpSegmentActivationThreshold' : None,

  # Minimum number of active synapses for a segment to be considered during
  # search for the best-matching segments.
  # None=use default
  # Replaces: tpMinThreshold
  'tpMinSegmentMatchSynapseThreshold' : None,
  
  # Maximum number of synapses per segment
  #  > 0 for fixed-size CLA
  # -1 for non-fixed-size CLA
  #
  # TODO for Ron: once the appropriate value is placed in TP constructor, see if
  #  we should eliminate this parameter from description.py
  #
  'tpMaxSynapsesPerSegment' : 32,
  
  # New Synapse formation count
  # NOTE: If None, use spNumActivePerInhArea
  #
  # TODO need better explanation
  #
  'tpNewSynapseCount' : 15,

}
# end of config dictionary


# Adjust base config dictionary for any modifications if imported from a
# sub-experiment
updateConfigFromSubConfig(config)

# Adjust config by applying ValueGetterBase-derived
# futures. NOTE: this MUST be called after updateConfigFromSubConfig() in order
# to support value-getter-based substitutions from the sub-experiment (if any)
applyValueGettersToContainer(config)



# ------------------------------------------------------------------------------
# Tasks
#
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


    # Input stream specification per py/nupic/cluster/database/StreamDef.json.
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
      
      'aggregation' : config['aggregationInfo']
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
        
      # Iteration cycle list consisting of opftaskdriver.IterationPhaseSpecXXXXX
      # instances.
      'iterationCycle' : [
        #IterationPhaseSpecLearnOnly(1000),
        IterationPhaseSpecLearnAndInfer(1000),
        #IterationPhaseSpecInferOnly(10),
      ],
        
      
      # Inference specifications: sequence of opftaskdriver.InferenceSpecXXXXX
      # instances that indicate which inferences to perform and which metrics to
      # gather for each inference step. Note that it is up to the client
      # to decide what to do with these metrics
      'inferences' : [
        InferenceSpecNonTemporal(
          # [optional] Names of fields whose values are to be withheld (i.e.,
          # replaced with missing value sentinels) for testing of non-temporal
          # reconstruction; the original values of those fields will be used as
          # ground-truth during metrics calculation. If omitted, all field values
          # will be used unaltered as inputs to the model.
          testFields=("consumption",),

          # [optional] Sequence of inference metrics to gather. If omitted,
          # no metrics will be gathered for this inference type
          metrics=(
            MetricSpec(metric='rmse', field="consumption"),
          )
        ),
        
        InferenceSpecTemporal(
          # [optional] Sequence of inference metrics to gather. If omitted,
          # no metrics will be gathered for this inference type
          metrics=(
            MetricSpec(metric='rmse', field='consumption'),
          ),
        ),
      ],
      
      # Logged Metrics: A sequence of regular expressions that specify which of
      # the metrics from the Inference Specifications section MUST be logged for
      # every prediction. The regex's correspond to the automatically generated
      # metric labels. This is similar to the way the optimization metric is
      # specified in permutations.py.
      'loggedMetrics': [],
      
      # Callbacks for experimentation/research (optional)
      'callbacks' : {
        # Callbacks to be called at the beginning of a task, before model iterations.
        # Signature: callback(<reference to OPFExperiment>); returns nothing
        'setup' : [claModelControlEnableSPLearningCb, claModelControlEnableTPLearningCb],
        
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



descriptionInterface = ExperimentDescriptionAPI(modelConfig=config,
                                                taskList=tasks)
