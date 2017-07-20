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

Metrics take the predicted and actual values and compute some metric (lower is 
better) which is used in the OPF for swarming (and just generally as part of the 
output.

One non-obvious thing is that they are computed over a fixed window size, 
typically something like 1000 records. So each output record will have a metric 
score computed over the 1000 records prior.

Example usage (hot gym example):
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Where:

- ``aae``: average absolute error
- ``altMAPE``: mean absolute percentage error but modified so you never have 
               divide by zero

.. code-block:: python

  from nupic.frameworks.opf.metrics import MetricSpec
  from nupic.frameworks.opf.prediction_metrics_manager import MetricsManager

  model = createOpfModel() # assuming this is done elsewhere

  metricSpecs = (
      MetricSpec(field='kw_energy_consumption', metric='multiStep',
                 inferenceElement='multiStepBestPredictions',
                 params={'errorMetric': 'aae', 'window': 1000, 'steps': 1}),
      MetricSpec(field='kw_energy_consumption', metric='trivial',
                 inferenceElement='prediction',
                 params={'errorMetric': 'aae', 'window': 1000, 'steps': 1}),
      MetricSpec(field='kw_energy_consumption', metric='multiStep',
                 inferenceElement='multiStepBestPredictions',
                 params={'errorMetric': 'altMAPE', 'window': 1000, 'steps': 1}),
      MetricSpec(field='kw_energy_consumption', metric='trivial',
                 inferenceElement='prediction',
                 params={'errorMetric': 'altMAPE', 'window': 1000, 'steps': 1}),
  )

  metricsManager = MetricsManager(metricSpecs, 
                                  model.getFieldInfo(),
                                  model.getInferenceType()
                                  )
  for row in inputData: # this is just pseudocode
    result = model.run(row)
    metrics = metricsManager.update(result)
    # You can collect metrics here, or attach to your result object.
    result.metrics = metrics

See :meth:`getModule` for a mapping of available metric identifiers to their
implementation classes.
"""


from abc import ABCMeta, abstractmethod

import numbers
import copy
import numpy as np

import nupic.math.roc_utils as roc
from nupic.data import SENTINEL_VALUE_FOR_MISSING_DATA
from nupic.frameworks.opf.opf_utils import InferenceType
from nupic.utils import MovingAverage

from collections import deque
from operator import itemgetter
from safe_interpreter import SafeInterpreter
from io import StringIO
from functools import partial

###############################################################################
# Public Metric specification class
###############################################################################

class MetricSpec(object):
  """
  This class represents a single Metrics specification in the TaskControl block.

  :param metric: (string) A metric type name that identifies which metrics 
         module is to be constructed by 
         :meth:`nupic.frameworks.opf.metrics.getModule`; e.g., ``rmse``

  :param inferenceElement: 
         (:class:`~nupic.frameworks.opf.opf_utils.InferenceElement`) Some 
         inference types (such as classification), can output more than one type 
         of inference (i.e. the predicted class AND the predicted next step). 
         This field specifies which of these inferences to compute the metrics 
         on.

  :param field: (string) Field name on which this metric is to be collected
  :param params: (dict) Custom parameters for the metrics module's constructor
  """

  _LABEL_SEPARATOR = ":"

  def __init__(self, metric, inferenceElement, field=None, params=None):
    self.metric = metric
    self.inferenceElement = inferenceElement
    self.field = field
    self.params = params
    return

  def __repr__(self):
    return "%s(metric=%r, inferenceElement=%r, field=%r, params=%r)" \
                      % (self.__class__.__name__,
                         self.metric,
                         self.inferenceElement,
                         self.field,
                         self.params)

  def getLabel(self, inferenceType=None):
    """ 
    Helper method that generates a unique label for a :class:`MetricSpec` / 
    :class:`~nupic.frameworks.opf.opf_utils.InferenceType` pair. The label is 
    formatted as follows:

    ::
        
        <predictionKind>:<metric type>:(paramName=value)*:field=<fieldname>

    For example:
    
    :: 
    
        classification:aae:paramA=10.2:paramB=20:window=100:field=pounds
    
    :returns: (string) label for inference type
    """
    result = []
    if inferenceType is not None:
      result.append(InferenceType.getLabel(inferenceType))
    result.append(self.inferenceElement)
    result.append(self.metric)

    params = self.params
    if params is not None:

      sortedParams= params.keys()
      sortedParams.sort()
      for param in sortedParams:
        # Don't include the customFuncSource - it is too long an unwieldy
        if param in ('customFuncSource', 'customFuncDef', 'customExpr'):
          continue
        value = params[param]
        if isinstance(value, str):
          result.extend(["%s='%s'"% (param, value)])
        else:
          result.extend(["%s=%s"% (param, value)])

    if self.field:
      result.append("field=%s"% (self.field) )

    return self._LABEL_SEPARATOR.join(result)

  @classmethod
  def getInferenceTypeFromLabel(cls, label):
    """ 
    Extracts the PredictionKind (temporal vs. nontemporal) from the given
    metric label.

    :param label: (string) for a metric spec generated by 
           :meth:`getMetricLabel`

    :returns: (:class:`~nupic.frameworks.opf.opf_utils.InferenceType`)
    """
    infType, _, _= label.partition(cls._LABEL_SEPARATOR)

    if not InferenceType.validate(infType):
      return None

    return infType



def getModule(metricSpec):
  """
  Factory method to return an appropriate :class:`MetricsIface` module.
  
  - ``rmse``: :class:`MetricRMSE`
  - ``nrmse``: :class:`MetricNRMSE`
  - ``aae``: :class:`MetricAAE`
  - ``acc``: :class:`MetricAccuracy`
  - ``avg_err``: :class:`MetricAveError`
  - ``trivial``: :class:`MetricTrivial`
  - ``two_gram``: :class:`MetricTwoGram`
  - ``moving_mean``: :class:`MetricMovingMean`
  - ``moving_mode``: :class:`MetricMovingMode`
  - ``neg_auc``: :class:`MetricNegAUC`
  - ``custom_error_metric``: :class:`CustomErrorMetric`
  - ``multiStep``: :class:`MetricMultiStep`
  - ``ms_aae``: :class:`MetricMultiStepAAE`
  - ``ms_avg_err``: :class:`MetricMultiStepAveError`
  - ``passThruPrediction``: :class:`MetricPassThruPrediction`
  - ``altMAPE``: :class:`MetricAltMAPE`
  - ``MAPE``: :class:`MetricMAPE`
  - ``multi``: :class:`MetricMulti`
  - ``negativeLogLikelihood``: :class:`MetricNegativeLogLikelihood`
  
  :param metricSpec: (:class:`MetricSpec`) metric to find module for. 
         ``metricSpec.metric`` must be in the list above.
  
  :returns: (:class:`AggregateMetric`) an appropriate metric module
  """

  metricName = metricSpec.metric

  if metricName == 'rmse':
    return MetricRMSE(metricSpec)
  if metricName == 'nrmse':
    return MetricNRMSE(metricSpec)
  elif metricName == 'aae':
    return MetricAAE(metricSpec)
  elif metricName == 'acc':
    return MetricAccuracy(metricSpec)
  elif metricName == 'avg_err':
    return MetricAveError(metricSpec)
  elif metricName == 'trivial':
    return MetricTrivial(metricSpec)
  elif metricName == 'two_gram':
    return MetricTwoGram(metricSpec)
  elif metricName == 'moving_mean':
    return MetricMovingMean(metricSpec)
  elif metricName == 'moving_mode':
    return MetricMovingMode(metricSpec)
  elif metricName == 'neg_auc':
    return MetricNegAUC(metricSpec)
  elif metricName == 'custom_error_metric':
    return CustomErrorMetric(metricSpec)
  elif metricName == 'multiStep':
    return MetricMultiStep(metricSpec)
  elif metricName == 'multiStepProbability':
    return MetricMultiStepProbability(metricSpec)
  elif metricName == 'ms_aae':
    return MetricMultiStepAAE(metricSpec)
  elif metricName == 'ms_avg_err':
    return MetricMultiStepAveError(metricSpec)
  elif metricName == 'passThruPrediction':
    return MetricPassThruPrediction(metricSpec)
  elif metricName == 'altMAPE':
    return MetricAltMAPE(metricSpec)
  elif metricName == 'MAPE':
    return MetricMAPE(metricSpec)
  elif metricName == 'multi':
    return MetricMulti(metricSpec)
  elif metricName == 'negativeLogLikelihood':
    return MetricNegativeLogLikelihood(metricSpec)
  else:
    raise Exception("Unsupported metric type: %s" % metricName)

################################################################################
#               Helper Methods and Classes                                    #
################################################################################

class _MovingMode(object):
  """ Helper class for computing windowed moving
  mode of arbitrary values """

  def __init__(self, windowSize = None):
    """
    :param windowSize:             The number of values that are used to compute the
                            moving average
    """
    self._windowSize = windowSize
    self._countDict = dict()
    self._history = deque([])


  def __call__(self, value):

    if len(self._countDict) == 0:
      pred = ""
    else:
      pred = max(self._countDict.items(), key = itemgetter(1))[0]

    # Update count dict and history buffer
    self._history.appendleft(value)

    if not value in self._countDict:
      self._countDict[value] = 0
    self._countDict[value] += 1

    if len(self._history) > self._windowSize:
      removeElem = self._history.pop()
      self._countDict[removeElem] -= 1
      assert(self._countDict[removeElem] > -1)

    return pred



def _isNumber(value):
  return isinstance(value, (numbers.Number, np.number))



class MetricsIface(object):
  """
  A Metrics module compares a prediction Y to corresponding ground truth X and 
  returns a single measure representing the "goodness" of the prediction. It is 
  up to the implementation to determine how this comparison is made.

  :param metricSpec: (:class:`MetricSpec`) spec used to created the metric
  """

  __metaclass__ = ABCMeta

  @abstractmethod
  def __init__(self, metricSpec):
    pass

  @abstractmethod
  def addInstance(self, groundTruth, prediction, record = None, result = None):
    """ 
    Add one instance consisting of ground truth and a prediction.

    :param groundTruth:
      The actual measured value at the current timestep
    
    :param prediction:
      The value predicted by the network at the current timestep

    :param record: the raw input record as fed to 
           :meth:`~nupic.frameworks.opf.model.Model.run` by the user. The 
           typical usage is to feed a record to that method and get a 
           :class:`~nupic.frameworks.opf.opf_utils.ModelResult`. Then you pass 
           :class:`~nupic.frameworks.opf.opf_utils.ModelResult`.rawInput into 
           this function as the record parameter.

    :param result: (:class:`~nupic.frameworks.opf.opf_utils.ModelResult`) the
           result of running a row of data through an OPF model

    :returns:
        The average error as computed over the metric's window size
    """

  @abstractmethod
  def getMetric(self):
    """
    ``stats`` is expected to contain further information relevant to the given 
    metric, for example the number of timesteps represented in the current 
    measurement. All stats are implementation defined, and ``stats`` can be 
    ``None``.

    :returns: (dict) representing data from the metric
       ::
       
           {value : <current measurement>, "stats" : {<stat> : <value> ...}}
      
    """



class AggregateMetric(MetricsIface):
  """
  Partial implementation of Metrics Interface for metrics that accumulate an 
  error and compute an aggregate score, potentially over some window of previous 
  data. This is a convenience class that can serve as the base class for a wide 
  variety of metrics.
  """
  ___metaclass__ = ABCMeta

  #FIXME @abstractmethod - this should be marked abstract method and required to be implemented
  def accumulate(self, groundTruth, prediction, accumulatedError, historyBuffer, result):
    """
    Updates the accumulated error given the prediction and the
    ground truth.

    :param groundTruth: Actual value that is observed for the current timestep

    :param prediction: Value predicted by the network for the given timestep

    :param accumulatedError: The total accumulated score from the previous
           predictions (possibly over some finite window)

    :param historyBuffer: A buffer of the last <self.window> ground truth values
           that have been observed.

           If historyBuffer = None,  it means that no history is being kept.

    :param result: An ModelResult class (see opf_utils.py), used for advanced
           metric calculation (e.g., MetricNegativeLogLikelihood)

    :returns: The new accumulated error. That is:
              
        .. code-block:: python
              
           self.accumulatedError = self.accumulate(
             groundTruth, predictions, accumulatedError
           )

        ``historyBuffer`` should also be updated in this method.
        ``self.spec.params["window"]`` indicates the maximum size of the window.
    """

  #FIXME @abstractmethod - this should be marked abstract method and required to be implemented
  def aggregate(self, accumulatedError, historyBuffer, steps):
    """
    Updates the final aggregated score error given the prediction and the ground 
    truth.

    :param accumulatedError: The total accumulated score from the previous
           predictions (possibly over some finite window)

    :param historyBuffer: A buffer of the last <self.window> ground truth values
           that have been observed. If ``historyBuffer`` = None,  it means that 
           no history is being kept.

    :param steps: (int) The total number of (groundTruth, prediction) pairs that 
           have been passed to the metric. This does not include pairs where 
           ``groundTruth = SENTINEL_VALUE_FOR_MISSING_DATA``

    :returns: The new aggregate (final) error measure.
    """

  def __init__(self, metricSpec):
    """ Initialize this metric

    If the params contains the key 'errorMetric', then that is the name of
    another metric to which we will pass a modified groundTruth and prediction
    to from our addInstance() method. For example, we may compute a moving mean
    on the groundTruth and then pass that to the AbsoluteAveError metric
    """

    # Init default member variables
    self.id = None
    self.verbosity = 0
    self.window = -1
    self.history = None
    self.accumulatedError = 0
    self.aggregateError = None
    self.steps = 0
    self.spec = metricSpec
    self.disabled = False

    # Number of steps ahead we are trying to predict. This is a list of
    #  prediction steps are processing
    self._predictionSteps = [0]

    # Where we store the ground truth history
    self._groundTruthHistory = deque([])

    # The instances of another metric to which we will pass a possibly modified
    #  groundTruth and prediction to from addInstance(). There is one instance
    #  for each step present in self._predictionSteps
    self._subErrorMetrics = None

    # The maximum number of records to process. After this many records have
    #  been processed, the metric value never changes. This can be used
    #  as the optimization metric for swarming, while having another metric without
    #  the maxRecords limit to get an idea as to how well a production model
    #  would do on the remaining data
    self._maxRecords = None

    # Parse the metric's parameters
    if metricSpec is not None and metricSpec.params is not None:

      self.id = metricSpec.params.get('id', None)
      self._predictionSteps = metricSpec.params.get('steps', [0])
      # Make sure _predictionSteps is a list
      if not hasattr(self._predictionSteps, '__iter__'):
        self._predictionSteps = [self._predictionSteps]

      self.verbosity = metricSpec.params.get('verbosity', 0)
      self._maxRecords = metricSpec.params.get('maxRecords', None)

      # Get the metric window size
      if 'window' in metricSpec.params:
        assert metricSpec.params['window'] >= 1
        self.history = deque([])
        self.window = metricSpec.params['window']

      # Get the name of the sub-metric to chain to from addInstance()
      if 'errorMetric' in metricSpec.params:
        self._subErrorMetrics = []
        for step in self._predictionSteps:
          subSpec = copy.deepcopy(metricSpec)
          # Do all ground truth shifting before we pass onto the sub-metric
          subSpec.params.pop('steps', None)
          subSpec.params.pop('errorMetric')
          subSpec.metric = metricSpec.params['errorMetric']
          self._subErrorMetrics.append(getModule(subSpec))



  def _getShiftedGroundTruth(self, groundTruth):
    """ Utility function that saves the passed in groundTruth into a local
    history buffer, and returns the groundTruth from self._predictionSteps ago,
    where self._predictionSteps is defined by the 'steps' parameter.
    This can be called from the beginning of a derived class's addInstance()
    before it passes groundTruth and prediction onto accumulate().
    """

    # Save this ground truth into our input history
    self._groundTruthHistory.append(groundTruth)

    # This is only supported when _predictionSteps has one item in it
    assert (len(self._predictionSteps) == 1)
    # Return the one from N steps ago
    if len(self._groundTruthHistory) > self._predictionSteps[0]:
      return self._groundTruthHistory.popleft()
    else:
      if hasattr(groundTruth, '__iter__'):
        return [None] * len(groundTruth)
      else:
        return None


  def addInstance(self, groundTruth, prediction, record = None, result = None):

    # This base class does not support time shifting the ground truth or a
    #  subErrorMetric.
    assert (len(self._predictionSteps) == 1)
    assert self._predictionSteps[0] == 0
    assert self._subErrorMetrics is None


    # If missing data,
    if groundTruth == SENTINEL_VALUE_FOR_MISSING_DATA or prediction is None:
      return self.aggregateError

    if self.verbosity > 0:
      print "groundTruth:\n%s\nPredictions:\n%s\n%s\n" % (groundTruth,
                                                prediction, self.getMetric())

    # Ignore if we've reached maxRecords
    if self._maxRecords is not None and self.steps >= self._maxRecords:
      return self.aggregateError

    # If there is a sub-metric, chain into it's addInstance
    # Accumulate the error
    self.accumulatedError = self.accumulate(groundTruth, prediction,
                                            self.accumulatedError, self.history, result)

    self.steps += 1
    return self._compute()

  def getMetric(self):
    return {"value": self.aggregateError, "stats" : {"steps" : self.steps}}

  def _compute(self):
    self.aggregateError = self.aggregate(self.accumulatedError, self.history,
                                         self.steps)
    return self.aggregateError


class MetricNegativeLogLikelihood(AggregateMetric):
  """
  Computes negative log-likelihood. Likelihood is the predicted probability of
  the true data from a model. It is more powerful than metrics that only 
  considers the single best prediction (e.g. MSE) as it considers the entire 
  probability distribution predicted by a model.

  It is more appropriate to use likelihood as the error metric when multiple
  predictions are possible.
  """
  def accumulate(self, groundTruth, prediction, accumulatedError, historyBuffer, result):
    bucketll = result.inferences['multiStepBucketLikelihoods']
    bucketIdxTruth = result.classifierInput.bucketIndex

    if bucketIdxTruth is not None:
      # a manually set minimum prediction probability so that the log(LL) doesn't blow up
      minProb = 0.00001
      negLL = 0
      for step in bucketll.keys():
        outOfBucketProb = 1 - sum(bucketll[step].values())
        if bucketIdxTruth in bucketll[step].keys():
          prob = bucketll[step][bucketIdxTruth]
        else:
          prob = outOfBucketProb

        if prob < minProb:
          prob = minProb
        negLL -= np.log(prob)

      accumulatedError += negLL

      if historyBuffer is not None:
        historyBuffer.append(negLL)
        if len(historyBuffer) > self.spec.params["window"]:
          accumulatedError -= historyBuffer.popleft()

    return accumulatedError

  def aggregate(self, accumulatedError, historyBuffer, steps):
    n = steps
    if historyBuffer is not None:
      n = len(historyBuffer)

    return accumulatedError / float(n)


class MetricRMSE(AggregateMetric):
  """
  Computes root-mean-square error.
  """
  def accumulate(self, groundTruth, prediction, accumulatedError, historyBuffer, result = None):
    error = (groundTruth - prediction)**2
    accumulatedError += error

    if historyBuffer is not None:
      historyBuffer.append(error)
      if len(historyBuffer) > self.spec.params["window"] :
        accumulatedError -= historyBuffer.popleft()

    return accumulatedError

  def aggregate(self, accumulatedError, historyBuffer, steps):
    n = steps
    if historyBuffer is not None:
      n = len(historyBuffer)

    return np.sqrt(accumulatedError / float(n))



class MetricNRMSE(MetricRMSE):
  """
  Computes normalized root-mean-square error.
  """
  def __init__(self, *args, **kwargs):
    super(MetricNRMSE, self).__init__(*args, **kwargs)
    self.groundTruths = []

  def accumulate(self, groundTruth, prediction, accumulatedError, historyBuffer, result = None):
    self.groundTruths.append(groundTruth)

    return super(MetricNRMSE, self).accumulate(groundTruth,
                                               prediction,
                                               accumulatedError,
                                               historyBuffer,
                                               result)

  def aggregate(self, accumulatedError, historyBuffer, steps):
    rmse = super(MetricNRMSE, self).aggregate(accumulatedError,
                                              historyBuffer,
                                              steps)
    denominator = np.std(self.groundTruths)
    return rmse / denominator if denominator > 0 else float("inf")



class MetricAAE(AggregateMetric):
  """
  Computes average absolute error.
  """
  def accumulate(self, groundTruth, prediction, accumulatedError, historyBuffer, result = None):
    error = abs(groundTruth - prediction)
    accumulatedError += error

    if historyBuffer is not None:
      historyBuffer.append(error)
      if len(historyBuffer) > self.spec.params["window"] :
        accumulatedError -= historyBuffer.popleft()

    return accumulatedError

  def aggregate(self, accumulatedError, historyBuffer, steps):
    n = steps
    if historyBuffer is not None:
      n = len(historyBuffer)

    return accumulatedError/ float(n)



class MetricAltMAPE(AggregateMetric):
  """
  Computes the "Alternative" Mean Absolute Percent Error.

  A generic MAPE computes the percent error for each sample, and then gets
  an average. This can suffer from samples where the actual value is very small
  or zero - this one sample can drastically alter the mean.

  This metric on the other hand first computes the average of the actual values
  and the averages of the errors before dividing. This washes out the effects of
  a small number of samples with very small actual values.
  """

  def __init__(self, metricSpec):
    super(MetricAltMAPE, self).__init__(metricSpec)
    self._accumulatedGroundTruth = 0
    self._accumulatedError = 0

  def addInstance(self, groundTruth, prediction, record = None, result = None):

    # If missing data,
    if groundTruth == SENTINEL_VALUE_FOR_MISSING_DATA or prediction is None:
      return self.aggregateError


    # Compute absolute error
    error = abs(groundTruth - prediction)
    if self.verbosity > 0:
      print "MetricAltMAPE:\n  groundTruth: %s\n  Prediction: " \
            "%s\n  Error: %s" % (groundTruth, prediction, error)

    # Update the accumulated groundTruth and aggregate error
    if self.history is not None:
      self.history.append((groundTruth, error))
      if len(self.history) > self.spec.params["window"] :
        (oldGT, oldErr) = self.history.popleft()
        self._accumulatedGroundTruth -= oldGT
        self._accumulatedError -= oldErr

    self._accumulatedGroundTruth += abs(groundTruth)
    self._accumulatedError += error

    # Compute aggregate pct error
    if self._accumulatedGroundTruth > 0:
      self.aggregateError = 100.0 * self._accumulatedError / \
                              self._accumulatedGroundTruth
    else:
      self.aggregateError = 0

    if self.verbosity >= 1:
      print "  accumGT:", self._accumulatedGroundTruth
      print "  accumError:", self._accumulatedError
      print "  aggregateError:", self.aggregateError

    self.steps += 1
    return self.aggregateError



class MetricMAPE(AggregateMetric):
  """
  Computes the "Classic" Mean Absolute Percent Error.

  This computes the percent error for each sample, and then gets
  an average. Note that this can suffer from samples where the actual value is
  very small or zero - this one sample can drastically alter the mean. To
  avoid this potential issue, use 'altMAPE' instead.

  This metric is provided mainly as a convenience when comparing results against
  other investigations that have also used MAPE.
  """

  def __init__(self, metricSpec):
    super(MetricMAPE, self).__init__(metricSpec)
    self._accumulatedPctError = 0

  def addInstance(self, groundTruth, prediction, record = None, result = None):

    # If missing data,
    if groundTruth == SENTINEL_VALUE_FOR_MISSING_DATA or prediction is None:
      return self.aggregateError


    # Compute absolute error
    if groundTruth != 0:
      pctError = float(abs(groundTruth - prediction))/groundTruth
    else:
      # Ignore this sample
      if self.verbosity > 0:
        print "Ignoring sample with groundTruth of 0"
      self.steps += 1
      return self.aggregateError

    if self.verbosity > 0:
      print "MetricMAPE:\n  groundTruth: %s\n  Prediction: " \
            "%s\n  Error: %s" % (groundTruth, prediction, pctError)

    # Update the accumulated groundTruth and aggregate error
    if self.history is not None:
      self.history.append(pctError)
      if len(self.history) > self.spec.params["window"] :
        (oldPctErr) = self.history.popleft()
        self._accumulatedPctError -= oldPctErr

    self._accumulatedPctError += pctError

    # Compute aggregate pct error
    self.aggregateError = 100.0 * self._accumulatedPctError / len(self.history)

    if self.verbosity >= 1:
      print "  accumPctError:", self._accumulatedPctError
      print "  aggregateError:", self.aggregateError

    self.steps += 1
    return self.aggregateError



class MetricPassThruPrediction(MetricsIface):
  """
  This is not a metric, but rather a facility for passing the predictions
  generated by a baseline metric through to the prediction output cache produced
  by a model.

  For example, if you wanted to see the predictions generated for the TwoGram
  metric, you would specify 'PassThruPredictions' as the 'errorMetric' 
  parameter.

  This metric class simply takes the prediction and outputs that as the
  aggregateMetric value.
  """

  def __init__(self, metricSpec):
    self.spec = metricSpec
    self.window = metricSpec.params.get("window", 1)
    self.avg = MovingAverage(self.window)

    self.value = None

  def addInstance(self, groundTruth, prediction, record = None, result = None):
    """Compute and store metric value"""
    self.value = self.avg(prediction)

  def getMetric(self):
    """Return the metric value """
    return {"value": self.value}


  #def accumulate(self, groundTruth, prediction, accumulatedError, historyBuffer):
  #  # Simply return the prediction as the accumulated error
  #  return prediction
  #
  #def aggregate(self, accumulatedError, historyBuffer, steps):
  #  # Simply return the prediction as the aggregateError
  #  return accumulatedError



class MetricMovingMean(AggregateMetric):
  """
  Computes error metric based on moving mean prediction.
  """
  def __init__(self, metricSpec):

    # This metric assumes a default 'steps' of 1
    if not 'steps' in metricSpec.params:
      metricSpec.params['steps'] = 1

    super(MetricMovingMean, self).__init__(metricSpec)

    # Only supports 1 item in _predictionSteps
    assert (len(self._predictionSteps) == 1)

    self.mean_window = 10
    if metricSpec.params.has_key('mean_window'):
      assert metricSpec.params['mean_window'] >= 1
      self.mean_window = metricSpec.params['mean_window']

    # Construct moving average instance
    self._movingAverage = MovingAverage(self.mean_window)

  def getMetric(self):
    return self._subErrorMetrics[0].getMetric()

  def addInstance(self, groundTruth, prediction, record = None, result = None):

    # If missing data,
    if groundTruth == SENTINEL_VALUE_FOR_MISSING_DATA:
      return self._subErrorMetrics[0].aggregateError

    if self.verbosity > 0:
      print "groundTruth:\n%s\nPredictions:\n%s\n%s\n" % (groundTruth, prediction, self.getMetric())

    # Use ground truth from 'steps' steps ago as our most recent ground truth
    lastGT = self._getShiftedGroundTruth(groundTruth)
    if lastGT is None:
      return self._subErrorMetrics[0].aggregateError

    mean = self._movingAverage(lastGT)

    return self._subErrorMetrics[0].addInstance(groundTruth, mean, record)

def evalCustomErrorMetric(expr, prediction, groundTruth, tools):
  sandbox = SafeInterpreter(writer=StringIO())
  if isinstance(prediction, dict):
    sandbox.symtable['prediction'] = tools.mostLikely(prediction)
    sandbox.symtable['EXP'] = tools.expValue(prediction)
    sandbox.symtable['probabilityDistribution'] = prediction
  else:
    sandbox.symtable['prediction'] = prediction
  sandbox.symtable['groundTruth'] = groundTruth
  sandbox.symtable['tools'] = tools
  error = sandbox(expr)
  return error



class CustomErrorMetric(MetricsIface):
  """
  Custom Error Metric class that handles user defined error metrics.
  """
  class CircularBuffer():
    """
      implementation of a fixed size constant random access circular buffer
    """
    def __init__(self,length):
      #Create an array to back the buffer
      #If the length<0 create a zero length array
      self.data = [None for i in range(max(length,0))]
      self.elements = 0
      self.index = 0
      self.dataLength = length

    def getItem(self,n):
      #Get item from n steps back
      if n >= self.elements or (n >= self.dataLength and not self.dataLength < 0):
        assert  False,"Trying to access data not in the stored window"
        return None
      if self.dataLength>=0:
        getInd = (self.index-n-1)%min(self.elements,self.dataLength)
      else:
        getInd = (self.index-n-1)%self.elements
      return self.data[getInd]

    def pushToEnd(self,obj):
      ret = None
      #If storing everything simply append right to the list
      if(self.dataLength < 0 ):
        self.data.append(obj)
        self.index+=1
        self.elements+=1
        return None
      if(self.elements==self.dataLength):
        #pop last added element
        ret = self.data[self.index % self.dataLength]
      else:
        #else push new element and increment the element counter
        self.elements += 1
      self.data[self.index % self.dataLength] = obj
      self.index += 1
      return ret
    def __len__(self):
      return self.elements

  def __init__(self,metricSpec):
    self.metricSpec = metricSpec
    self.steps = 0
    self.error = 0
    self.averageError = None
    self.errorMatrix = None
    self.evalError = self.evalAbsErr
    self.errorWindow = 1
    self.storeWindow=-1
    self.userDataStore = dict()
    if "errorWindow" in metricSpec.params:
      self.errorWindow = metricSpec.params["errorWindow"]
      assert self.errorWindow  != 0 , "Window Size cannon be zero"
    if "storeWindow" in metricSpec.params:
      self.storeWindow = metricSpec.params["storeWindow"]
      assert self.storeWindow  != 0 , "Window Size cannon be zero"
    self.errorStore = self.CircularBuffer(self.errorWindow)
    self.recordStore = self.CircularBuffer(self.storeWindow)
    if "customExpr" in metricSpec.params:
      assert not "customFuncDef" in metricSpec.params
      assert not "customFuncSource" in metricSpec.params
      self.evalError = partial(evalCustomErrorMetric, metricSpec.params["customExpr"])
    elif "customFuncSource" in metricSpec.params:
      assert not "customFuncDef" in metricSpec.params
      assert not "customExpr" in metricSpec.params
      exec(metricSpec.params["customFuncSource"])
      #pull out defined function from locals
      self.evalError = locals()["getError"]
    elif "customFuncDef" in metricSpec.params:
      assert not "customFuncSource" in metricSpec.params
      assert not "customExpr" in metricSpec.params
      self.evalError = metricSpec.params["customFuncDef"]

  def getPrediction(self,n):
    #Get prediction from n steps ago
    return self.recordStore.getItem(n)["prediction"]

  def getFieldValue(self,n,field):
    #Get field value from record n steps ago
    record = self.recordStore.getItem(n)["record"]
    value = record[field]
    return value

  def getGroundTruth(self,n):
    #Get the groundTruth from n steps ago
    return self.recordStore.getItem(n)["groundTruth"]

  def getBufferLen(self):
    return len(self.recordStore)

  def storeData(self,name,obj):
    #Store custom user data
    self.userDataStore[name] = obj

  def getData(self,name):
    #Retrieve user data
    if name in self.userDataStore:
      return self.userDataStore[name]
    return None

  def mostLikely(self, pred):
    """ Helper function to return a scalar value representing the most
        likely outcome given a probability distribution
    """
    if len(pred) == 1:
      return pred.keys()[0]

    mostLikelyOutcome = None
    maxProbability = 0

    for prediction, probability in pred.items():
      if probability > maxProbability:
        mostLikelyOutcome = prediction
        maxProbability = probability

    return mostLikelyOutcome

  def expValue(self, pred):
    """ Helper function to return a scalar value representing the expected
        value of a probability distribution
    """
    if len(pred) == 1:
      return pred.keys()[0]

    return sum([x*p for x,p in pred.items()])

  def evalAbsErr(self,pred,ground):
    return abs(pred-ground)

  def getMetric(self):
    return {'value': self.averageError, "stats" : {"steps" : self.steps}}

  def addInstance(self, groundTruth, prediction, record = None, result = None):

    #If missing data,
    if groundTruth == SENTINEL_VALUE_FOR_MISSING_DATA or prediction is None:
      return self.averageError

    self.recordStore.pushToEnd({"groundTruth":groundTruth,
                                         "prediction":prediction,"record":record})

    if isinstance(prediction, dict):
      assert not any(True for p in prediction if p is None), \
        "Invalid prediction of `None` in call to %s.addInstance()" % \
          self.__class__.__name__

    error = self.evalError(prediction,groundTruth,self)
    popped = self.errorStore.pushToEnd({"error":error})
    if not popped is None:
      #Subtract error that dropped out of the buffer
      self.error -= popped["error"]
    self.error+= error
    self.averageError =  float(self.error)/self.errorStore.elements
    self.steps+=1

    return self.averageError



class MetricMovingMode(AggregateMetric):
  """
  Computes error metric based on moving mode prediction.
  """


  def __init__(self, metricSpec):

    super(MetricMovingMode, self).__init__(metricSpec)

    self.mode_window = 100
    if metricSpec.params.has_key('mode_window'):
      assert metricSpec.params['mode_window'] >= 1
      self.mode_window = metricSpec.params['mode_window']

    # Only supports one stepsize
    assert len(self._predictionSteps) == 1

    # Construct moving average instance
    self._movingMode = _MovingMode(self.mode_window)

  def getMetric(self):
    return self._subErrorMetrics[0].getMetric()

  def addInstance(self, groundTruth, prediction, record = None, result = None):

    # If missing data,
    if groundTruth == SENTINEL_VALUE_FOR_MISSING_DATA:
      return self._subErrorMetrics[0].aggregateError

    if self.verbosity > 0:
      print "groundTruth:\n%s\nPredictions:\n%s\n%s\n" % (groundTruth, prediction,
                                                          self.getMetric())

    # Use ground truth from 'steps' steps ago as our most recent ground truth
    lastGT = self._getShiftedGroundTruth(groundTruth)
    if lastGT is None:
      return self._subErrorMetrics[0].aggregateError

    mode = self._movingMode(lastGT)

    result = self._subErrorMetrics[0].addInstance(groundTruth, mode, record)
    return result



class MetricTrivial(AggregateMetric):
  """
  Computes a metric against the ground truth N steps ago. The metric to
  compute is designated by the ``errorMetric`` entry in the metric params.
  """

  def __init__(self, metricSpec):

    # This metric assumes a default 'steps' of 1
    if not 'steps' in metricSpec.params:
      metricSpec.params['steps'] = 1

    super(MetricTrivial, self).__init__(metricSpec)

    # Only supports one stepsize
    assert len(self._predictionSteps) == 1

    # Must have a suberror metric
    assert self._subErrorMetrics is not None, "This metric requires that you" \
        + " specify the name of another base metric  via the 'errorMetric' " \
        + " parameter."

  def getMetric(self):
    return self._subErrorMetrics[0].getMetric()

  def addInstance(self, groundTruth, prediction, record = None, result = None):

    # Use ground truth from 'steps' steps ago as our "prediction"
    prediction = self._getShiftedGroundTruth(groundTruth)

    if self.verbosity > 0:
      print "groundTruth:\n%s\nPredictions:\n%s\n%s\n" % (groundTruth,
                                            prediction, self.getMetric())
    # If missing data,
    if groundTruth == SENTINEL_VALUE_FOR_MISSING_DATA:
      return self._subErrorMetrics[0].aggregateError

    # Our "prediction" is simply what happened 'steps' steps ago
    return self._subErrorMetrics[0].addInstance(groundTruth, prediction, record)



class MetricTwoGram(AggregateMetric):
  """
  Computes error metric based on one-grams. The groundTruth passed into
  this metric is the encoded output of the field (an array of 1's and 0's).
  """


  def __init__(self, metricSpec):

    # This metric assumes a default 'steps' of 1
    if not 'steps' in metricSpec.params:
      metricSpec.params['steps'] = 1

    super(MetricTwoGram, self).__init__(metricSpec)

    # Only supports 1 stepsize
    assert len(self._predictionSteps) == 1

    # Must supply the predictionField
    assert(metricSpec.params.has_key('predictionField'))
    self.predictionField = metricSpec.params['predictionField']
    self.twoGramDict = dict()

  def getMetric(self):
    return self._subErrorMetrics[0].getMetric()

  def addInstance(self, groundTruth, prediction, record = None, result = None):

    # If missing data return previous error (assuming one gram will always
    #  receive an instance of ndarray)
    if groundTruth.any() == False:
      return self._subErrorMetrics[0].aggregateError

    # Get actual ground Truth value from record. For this metric, the
    # "groundTruth" parameter is the encoder output and we use actualGroundTruth
    # to hold the input to the encoder (either a scalar or a category string).
    #
    # We will use 'groundTruthKey' (the stringified encoded value of
    # groundTruth) as the key for our one-gram dict and the 'actualGroundTruth'
    # as the values in our dict, which are used to compute our prediction.
    actualGroundTruth = record[self.predictionField]

    # convert binary array to a string
    groundTruthKey = str(groundTruth)

    # Get the ground truth key from N steps ago, that is what we will base
    #  our prediction on. Note that our "prediction" is the prediction for the
    #  current time step, to be compared to actualGroundTruth
    prevGTKey = self._getShiftedGroundTruth(groundTruthKey)

    # -------------------------------------------------------------------------
    # Get the prediction based on the previously known ground truth
    # If no previous, just default to "" or 0, depending on the groundTruth
    #  data type.
    if prevGTKey == None:
      if isinstance(actualGroundTruth,str):
        pred = ""
      else:
        pred = 0

    # If the previous was never seen before, create a new dict for it.
    elif not prevGTKey in self.twoGramDict:
      if isinstance(actualGroundTruth,str):
        pred = ""
      else:
        pred = 0
      # Create a new dict for it
      self.twoGramDict[prevGTKey] = {actualGroundTruth:1}

    # If it was seen before, compute the prediction from the past history
    else:
      # Find most often occurring 1-gram
      if isinstance(actualGroundTruth,str):
        # Get the most frequent category that followed the previous timestep
        twoGramMax = max(self.twoGramDict[prevGTKey].items(), key=itemgetter(1))
        pred = twoGramMax[0]

      else:
        # Get average of all possible values that followed the previous
        # timestep
        pred = sum(self.twoGramDict[prevGTKey].iterkeys())
        pred /= len(self.twoGramDict[prevGTKey])

      # Add current ground truth to dict
      if actualGroundTruth in self.twoGramDict[prevGTKey]:
        self.twoGramDict[prevGTKey][actualGroundTruth] += 1
      else:
        self.twoGramDict[prevGTKey][actualGroundTruth] = 1

    if self.verbosity > 0:
      print "\nencoding:%s\nactual:%s\nprevEncoding:%s\nprediction:%s\nmetric:%s" % \
          (groundTruth, actualGroundTruth, prevGTKey, pred, self.getMetric())

    return self._subErrorMetrics[0].addInstance(actualGroundTruth, pred, record)



class MetricAccuracy(AggregateMetric):
  """
  Computes simple accuracy for an enumerated type. all inputs are treated as
  discrete members of a set, therefore for example 0.5 is only a correct
  response if the ground truth is exactly 0.5. Inputs can be strings, integers,
  or reals.
  """

  def accumulate(self, groundTruth, prediction, accumulatedError, historyBuffer, result = None):

    # This is really an accuracy measure rather than an "error" measure
    error = 1.0 if groundTruth == prediction else 0.0
    accumulatedError += error

    if historyBuffer is not None:
      historyBuffer.append(error)
      if len(historyBuffer) > self.spec.params["window"] :
        accumulatedError -= historyBuffer.popleft()

    return accumulatedError

  def aggregate(self, accumulatedError, historyBuffer, steps):
    n = steps
    if historyBuffer is not None:
      n = len(historyBuffer)

    return accumulatedError/ float(n)



class MetricAveError(AggregateMetric):
  """
  Simply the inverse of the Accuracy metric.  More consistent with scalar 
  metrics because they all report an error to be minimized.
  """

  def accumulate(self, groundTruth, prediction, accumulatedError, historyBuffer, result = None):

    error = 1.0 if groundTruth != prediction else 0.0
    accumulatedError += error

    if historyBuffer is not None:
      historyBuffer.append(error)
      if len(historyBuffer) > self.spec.params["window"] :
        accumulatedError -= historyBuffer.popleft()

    return accumulatedError

  def aggregate(self, accumulatedError, historyBuffer, steps):
    n = steps
    if historyBuffer is not None:
      n = len(historyBuffer)

    return accumulatedError/ float(n)



class MetricNegAUC(AggregateMetric):
  """ 
  Computes -1 * AUC (Area Under the Curve) of the ROC (Receiver Operator
  Characteristics) curve. We compute -1 * AUC because metrics are optimized to 
  be LOWER when swarming.

  For this, we assuming that category 1 is the "positive" category and we are 
  generating an ROC curve with the TPR (True Positive Rate) of category 1 on the 
  y-axis and the FPR (False Positive Rate) on the x-axis.
  """

  def accumulate(self, groundTruth, prediction, accumulatedError, historyBuffer, result = None):
    """ 
    Accumulate history of groundTruth and "prediction" values.

    For this metric, groundTruth is the actual category and "prediction" is a
    dict containing one top-level item with a key of 0 (meaning this is the
    0-step classificaton) and a value which is another dict, which contains the
    probability for each category as output from the classifier. For example,
    this is what "prediction" would be if the classifier said that category 0
    had a 0.6 probability and category 1 had a 0.4 probability: {0:0.6, 1: 0.4}
    """

    # We disable it within aggregate() if we find that the classifier classes
    #  are not compatible with AUC calculations.
    if self.disabled:
      return 0

    # Just store the groundTruth, probability into our history buffer. We will
    #  wait until aggregate gets called to actually compute AUC.
    if historyBuffer is not None:
      historyBuffer.append((groundTruth, prediction[0]))
      if len(historyBuffer) > self.spec.params["window"] :
        historyBuffer.popleft()

    # accumulatedError not used in this metric
    return 0

  def aggregate(self, accumulatedError, historyBuffer, steps):

    # If disabled, do nothing.
    if self.disabled:
      return 0.0

    if historyBuffer is not None:
      n = len(historyBuffer)
    else:
      return 0.0

    # For performance reasons, only re-compute this every 'computeEvery' steps
    frequency = self.spec.params.get('computeEvery', 1)
    if ((steps+1) % frequency) != 0:
      return self.aggregateError

    # Compute the ROC curve and the area underneath it
    actuals = [gt for (gt, probs) in historyBuffer]
    classes = np.unique(actuals)

    # We can only compute ROC when we have at least 1 sample of each category
    if len(classes) < 2:
      return -1 * 0.5

    # Print warning the first time this metric is asked to be computed on a
    #  problem with more than 2 classes
    if sorted(classes) != [0,1]:
      print "WARNING: AUC only implemented for binary classifications where " \
          "the categories are category 0 and 1. In this network, the " \
          "categories are: %s" % (classes)
      print "WARNING: Computation of this metric is disabled for the remainder of " \
            "this experiment."
      self.disabled = True
      return 0.0

    # Compute the ROC and AUC. Note that because we are online, there's a
    #  chance that some of the earlier classification probabilities don't
    #  have the True class (category 1) yet because it hasn't been seen yet.
    #  Therefore, we use probs.get() with a default value of 0.
    scores = [probs.get(1, 0) for (gt, probs) in historyBuffer]
    (fpr, tpr, thresholds) = roc.ROCCurve(actuals, scores)
    auc = roc.AreaUnderCurve(fpr, tpr)

    # Debug?
    if False:
      print
      print "AUC metric debug info (%d steps):" % (steps)
      print " actuals:", actuals
      print " probabilities:", ["%.2f" % x for x in scores]
      print " fpr:", fpr
      print " tpr:", tpr
      print " thresholds:", thresholds
      print " AUC:", auc

    return -1 * auc



class MetricMultiStep(AggregateMetric):
  """
  This is an "uber" metric which is used to apply one of the other basic
  metrics to a specific step in a multi-step prediction.

  The specParams are expected to contain:
  
  - ``errorMetric``: name of basic metric to apply
  - ``steps``: compare prediction['steps'] to the current ground truth.

  Note that the metrics manager has already performed the time shifting
  for us - it passes us the prediction element from 'steps' steps ago
  and asks us to compare that to the current ground truth.

  When multiple steps of prediction are requested, we average the results of
  the underlying metric for each step.
  """
  def __init__(self, metricSpec):

    super(MetricMultiStep, self).__init__(metricSpec)

    assert self._subErrorMetrics is not None

  def getMetric(self):
    return {'value': self.aggregateError, "stats" : {"steps" : self.steps}}


  def addInstance(self, groundTruth, prediction, record = None, result = None):

    # If missing data,
    if groundTruth == SENTINEL_VALUE_FOR_MISSING_DATA:
      return self.aggregateError

    # Get the prediction for this time step
    aggErrSum = 0
    try:
      for step, subErrorMetric in \
                  zip(self._predictionSteps, self._subErrorMetrics):

        stepPrediction = prediction[step]
        # Unless this is a custom_error_metric, when we have a dict of
        #  probabilities, get the most probable one. For custom error metrics,
        #  we pass the probabilities in so that it can decide how best to deal with
        #  them.
        if isinstance(stepPrediction, dict) \
            and not isinstance(subErrorMetric, CustomErrorMetric):
          predictions = [(prob,value) for (value, prob) in \
                                                    stepPrediction.iteritems()]
          predictions.sort()
          stepPrediction = predictions[-1][1]

        # Get sum of the errors
        aggErr = subErrorMetric.addInstance(groundTruth, stepPrediction, record, result)
        if self.verbosity >= 2:
          print "MetricMultiStep %s: aggErr for stepSize %d: %s" % \
                  (self._predictionSteps, step, aggErr)

        aggErrSum += aggErr
    except:
      pass


    # Return average aggregate error across all step sizes
    self.aggregateError = aggErrSum / len(self._subErrorMetrics)
    if self.verbosity >= 2:
      print "MetricMultiStep %s: aggErrAvg: %s" % (self._predictionSteps,
                                                   self.aggregateError)
    self.steps += 1

    if self.verbosity >= 1:
      print "\nMetricMultiStep %s: \n  groundTruth:  %s\n  Predictions:  %s" \
            "\n  Metric:  %s" % (self._predictionSteps, groundTruth, prediction,
                                 self.getMetric())

    return self.aggregateError



class MetricMultiStepProbability(AggregateMetric):
  """
  This is an "uber" metric which is used to apply one of the other basic
  metrics to a specific step in a multi-step prediction.

  The specParams are expected to contain:
  
  - ``errorMetric``: name of basic metric to apply
  - ``steps``: compare prediction['steps'] to the current ground truth.


  Note that the metrics manager has already performed the time shifting
  for us - it passes us the prediction element from 'steps' steps ago
  and asks us to compare that to the current ground truth.
  """
  def __init__(self, metricSpec):


    # Default window should be 1
    if not 'window' in metricSpec.params:
      metricSpec.params['window'] = 1

    super(MetricMultiStepProbability, self).__init__(metricSpec)

    # Must have a suberror metric
    assert self._subErrorMetrics is not None, "This metric requires that you" \
        + " specify the name of another base metric  via the 'errorMetric' " \
        + " parameter."

    # Force all subErrorMetric windows to 1. This is necessary because by
    #  default they each do their own history averaging assuming that their
    #  addInstance() gets called once per interation. But, in this metric
    #  we actually call into each subErrorMetric multiple times per iteration
    for subErrorMetric in self._subErrorMetrics:
      subErrorMetric.window = 1
      subErrorMetric.spec.params['window'] = 1

    self._movingAverage = MovingAverage(self.window)

  def getMetric(self):
    return {'value': self.aggregateError, "stats" :
            {"steps" : self.steps}}

  def addInstance(self, groundTruth, prediction, record = None, result = None):

    # If missing data,
    if groundTruth == SENTINEL_VALUE_FOR_MISSING_DATA:
      return self.aggregateError

    if self.verbosity >= 1:
      print "\nMetricMultiStepProbability %s: \n  groundTruth:  %s\n  " \
            "Predictions:  %s" % (self._predictionSteps, groundTruth,
                                  prediction)

    # Get the aggregateErrors for all requested step sizes and average them
    aggErrSum = 0
    for step, subErrorMetric in \
                zip(self._predictionSteps, self._subErrorMetrics):

      stepPrediction = prediction[step]

      # If it's a dict of probabilities, get the expected value
      error = 0
      if isinstance(stepPrediction, dict):
        expectedValue = 0
        # For every possible prediction multiply its error by its probability
        for (pred, prob) in stepPrediction.iteritems():
          error += subErrorMetric.addInstance(groundTruth, pred, record) \
                    * prob
      else:
        error += subErrorMetric.addInstance(groundTruth, stepPrediction,
                                            record)

      if self.verbosity >= 2:
          print ("MetricMultiStepProbability %s: aggErr for stepSize %d: %s" %
                 (self._predictionSteps, step, error))

      aggErrSum += error


    # Return aggregate error
    avgAggErr = aggErrSum / len(self._subErrorMetrics)
    self.aggregateError = self._movingAverage(avgAggErr)
    if self.verbosity >= 2:
      print ("MetricMultiStepProbability %s: aggErr over all steps, this "
             "iteration (%d): %s" % (self._predictionSteps, self.steps, avgAggErr))
      print ("MetricMultiStepProbability %s: aggErr moving avg: %s" %
             (self._predictionSteps, self.aggregateError))
    self.steps += 1

    if self.verbosity >= 1:
      print "MetricMultiStepProbability %s: \n  Error: %s\n  Metric:  %s" % \
              (self._predictionSteps, avgAggErr, self.getMetric())

    return self.aggregateError



class MetricMulti(MetricsIface):
  """
  Multi metric can combine multiple other (sub)metrics and weight them to 
  provide combined score.
  """

  def __init__(self, metricSpec):
    """MetricMulti constructor using metricSpec is not allowed."""
    raise ValueError("MetricMulti cannot be constructed from metricSpec string! "
                     "Use MetricMulti(weights,metrics) constructor instead.")

  def __init__(self, weights, metrics, window=None):
    """MetricMulti
       @param weights - [list of floats] used as weights
       @param metrics - [list of submetrics]
       @param window - (opt) window size for moving average, or None when disabled
    """
    if (weights is None or not isinstance(weights, list) or
                          not len(weights) > 0 or
                          not isinstance(weights[0], float)):
      raise ValueError("MetricMulti requires 'weights' parameter as a [list of floats]")
    self.weights = weights

    if (metrics is None or not isinstance(metrics, list) or
                          not len(metrics) > 0 or
                          not isinstance(metrics[0], MetricsIface)):
      raise ValueError("MetricMulti requires 'metrics' parameter as a [list of Metrics]")
    self.metrics = metrics
    if window is not None:
      self.movingAvg = MovingAverage(windowSize=window)
    else:
      self.movingAvg = None


  def addInstance(self, groundTruth, prediction, record = None, result = None):
    err = 0.0
    subResults = [m.addInstance(groundTruth, prediction, record) for m in self.metrics]
    for i in xrange(len(self.weights)):
      if subResults[i] is not None:
        err += subResults[i]*self.weights[i]
      else: # submetric returned None, propagate
        self.err = None
        return None

    if self.verbosity > 2:
      print "IN=",groundTruth," pred=",prediction,": w=",self.weights[i]," metric=",self.metrics[i]," value=",m," err=",err
    if self.movingAvg is not None:
      err=self.movingAvg(err)
    self.err = err
    return err


  def __repr__(self):
    return "MetricMulti(weights=%s, metrics=%s)" % (self.weights, self.metrics)


  def getMetric(self):
    return {'value': self.err, "stats" : {"weights" : self.weights}}

