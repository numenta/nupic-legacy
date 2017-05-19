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
This script is part of the Online Prediction Framework (OPF) suite.
It implements the TaskDriver for an OPF experiment.

It's used by OPF RunExperiment and may also be useful for swarming's
HyperSearch Worker

The TaskDriver is a simple state machine that:

  1. Accepts incoming records from the client one data row at a time.

  2. Cycles through phases in the requested iteration cycle; the phases may
     include any combination of learnOnly, inferOnly, and learnAndInfer.

  3. For each data row, generates an OPF Model workflow that corresponds to
     the current phase in the iteration cycle and the requested inference types.

  4. Emits inference results via user-supplied PredictionLogger

  5. Gathers requested inference metrics.

  6. Invokes user-proved callbaks (setup, postIter, finish)

.. note:: For the purposes of testing predictions and generating metrics, it
  assumes that all incoming dataset records are "sensor data" - i.e., ground
  truth. However, if you're using OPFTaskDriver only to generate predictions,
  and not for testing predictions/generating metrics, they don't need to be
  "ground truth" records.
"""

from abc import (
  ABCMeta,
  abstractmethod)
from collections import defaultdict
import itertools
import logging

from prediction_metrics_manager import (
  MetricsManager,
  )



class IterationPhaseSpecLearnOnly(object):
  """ This class represents the Learn-only phase of the Iteration Cycle in
  the TaskControl block of description.py

  :param nIters: (int) iterations to remain in this phase. An iteration
                 corresponds to a single :meth:`OPFTaskDriver.handleInputRecord`
                 call.
  """

  def __init__(self, nIters):
    assert nIters > 0, "nIter=%s" % nIters

    self.__nIters = nIters
    return

  def __repr__(self):
    s = "%s(nIters=%r)" % (self.__class__.__name__, self.__nIters)
    return s


  def _getImpl(self, model):
    """ Creates and returns the _IterationPhase-based instance corresponding
    to this phase specification

    model:          Model instance
    """
    impl = _IterationPhaseLearnOnly(model=model,
                                    nIters=self.__nIters)
    return impl


class IterationPhaseSpecInferOnly(object):
  """ This class represents the Infer-only phase of the Iteration Cycle in
  the TaskControl block of description.py

  :param nIters: (int) Number of iterations to remain in this phase. An
         iteration corresponds to a single
         :meth:`OPFTaskDriver.handleInputRecord` call.
  :param inferenceArgs: (dict) A dictionary of arguments required for inference.
         These depend on the
         :class:`~nupic.frameworks.opf.opf_utils.InferenceType` of the current
         model.
  """

  def __init__(self, nIters, inferenceArgs=None):
    assert nIters > 0, "nIters=%s" % nIters

    self.__nIters = nIters
    self.__inferenceArgs = inferenceArgs
    return

  def __repr__(self):
    s = "%s(nIters=%r)" % (self.__class__.__name__, self.__nIters)
    return s

  def _getImpl(self, model):
    """ Creates and returns the _IterationPhase-based instance corresponding
    to this phase specification

    model:          Model instance
    """
    impl = _IterationPhaseInferOnly(model=model,
                                    nIters=self.__nIters,
                                    inferenceArgs=self.__inferenceArgs)
    return impl


class IterationPhaseSpecLearnAndInfer(object):
  """ This class represents the Learn-and-Infer phase of the Iteration Cycle in
  the TaskControl block of description.py

  :param nIters: (int) Number of iterations to remain in this phase. An
         iteration corresponds to a single
         :meth:`OPFTaskDriver.handleInputRecord` call.
  :param inferenceArgs: (dict) A dictionary of arguments required for inference.
         These depend on the
         :class:`~nupic.frameworks.opf.opf_utils.InferenceType` of the current
         model.
  """

  def __init__(self, nIters, inferenceArgs=None):
    assert nIters > 0, "nIters=%s" % nIters

    self.__nIters = nIters
    self.__inferenceArgs = inferenceArgs
    return

  def __repr__(self):
    s = "%s(nIters=%r)" % (self.__class__.__name__, self.__nIters)
    return s

  def _getImpl(self, model):
    """ Creates and returns the _IterationPhase-based instance corresponding
    to this phase specification

    model:          Model instance
    """
    impl = _IterationPhaseLearnAndInfer(model=model,
                                        nIters=self.__nIters,
                                        inferenceArgs=self.__inferenceArgs)
    return impl



class OPFTaskDriver(object):
  """
  Task Phase Driver implementation

  Conceptually, the client injects input records, one at a time, into
  an OPFTaskDriver instance for execution according to the
  current IterationPhase as maintained by the OPFTaskDriver instance.

  :param taskControl: (dict) conforming to opfTaskControlSchema.json that
         defines the actions to be performed on the given model.

  :param model: (:class:`nupic.frameworks.opf.model.Model`) that this
         OPFTaskDriver instance will drive.
  """

  def __init__(self, taskControl, model):
    #validateOpfJsonValue(taskControl, "opfTaskControlSchema.json")


    self.__reprstr = ("%s(" + \
                      "taskControl=%r, " + \
                      "model=%r)") % \
                          (self.__class__.__name__,
                           taskControl,
                           model)

    # Init logging
    #
    self.logger = logging.getLogger(".".join(
      ['com.numenta', self.__class__.__module__, self.__class__.__name__]))

    self.logger.debug(("Instantiating %s; %r.") % \
                        (self.__class__.__name__,
                         self.__reprstr))

    # -----------------------------------------------------------------------
    # Save args of interest
    #
    self.__taskControl = taskControl
    self.__model = model

    # -----------------------------------------------------------------------
    # Create Metrics Manager.
    #
    self.__metricsMgr = None
    metrics = taskControl.get('metrics', None)
    self.__metricsMgr = MetricsManager(metricSpecs=metrics,
                                       inferenceType=model.getInferenceType(),
                                       fieldInfo=model.getFieldInfo())

    # -----------------------------------------------------------------------
    # Figure out which metrics should be logged
    #

    # The logged metrics won't within the current task
    self.__loggedMetricLabels = set([])

    loggedMetricPatterns =  taskControl.get('loggedMetrics', None)

    # -----------------------------------------------------------------------
    # Create our phase manager
    #
    self.__phaseManager = _PhaseManager(
      model=model,
      phaseSpecs=taskControl.get('iterationCycle', []))

    # -----------------------------------------------------------------------
    # Initialize the callbacks container
    #
    self.__userCallbacks = defaultdict(list, taskControl.get('callbacks', {}))

    return


  def __repr__(self):
    return self.__reprstr


  def replaceIterationCycle(self, phaseSpecs):
    """ Replaces the Iteration Cycle phases

    :param phaseSpecs: Iteration cycle description consisting of a sequence of
                  IterationPhaseSpecXXXXX elements that are performed in the
                  given order
    """

    # -----------------------------------------------------------------------
    # Replace our phase manager
    #
    self.__phaseManager = _PhaseManager(
      model=self.__model,
      phaseSpecs=phaseSpecs)

    return


  def setup(self):
    """ Performs initial setup activities, including 'setup' callbacks. This
    method MUST be called once before the first call to
    :meth:`handleInputRecord`.
    """
    # Execute task-setup callbacks
    for cb in self.__userCallbacks['setup']:
      cb(self.__model)

    return


  def finalize(self):
    """ Perform final activities, including 'finish' callbacks. This
    method MUST be called once after the last call to :meth:`handleInputRecord`.
    """
    # Execute task-finish callbacks
    for cb in self.__userCallbacks['finish']:
      cb(self.__model)

    return


  def handleInputRecord(self, inputRecord):
    """
    Processes the given record according to the current iteration cycle phase

    :param inputRecord: (object) record expected to be returned from
           :meth:`nupic.data.record_stream.RecordStreamIface.getNextRecord`.

    :returns: :class:`nupic.frameworks.opf.opf_utils.ModelResult`
    """
    assert inputRecord, "Invalid inputRecord: %r" % inputRecord

    results = self.__phaseManager.handleInputRecord(inputRecord)
    metrics = self.__metricsMgr.update(results)

    # Execute task-postIter callbacks
    for cb in self.__userCallbacks['postIter']:
      cb(self.__model)

    results.metrics = metrics

    # Return the input and predictions for this record
    return results


  def getMetrics(self):
    """ Gets the current metric values

    :returns: A dictionary of metric values. The key for each entry is the label
              for the metric spec, as generated by
              :meth:`nupic.frameworks.opf.metrics.MetricSpec.getLabel`. The
              value for each entry is a dictionary containing the value of the
              metric as returned by
              :meth:`nupic.frameworks.opf.metrics.MetricsIface.getMetric`.
    """
    return self.__metricsMgr.getMetrics()

  def getMetricLabels(self):
    """
    :returns: (list) labels for the metrics that are being calculated
    """
    return self.__metricsMgr.getMetricLabels()



class _PhaseManager(object):
  """ Manages iteration cycle phase drivers
  """
  def __init__(self, model, phaseSpecs):
    """
    model:   Model instance
    phaseSpecs:   Iteration period description consisting of a sequence of
                  IterationPhaseSpecXXXXX elements that are performed in the
                  given order
    """

    self.__model = model

    # Instantiate Iteration Phase drivers
    self.__phases = tuple(map(lambda x: x._getImpl(model=model),
                              phaseSpecs))

    # Init phase-management structures
    if self.__phases:
      self.__phaseCycler = itertools.cycle(self.__phases)
      self.__advancePhase()

    return


  def __repr__(self):
    return "%s(phases=%r)" % \
                (self.__class__.__name__,
                 self.__phases)


  def __advancePhase(self):
    """ Advance to the next iteration cycle phase
    """
    self.__currentPhase = self.__phaseCycler.next()
    self.__currentPhase.enterPhase()

    return


  def handleInputRecord(self, inputRecord):
    """ Processes the given record according to the current phase

    inputRecord:  record object formatted according to
                  nupic.data.FileSource.getNext() result format.

    Returns:      An opf_utils.ModelResult object with the inputs and inferences
                  after the current record is processed by the model
    """

    results = self.__model.run(inputRecord)

    shouldContinue = self.__currentPhase.advance()
    if not shouldContinue:
      self.__advancePhase()

    return results




###############################################################################
# Iteration cycle phase drivers
###############################################################################



class _IterationPhase(object):
  """ Interface for IterationPhaseXXXXX classes
  """

  __metaclass__ = ABCMeta

  def __init__(self, nIters):
    """
    nIters:       Number of iterations; MUST be greater than 0
    """

    assert nIters > 0, "nIters=%s" % nIters
    self.__nIters = nIters

    return

  @abstractmethod
  def enterPhase(self):
    """
    Performs initialization that is necessary upon entry to the phase. Must
    be called before handleInputRecord() at the beginning of each phase
    """

    self.__iter = iter(xrange(self.__nIters))

    # Prime the iterator
    self.__iter.next()


  def advance(self):
    """ Advances the iteration;

    Returns:      True if more iterations remain; False if this is the final
                  iteration.
    """
    hasMore = True
    try:
      self.__iter.next()
    except StopIteration:
      self.__iter = None
      hasMore = False

    return hasMore



class _IterationPhaseLearnOnly(_IterationPhase):
  """ This class implements the "learn-only" phase of the Iteration Cycle
  """
  def __init__(self, model, nIters):
    """
    model:        Model instance
    nIters:       Number of iterations; MUST be greater than 0
    """

    super(_IterationPhaseLearnOnly, self).__init__(nIters=nIters)

    self.__model = model
    return

  def enterPhase(self):
    """ [_IterationPhase method implementation]
    Performs initialization that is necessary upon entry to the phase. Must
    be called before handleInputRecord() at the beginning of each phase
    """
    super(_IterationPhaseLearnOnly, self).enterPhase()
    self.__model.enableLearning()
    self.__model.disableInference()
    return



class _IterationPhaseInferCommon(_IterationPhase):
  """ Basic class providing common implementation for
  _IterationPhaseInferOnly and _IterationPhaseLearnAndInfer classes
  """
  def __init__(self, model, nIters, inferenceArgs):
    """
    model:        Model instance
    nIters:       Number of iterations; MUST be greater than 0
    inferenceArgs:
                  A dictionary of arguments required for inference. These
                  depend on the InferenceType of the current model
    """

    super(_IterationPhaseInferCommon, self).__init__(nIters=nIters)
    self._model = model
    self._inferenceArgs = inferenceArgs
    return

  def enterPhase(self):
    """ [_IterationPhase method implementation]
    Performs initialization that is necessary upon entry to the phase. Must
    be called before handleInputRecord() at the beginning of each phase
    """
    super(_IterationPhaseInferCommon, self).enterPhase()
    self._model.enableInference(inferenceArgs=self._inferenceArgs)
    return



class _IterationPhaseInferOnly(_IterationPhaseInferCommon):
  """ This class implements the "infer-only" phase of the Iteration Cycle
  """

  def __init__(self, model, nIters, inferenceArgs):
    """
    model:        Model instance
    nIters:       Number of iterations; MUST be greater than 0
    inferenceArgs:
                  A dictionary of arguments required for inference. These
                  depend on the InferenceType of the current model
    """

    super(_IterationPhaseInferOnly, self).__init__(
      model=model,
      nIters=nIters,
      inferenceArgs=inferenceArgs)
    return

  def enterPhase(self):
    """ [_IterationPhase method implementation]
    Performs initialization that is necessary upon entry to the phase. Must
    be called before handleInputRecord() at the beginning of each phase
    """
    super(_IterationPhaseInferOnly, self).enterPhase()
    self._model.disableLearning()
    return



class _IterationPhaseLearnAndInfer(_IterationPhaseInferCommon):
  """ This class implements the "learn-and-infer" phase of the Iteration Cycle
  """

  def __init__(self, model, nIters, inferenceArgs):
    """
    model:        Model instance
    nIters:       Number of iterations; MUST be greater than 0
    inferenceArgs:
                  A dictionary of arguments required for inference. These
                  depend on the InferenceType of the current model
    """

    super(_IterationPhaseLearnAndInfer, self).__init__(
      model=model,
      nIters=nIters,
      inferenceArgs=inferenceArgs)

    return

  def enterPhase(self):
    """ [_IterationPhase method implementation]
    Performs initialization that is necessary upon entry to the phase. Must
    be called before handleInputRecord() at the beginning of each phase
    """
    super(_IterationPhaseLearnAndInfer, self).enterPhase()
    self._model.enableLearning()
    return
