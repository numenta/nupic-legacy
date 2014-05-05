# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------

"""
This file describes the Description API interface of the Online Prediction
Framework (OPF).

The Description API interface encapsulates the following two important sets of
configuration parameters in OPF
1) model creation parameters (via getDescription)
2) task control parameters (via getExperimentTasks)



The description class objects instantiated in description.py
implements the functionality by subclassing the Description API interface.

This allows description.py to be generic and oblivious to the specific
experiments.
"""



from abc import ABCMeta, abstractmethod
import logging
import types
import validictory

from nupic.frameworks.opf.opfutils import (
  validateOpfJsonValue)
from nupic.frameworks.opf.opftaskdriver import (
                                            IterationPhaseSpecLearnOnly,
                                            IterationPhaseSpecInferOnly,
                                            IterationPhaseSpecLearnAndInfer)
from nupic.support.enum import Enum



###############################################################################
# Enum to characterize potential generation environments
OpfEnvironment = Enum(Grok='grok',
                      Experiment='opfExperiment')



###############################################################################
class DescriptionIface(object):
  """ This is the base interface class for description API classes which provide
  OPF configuration parameters.

  This mechanism abstracts description API from the specific description objects
  created by the individiual users.

  TODO: logging interface?
  """
  __metaclass__ = ABCMeta


  @abstractmethod
  def __init__(self, modelConfig, control):
    """
        modelConfig:
            a dictionary object which holds user-defined settings for model
            creation.  See OPF descriptionTemplate.tpl for config dict
            documentation

        control:
            A dictionary describing how the model is to be run. The schema of
            this dictionary depends on the 'environment' parameter, which
            specifies the context in which the model is being run.
    """

  @abstractmethod
  def getModelDescription(self):
    """ Returns the model creation parameters based on the settings in the config
    dictionary.
    """


  @abstractmethod
  def getModelControl(self):
    """ Returns the task instances of the experiment description.

    Returns: A python dict describing how the model is to be run
    """

  @abstractmethod
  def convertGrokEnvToOPF(self):
    """ Converts the control element from Grok format to a default OPF
    format with 1 task. This is useful when you have a base description file
    that you want to run both permutations on (which requires the Grok
    environment format) and single OPF experiments on (which requires the
    OPF format).

    Returns: None
    """



###############################################################################
###############################################################################
class ExperimentDescriptionAPI(DescriptionIface):

  def __init__(self, modelConfig, control):
    """
    modelConfig:
        a dictionary object which holds user-defined settings for model
        creation.  See OPF descriptionTemplate.tpl for config dict
        documentation

    control:
        A dictionary describing how the model is to be run. The schema of
        this dictionary depends on the 'environment' parameter, which
        specifies the context in which the model is being run.
    """
    environment = control['environment']
    if environment == OpfEnvironment.Experiment:
      self.__validateExperimentControl(control)
    elif environment == OpfEnvironment.Grok:
      self.__validateGrokControl(control)

    self.__modelConfig = modelConfig
    self.__control = control


  #############################################################################
  def getModelDescription(self):
    if (self.__modelConfig['model'] == 'CLA' and
        'version' not in self.__modelConfig):
      # The modelConfig is in the old CLA format, update it.
      return self.__getCLAModelDescription()
    else:
      return self.__modelConfig

  #############################################################################
  def getModelControl(self):
    """ Returns the task instances of the experiment description.

    Returns: A python dict describing how the model is to be run
    """
    return self.__control

  #############################################################################
  def __validateExperimentControl(self, control):
    """ Validates control dictionary for the experiment context"""
    # Validate task list
    taskList = control.get('tasks', None)
    if taskList is not None:
      taskLabelsList = []

      for task in taskList:
        validateOpfJsonValue(task, "opfTaskSchema.json")
        validateOpfJsonValue(task['taskControl'], "opfTaskControlSchema.json")

        taskLabel = task['taskLabel']

        assert isinstance(taskLabel, types.StringTypes), \
               "taskLabel type: %r" % type(taskLabel)
        assert len(taskLabel) > 0, "empty string taskLabel not is allowed"

        taskLabelsList.append(taskLabel.lower())

      taskLabelDuplicates = filter(lambda x: taskLabelsList.count(x) > 1,
                                   taskLabelsList)
      assert len(taskLabelDuplicates) == 0, \
             "Duplcate task labels are not allowed: %s" % taskLabelDuplicates

    return

  #############################################################################
  def __validateGrokControl(self, control):
    """ Validates control dictionary for the grok engine context"""
    validateOpfJsonValue(control, "grokControlSchema.json")


  #############################################################################
  def convertGrokEnvToOPF(self):

    # We need to create a task structure, most of which is taken verbatim
    # from the Grok control dict
    task = dict(self.__control)

    task.pop('environment')
    inferenceArgs = task.pop('inferenceArgs')
    task['taskLabel'] = 'DefaultTask'

    # Create the iterationCycle element that will be placed inside the
    #  taskControl.
    iterationCount = task.get('iterationCount', -1)
    iterationCountInferOnly = task.pop('iterationCountInferOnly', 0)
    if iterationCountInferOnly == -1:
      iterationCycle = [IterationPhaseSpecInferOnly(1000, inferenceArgs=inferenceArgs)]
    elif iterationCountInferOnly > 0:
      assert iterationCount > 0, "When iterationCountInferOnly is specified, "\
        "iterationCount must also be specified and not be -1"
      iterationCycle = [IterationPhaseSpecLearnAndInfer(iterationCount
                                                    -iterationCountInferOnly, inferenceArgs=inferenceArgs),
                        IterationPhaseSpecInferOnly(iterationCountInferOnly, inferenceArgs=inferenceArgs)]
    else:
      iterationCycle = [IterationPhaseSpecLearnAndInfer(1000, inferenceArgs=inferenceArgs)]


    taskControl = dict(metrics = task.pop('metrics'),
                       loggedMetrics = task.pop('loggedMetrics'),
                       iterationCycle = iterationCycle)
    task['taskControl'] = taskControl

    # Create the new control
    self.__control = dict(environment = OpfEnvironment.Grok,
                          tasks = [task])


  #############################################################################
  def __getCLAModelDescription(self):
    config = self.__modelConfig

    assert config['model'] == "CLA"
    spParams = dict(
      spVerbosity = config['spVerbosity'],
      globalInhibition = 1,
      columnCount = config['claRegionNColumns'],
      inputWidth = 0,
      numActivePerInhArea = config['spNumActivePerInhArea'],
      seed = 1956,
      coincInputPoolPct = config.get('spCoincInputPoolPct', 1.0),
      synPermConnected = config.get('spSynPermConnected', 0.1),
      synPermActiveInc = config.get('synPermActiveInc', 0.1),
      synPermInactiveDec = config.get('synPermInactiveDec', 0.01),
    )

    tpParams = dict(
      verbosity = config['tpVerbosity'],
      columnCount = config['claRegionNColumns'],
      cellsPerColumn = config['tpNCellsPerCol'] if config['tpEnable']  else 1,
      inputWidth   = spParams['columnCount'],
      seed = 1960,
      temporalImp = config['tpImplementation'],
      newSynapseCount = config['tpNewSynapseCount']
                        if config['tpNewSynapseCount'] is not None
                        else config['spNumActivePerInhArea'],
      maxSynapsesPerSegment = config['tpMaxSynapsesPerSegment'],
      maxSegmentsPerCell = config['tpMaxSegmentsPerCell'],
      initialPerm = config['tpInitialPerm'],
      permanenceInc = config['tpPermanenceInc'],
      permanenceDec = config['tpPermanenceInc']
                      if config['tpPermanenceDec'] is None
                      else config['tpPermanenceDec'],
      globalDecay = 0.0,
      maxAge = 0,
      minThreshold = 12 if config['tpMinSegmentMatchSynapseThreshold'] is None
                      else config['tpMinSegmentMatchSynapseThreshold'],
      activationThreshold = 16 if config['tpSegmentActivationThreshold'] is None
                                  else config['tpSegmentActivationThreshold'],

      outputType = config.get('tpOutputType', 'normal'),
      pamLength = config.get('tpPamLength', 1),
    )

    sensorParams = dict(
      verbosity = config['sensorVerbosity'],
      encoders = config['dsEncoderSchema'],
      sensorAutoReset = config['sensorAutoReset']
    )

    if 'clRegionName' in config:
      clParams = dict(
        regionName = config['clRegionName'],
        clVerbosity = config['clVerbosity'],
      )
      if config['clRegionName'] == 'KNNClassifierRegion':
        clParams['replaceDuplicates'] = 1
      elif config['clRegionName'] == 'CLAClassifierRegion':
        clAlpha = config.get('clAlpha', None)
        if clAlpha is None:
          clAlpha = 0.001
        clParams['alpha'] = clAlpha
        clParams['steps'] = config.get('clSteps', '1')

      if 'clAdvancedParams' in config:
        clParams.update(config['clAdvancedParams'])

    else:
      clParams = None


    modelDescription =  dict(
      version = 1,
      model = config['model'],
      modelParams = dict(
           inferenceType  = config['inferenceType'],
           predictedField = config.get('predictedField', None),
           sensorParams   = sensorParams,
           spEnable       = config.get('spEnable', True),
           spParams       = spParams,
           tpEnable       = config['tpEnable'],
           tpParams       = tpParams,
           clParams       = clParams,
           trainSPNetOnlyIfRequested = config.get(
                                      'claTrainSPNetOnlyIfRequested', False),
      )
    )

    return modelDescription
