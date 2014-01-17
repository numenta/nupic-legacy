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


# This file contains utility functions that are used
# by description.py files based on descriptionTempalte.py


from datetime import timedelta
import sys
import itertools
import copy
from collections import defaultdict


from nupic.encoders import (MultiEncoder, DateEncoder, ScalarEncoder)
from nupic.data.aggregator import (generateDataset, getFilename)
from nupic.data.file_record_stream import FileRecordStream
from nupic.frameworks.prediction.callbacks import (printSPCoincidences,
                                                   displaySPCoincidences,
                                                   setAttribute,
                                                   sensorRewind, sensorOpen,
                                                   printSensorOutput,
                                                   setTPAttribute,
                                                   fileSourceAutoRewind,
                                                   setAutoResetInterval,
                                                   printTPTiming)
from nupic.regions.RecordSensorFilters.ModifyFields import ModifyFields


###############################################################################
class ValueGetterBase(object):
  """ Base class for "value getters" (e.g., class DictValueGetter) that are used
  to resolve values of sub-fields after the experiment's config dictionary (in
  description.py) is defined and possibly updated from a sub-experiment.

  This solves the problem of referencing the config dictionary's field from within
  the definition of the dictionary itself (before the dictionary's own defintion
  is complete).

  NOTE: its possible that the referenced value does not yet exist at the
        time of instantiation of a given value-getter future.  It will be
        resolved when the base description.py calls applyValueGettersToConfig().

  NOTE: The constructor of the derived classes MUST call our constructor.
  NOTE: The derived classes MUST override handleGetValue(self).

  NOTE: may be used by base and sub-experiments to derive their own custom value
    getters; however, their use is applicapble only where permitted, as described
    in comments within descriptionTemplate.py.  See class DictValueGetter for
    implementation example.
  """

  class __NoResult(object):
    """ A private class that we use as a special unique value to indicate that
    our result cache instance variable does not hold a valid result.
    """
    pass


  def __init__(self):
    #print("NOTE: ValueGetterBase INITIALIZING")
    self.__inLookup = False
    self.__cachedResult = self.__NoResult


  def __call__(self, topContainer):
    """ Resolves the referenced value.  If the result is already cached,
    returns it to caller. Otherwise, invokes the pure virtual method
    handleGetValue.  If handleGetValue() returns another value-getter, calls
    that value-getter to resolve the value.  This may result in a chain of calls
    that terminates once the value is fully resolved to a non-value-getter value.
    Upon return, the value is fully resolved and cached, so subsequent calls will
    always return the cached value reference.

    topContainer: The top-level container (dict, tuple, or list [sub-]instance)
                  within whose context the value-getter is applied.

    Returns:  The fully-resolved value that was referenced by the value-getter
              instance
    """

    #print("IN ValueGetterBase.__CAll__()")

    assert(not self.__inLookup)

    if self.__cachedResult is not self.__NoResult:
      return self.__cachedResult

    self.__cachedResult = self.handleGetValue(topContainer)

    if isinstance(self.__cachedResult, ValueGetterBase):
      valueGetter = self.__cachedResult
      self.__inLookup = True
      self.__cachedResult = valueGetter(topContainer)
      self.__inLookup = False

    # The value should be full resolved at this point
    assert(self.__cachedResult is not self.__NoResult)
    assert(not isinstance(self.__cachedResult, ValueGetterBase))

    return self.__cachedResult


  def handleGetValue(self, topContainer):
    """ A "pure virtual" method.  The derived class MUST override this method
    and return the referenced value.  The derived class is NOT responsible for
    fully resolving the reference'd value in the event the value resolves to
    another ValueGetterBase-based instance -- this is handled automatically
    within ValueGetterBase implementation.

    topContainer: The top-level container (dict, tuple, or list [sub-]instance)
                  within whose context the value-getter is applied.

    Returns:      The value referenced by this instance (which may be another
                  value-getter instance)
    """
    raise NotImplementedError("ERROR: ValueGetterBase is an abstract " + \
                              "class; base class MUST override handleGetValue()")



###############################################################################
class DictValueGetter(ValueGetterBase):
  """
    Creates a "future" reference to a value within a top-level or a nested
    dictionary.  See also class DeferredDictLookup.
  """
  def __init__(self, referenceDict, *dictKeyChain):
    """
      referenceDict: Explicit reference dictionary that contains the field
                    corresonding to the first key name in dictKeyChain.  This may
                    be the result returned by the built-in globals() function,
                    when we desire to look up a dictionary value from a dictionary
                    referenced by a global variable within the calling module.
                    If None is passed for referenceDict, then the topContainer
                    parameter supplied to handleGetValue() will be used as the
                    reference dictionary instead (this allows the desired module
                    to designate the appropriate reference dictionary for the
                    value-getters when it calls applyValueGettersToContainer())

      dictKeyChain: One or more strings; the first string is a key (that will
                    eventually be defined) in the reference dictionary. If
                    additional strings are supplied, then the values
                    correspnding to prior key strings must be dictionaries, and
                    each additionl string references a sub-dictionary of the
                    former. The final string is the key of the field whose value
                    will be returned by handleGetValue().

      NOTE: Its possible that the referenced value does not yet exist at the
            time of instantiation of this class.  It will be resolved when the
            base description.py calls applyValueGettersToConfig().


    Example:
      config = dict(
        _dsEncoderFieldName2_N = 70,
        _dsEncoderFieldName2_W = 5,

        dsEncoderSchema = [
          dict(
            base=dict(
              fieldname='Name2', type='ScalarEncoder',
              name='Name2', minval=0, maxval=270, clipInput=True,
              n=DictValueGetter(None, '_dsEncoderFieldName2_N'),
              w=DictValueGetter(None, '_dsEncoderFieldName2_W')),
            ),
          ],
      )

      updateConfigFromSubConfig(config)
      applyValueGettersToContainer(config)
    """

    # First, invoke base constructor
    ValueGetterBase.__init__(self)

    assert(referenceDict is None or isinstance(referenceDict, dict))
    assert(len(dictKeyChain) >= 1)

    self.__referenceDict = referenceDict
    self.__dictKeyChain = dictKeyChain


  def handleGetValue(self, topContainer):
    """ This method overrides ValueGetterBase's "pure virtual" method.  It
    returns the referenced value.  The derived class is NOT responsible for
    fully resolving the reference'd value in the event the value resolves to
    another ValueGetterBase-based instance -- this is handled automatically
    within ValueGetterBase implementation.

    topContainer: The top-level container (dict, tuple, or list [sub-]instance)
                  within whose context the value-getter is applied.  If
                  self.__referenceDict is None, then topContainer will be used
                  as the reference dictionary for resolving our dictionary key
                  chain.

    Returns:      The value referenced by this instance (which may be another
                  value-getter instance)
    """
    value = self.__referenceDict if self.__referenceDict is not None else topContainer
    for key in self.__dictKeyChain:
      value = value[key]

    return value



###############################################################################
class DeferredDictLookup(DictValueGetter):
  """
    Creates a "future" reference to a value within an implicit dictionary that
    will be passed to applyValueGettersToContainer() in the future (typically
    called by description.py after its config dictionary has been updated from
    the sub-experiment). The reference is relative to the dictionary that will
    be passed to applyValueGettersToContainer()
  """
  def __init__(self, *dictKeyChain):
    """
      dictKeyChain: One or more strings; the first string is a key (that will
                    eventually be defined) in the dictionary that will be passed
                    to applyValueGettersToContainer(). If additional strings are
                    supplied, then the values correspnding to prior key strings
                    must be dictionaries, and each additionl string references a
                    sub-dictionary of the former. The final string is the key of
                    the field whose value will be returned by this value-getter

      NOTE: its possible that the referenced value does not yet exist at the
            time of instantiation of this class.  It will be resolved when the
            base description.py calls applyValueGettersToConfig().


    Example:
      config = dict(
        _dsEncoderFieldName2_N = 70,
        _dsEncoderFieldName2_W = 5,

        dsEncoderSchema = [
          dict(
            base=dict(
              fieldname='Name2', type='ScalarEncoder',
              name='Name2', minval=0, maxval=270, clipInput=True,
              n=DeferredDictLookup('_dsEncoderFieldName2_N'),
              w=DeferredDictLookup('_dsEncoderFieldName2_W')),
            ),
          ],
      )

      updateConfigFromSubConfig(config)
      applyValueGettersToContainer(config)
    """

    # Invoke base (DictValueGetter constructor), passing None for referenceDict,
    # which will force it use the dictionary passed via
    # applyValueGettersToContainer(), instead.
    DictValueGetter.__init__(self, None, *dictKeyChain)



###############################################################################
def fromConfig(key):
  """
  NOTE: this function is DEPRECATED: use DeferredDictLookup class directly instead

  Creates a future for deferred retrieval of a value from a field in the
  experiment's config dictionary, given the variable's key. The value will be
  resolved by the call to applyValueGettersToContainer() from the base
  description.py after its config dictionary has been updated from the
  permutation/sub-experiment.
  """
  return DeferredDictLookup(key)



###############################################################################
def applyValueGettersToContainer(container):
  """
  """
  _applyValueGettersImpl(container=container, currentObj=container,
                         recursionStack=[])



###############################################################################
def _applyValueGettersImpl(container, currentObj, recursionStack):
  """
  """

  # Detect cycles
  if currentObj in recursionStack:
    return

  # Sanity-check of our cycle-detection logic
  assert(len(recursionStack) < 1000)

  # Push the current object on our cycle-detection stack
  recursionStack.append(currentObj)

  # Resolve value-getters within dictionaries, tuples and lists

  if isinstance(currentObj, dict):
    for (key, value) in currentObj.items():
      if isinstance(value, ValueGetterBase):
        currentObj[key] = value(container)

      _applyValueGettersImpl(container, currentObj[key], recursionStack)


  elif isinstance(currentObj, tuple) or isinstance(currentObj, list):
    for (i, value) in enumerate(currentObj):
      # NOTE: values within a tuple should never be value-getters, since
      #       the top-level elements within a tuple are immutable. However,
      #       if any nested sub-elements might be mutable
      if isinstance(value, ValueGetterBase):
        currentObj[i] = value(container)

      _applyValueGettersImpl(container, currentObj[i], recursionStack)

  else:
    pass

  recursionStack.pop()
  return



###############################################################################
def applyValueGettersToConfig(config):
  """
  NOTE: This function has been DEPRECATED.  Use applyValueGettersToContainer
        instead.
  """
  applyValueGettersToContainer(config)



###############################################################################
def getBaseDatasetsImpl(config):
  """ Implementation for description.py getBaseDatasets() entry point function.
  Returns a dictionary containing the dataset paths of the raw training and test
  datasets that we wish to use in this experiment; The value of each key is a
  (possibly relative) path to the raw dataset (pre-aggregation).
  NOTE: keynames are specific to this description script and are not interpreted
    by the framework.

    config:   configuration dictionary from description.py
  """

  datasets= dict()

  # ------------------------------------------------------------------
  # Add the raw dataset paths

  # Add training dataset if training will be performed
  if _isSPTrainingEnabled(config) or _isTPTrainingEnabled(config):
    datasets[_getTrainingDatasetKey(config)] = config['trainDatasetPath']

  # Add the raw inference datasets
  for i, ds in enumerate(config['inferDatasets']):
    key = _datasetKeyFromInferenceDatasetIndex(index=i, config=config)
    assert(key not in datasets)
    datasets[key] = ds['path']

  return datasets



###############################################################################
def getDatasetsImpl(baseDatasets, generate, config):
  """ Implementation for description.py getDatasets() entry point function.
  Given a list of base datasets, returns a list of possibly transformed dataset
  paths to use; if config['aggregationInfo'] is disabled, then an identical
  dataset list is returned.  Optionally, generates new datasets by applying
  transformations specified in config['aggregationInfo'].

    baseDatasets: a dictionaary of base dataset paths, where each key/value pair
                    corresponds to a base (raw) dataset.  The keys are as generated
                    by our getBaseDatasets(); NOTE: the paths are absolute (fixed
                    up by the framework)

    NOTE: Note that the paths in the baseDatasets dict will have been adjusted by
      the prediction framework to point to actual dataset locations as found on
      disk, and are not likely to be the same as the (local) paths initially returned
      by getBaseDatasets

    generate:     if True and config['aggregationInfo'] is enabled, then new
                    datasets will be generated per config['aggregationInfo'];
                    otherwise, new datasets will not be generated

    config:       configuration dictionary from description.py

    Returns:      dictionary of dataset paths to use with same keys as in baseDatasets;
                    the values may differ from baseDatasets as follows: if
                    config['aggregationInfo']  is enabled, then new dataset paths
                    will be generated per config['aggregationInfo'].
  """


  # Aggregation info
  aggInfo = config['aggregationInfo'] if config['aggregationInfo'] else dict()

  datasets = dict()

  targetPaths = []
  for name in baseDatasets:
    if generate:
      # NOTE: Avoid processing the same dataset more than once, such as when the
      #  same dataset is used for training and inference in some tests
      tempPath = getFilename(aggInfo, baseDatasets[name])
      if tempPath not in targetPaths:
        path = generateDataset(aggInfo, baseDatasets[name])
        assert(path == tempPath)
      else:
        path = tempPath

      targetPaths.append(path)

    else:
      path = getFilename(aggInfo, baseDatasets[name])

    datasets[name] = path


  return datasets



###############################################################################
def getDescriptionImpl(datasets, config):
  """ Implementation for description.py getDescription() entry point function.
  Builds an experiment description dictionary as required by LPF (Lightweight
  Prediction Framework).  Hardcoded data that is less likely to vary between
  experiments is augmented with data from the config dictionary.
  See getBaseDatasets() and getDatasets().

    datasets:     a dictionary of input datasets that may have been pre-processed
                   via aggregation.  Keys:
                   'trainDataset'         -- path to the training dataset
                   'inferDataset.N.alias' -- path(s) to the inference dataset

    config:       configuration dictionary from description.py

    returns:      an experiment description dictionary as required by LPF
  """

  # ----------------------------------------------------------------------------
  # Encoder for the sensor
  encoder = MultiEncoder(_getDatasetEncoderConfig(config))

  # ------------------------------------------------------------------
  # Region params
  CLAParams = _getCLAParams(encoder=encoder, config=config)


  sensorParams = dict(
    # encoder/datasource are not parameters so don't include here
    verbosity=config['sensorVerbosity']
  )

  # Filesource for the sensor. Set the filename in setup functions.
  dataSource = FileRecordStream('foo')

  description = dict(
    options = dict(
      logOutputsDuringInference = False,
      ),

    network = dict(

      # Think of sensor as a shell with dataSource and encoder;
      # Encoder has a pre-encoder and post-encoder filters;
      # filters appear in a different place (TODO: where?)
      sensorDataSource = dataSource,
      sensorEncoder = encoder,

      # LPF converts this to JSON strings; used as constructor args; has simple
      # types (ints, strings, floats)
      sensorParams = sensorParams,

      # CLA class; py. prefix for class names implemented in python; older code
      # implemented regions in C++ and designated class name without prefix.
      CLAType = 'py.CLARegion',
      # dict converted to JSON string
      CLAParams = CLAParams,

      # classifiers are presently not used (formerly used by vision code); should
      # be okay to leave out Classifier, sensor, CLA
      classifierType = None,
      classifierParams = None),
  )

  # ----------------------------------------------------------------------------
  # Configure Training and Inference phases
  # ----------------------------------------------------------------------------
  #
  # phase is 0 or more steps (a list of dictionaries, each dict corresponds to one step)
  # (see py/nupic/frameworks/prediction/experiment.py docstring)
  #
  # step = dict (name, setup, iter, finish, iterationCount)
  #   setup, iter, finish are callbacks;
  #
  # name: step name string; optional, used for printing messages to console
  # setup: open input file (e.g., via dataSource), print stats, etc.
  # iter: for diagnostics/debugging; called by net.run between iterations.
  # finish: called at the end by net.run; usually prints out stats (e.g., how many
  #   synapses, time taken, etc.)
  # callbacks are almost always reused, so they are not experiment-specific (see
  #   imports at top of file)
  # a callback always has this form c(experiment_obj, iter_number); can get
  #   experiment.network.regions["sensor"].getSelf()

  spEnable = config['spEnable']
  spTrain = _isSPTrainingEnabled(config)

  tpEnable = config['tpEnable']
  tpTrain = _isTPTrainingEnabled(config)
  # NOTE: presently, we always train TP (during training phase) if TP is enabled
  assert(tpTrain == tpEnable)

  # At least one of SP/TP must be enabled for a meaningful system
  assert(spEnable or tpEnable)

  # NOTE: SP and Spatial regression need to undergo training over the same
  #       set of rows. Since we're not reading the training dataset here to
  #       find out the number of rows, we presently configure both with the
  #       same auto-rewind setting.
  # TODO: this may cause knn training to repeatedly iterate unnecessarily
  #       over the same records in case spTrainIterationCount is larger than the
  #       nuber of rows in the training dataset. Look into optimizing this to
  #       avoid wasting time on knn training due to unnecessary iterations, but
  #       make sure that both SP and knn train on the exact same rows.
  spTrainMayNeedAutoRewind = True \
                             if config['spTrainIterationCount'] is not None \
                             else False


  # ----------------------------------------------------------------------------
  # SP training
  if spTrain:
    description['spTrain'] = []
    for i in xrange(config['spTrainNPasses']):
      stepDict = dict(
        name='sp.train.pass_%d' % (i),
        iterationCount=config['spTrainIterationCount'],
        setup=[sensorOpen(datasets[_getTrainingDatasetKey(config)]) if i==0 \
                 else sensorRewind,
               fileSourceAutoRewind(spTrainMayNeedAutoRewind),],
        finish=[fileSourceAutoRewind(False),],
      )

      description['spTrain'].append(stepDict)

  elif spEnable:
    description['spTrain'] = dict(
      # need to train with one iteration just to initialize data structures
      # TODO: seems like a hack; shouldn't CLA framework automatically initialize
      #   the necessary subsystems? (ask Ron)
      iterationCount=1,
    )


  # ----------------------------------------------------------------------------
  # TP training
  if tpTrain:
    description['tpTrain'] = []
    mayNeedAutoRewind = True if config['tpTrainIterationCount'] is not None else False
    for i in xrange(config['tpTrainNPasses']):
      stepDict = dict(
        name='tp.train.pass_%d' % (i),
        iterationCount=config['tpTrainIterationCount'],
        setup=[
          sensorOpen(datasets[_getTrainingDatasetKey(config)]) if i==0 \
            else sensorRewind,
          fileSourceAutoRewind(mayNeedAutoRewind),
          ],
        finish=[fileSourceAutoRewind(False),],
        )
      if config['tpTrainPrintStatsPeriodIter'] > 0:
        stepDict['iter'] = printTPTiming(config['tpTrainPrintStatsPeriodIter'])
        stepDict['finish'] += [printTPTiming()] #, printTPCells]

      description['tpTrain'].append(stepDict)


  # ----------------------------------------------------------------------------
  # Inference tests
  # NOTE: Presently, SP and TP learning is disabled during inference
  description['infer'] = []

  predictionFields = None
  spatialRegrTests = None
  if 'spFieldPredictionSchema' in config and config['spFieldPredictionSchema'] != None:
    if len(config['spFieldPredictionSchema']['predictionFields']) > 0:
      spFieldPredictionSchema = config['spFieldPredictionSchema']
      predictionFields = spFieldPredictionSchema['predictionFields']
      if len(spFieldPredictionSchema['regressionTests']) > 0:
        # presently, our spatial regression modules (knn and linear) don't support
        # multiple fields
        assert(len(predictionFields) == 1)
        spatialRegrTests = spFieldPredictionSchema['regressionTests']


  # Set up test steps for all inference datasets
  for i, ds in enumerate(config['inferDatasets']):

    datasetInfo = config['inferDatasets'][i]

    # NOTE: the path/contents may differ from the corresponding dataset
    #       referenced in config['inferDatasets'] due to preprocessing (e.g.,
    #       aggregation)
    inferenceDatasetKey = \
      _datasetKeyFromInferenceDatasetIndex(index=i, config=config)
    inferenceDatasetPath = datasets[inferenceDatasetKey]


    # ----------------------------------------
    # Step: Temporal inference
    #
    if tpEnable:

      # Turn off plot histograms when running under darwin
      plotTemporalHistograms = True
      if sys.platform.startswith('darwin'):
        plotTemporalHistograms = False
        print "Turning off plotTemporalHistograms under darwin"

      temporalTestingStep = dict(
        name = getTemporalInferenceStepName(datasetInfo['alias'], i),
        iterationCount = ds['iterCount'],
        setup = [sensorOpen(inferenceDatasetPath)],
        ppOptions = dict(verbosity=config['postprocVerbosity'],
                         plotTemporalHistograms=plotTemporalHistograms,
                         printLearnedCoincidences=False,
                         logPredictions=True,)
      )
      description['infer'].append(temporalTestingStep)
    else:
      print 'temporalTestingStep skipped.'

    # ----------------------------------------
    # Step: Non-temporal Regression algorithm training (if enabled)
    #
    if spatialRegrTests:
      # NOTE: we don't need auto-rewind when training spatial regression algorithms
      regrTrainStep = dict(
        name = ('%s_nontemporal.training') % \
                 (_normalizeDatasetAliasNameForStepName(datasetInfo['alias']),),
        iterationCount=config['spTrainIterationCount'],
        setup=[sensorOpen(datasets[_getTrainingDatasetKey(config)]),
               fileSourceAutoRewind(spTrainMayNeedAutoRewind),],
        ppOptions = dict(verbosity=config['postprocVerbosity'],
                         printLearnedCoincidences=False,)
      )

      # Add Spatial Regression algorithm training requests
      ppOptions = regrTrainStep['ppOptions']
      for test in spatialRegrTests:
        assert(len(predictionFields) == 1)
        ppOptions[test['algorithm']] = 'train,%s' % (predictionFields[0])

      description['infer'].append(regrTrainStep)


    # ----------------------------------------
    # Step: Non-temporal Inference
    #
    nontemporalTestingStep = dict(
      name = getNonTemporalInferenceStepName(datasetInfo['alias'], i),
      iterationCount = ds['iterCount'],
      setup = [
        sensorOpen(inferenceDatasetPath),
        fileSourceAutoRewind(False),
        # TODO Do we need to turn off collectStats in the 'finish' sub-step?
        setTPAttribute('collectStats', 1),
        ],
      # TODO which ppOptions do we want in this template?
      ppOptions = dict(
        verbosity=config['postprocVerbosity'],
        plotTemporalHistograms=False,
        printLearnedCoincidences=False,
        logPredictions=True,
        ),
      )

    # Add Spatial Field Prediction options to inference step
    if predictionFields:
      # Set sparse encodings of prediction fields to zero
      setup = nontemporalTestingStep['setup']
      setup.append(
        setAttribute('sensor', 'postEncodingFilters',
                     [ModifyFields(fields=predictionFields, operation='setToZero')])
      )
    if spatialRegrTests:
      # Add regression test requests
      ppOptions = nontemporalTestingStep['ppOptions']
      for test in spatialRegrTests:
        assert(len(predictionFields) == 1)
        ppOptions[test['algorithm']] = 'test,%s' % (predictionFields[0])

    description['infer'].append(nontemporalTestingStep)


  # ----------------------------------------------------------------------------
  # Add auto-reset intervals to the sensor region for tpTrain and Infer phases
  # (if config['sensorAutoReset'] is enabled)
  # ----------------------------------------------------------------------------
  if 'sensorAutoReset' in config and config['sensorAutoReset'] is not None:
    dd = defaultdict(lambda: 0,  config['sensorAutoReset'])
    # class timedelta([days[, seconds[, microseconds[, milliseconds[, minutes[,
    #                 hours[, weeks]]]]]]])
    if not (0 == dd['days'] == dd['hours'] == dd['minutes'] == dd['seconds'] \
            == dd['milliseconds'] == dd['microseconds'] == dd['weeks']):
      timeDelta = timedelta(days=dd['days'],
                            hours=dd['hours'],
                            minutes=dd['minutes'],
                            seconds=dd['seconds'],
                            milliseconds=dd['milliseconds'],
                            microseconds=dd['microseconds'],
                            weeks=dd['weeks'])

      tpTrainSteps = description['tpTrain'] if 'tpTrain' in description else []
      inferSteps = description['infer'] if 'infer' in description else []
      for step in itertools.chain(tpTrainSteps, inferSteps):
        if 'setup' not in step:
          step['setup'] = []
        step['setup'].append(setAutoResetInterval(timeDelta))

  return description
  # end of getDescriptionImpl()



###############################################################################
def getTemporalInferenceStepName(datasetAlias, datasetIndex):
  """
  Construct the step name for a temporal inference step.  May also be called
  by external code (e.g., ScanOTron) duriong generation of permutations.py

  datasetAlias:   'alias' property value from the dataset's element in
                  config['inferDatasets']
  datasetIndex:   0-based index of the dataset's element in
                  config['inferDatasets'] list (ignored, for now)

  Returns:        Name of the Temporal inference step corresponding to the given
                  dataset information
  """
  stepName = ("%s_temporal.prediction") % \
                (_normalizeDatasetAliasNameForStepName(datasetAlias),)

  return stepName




###############################################################################
def getNonTemporalInferenceStepName(datasetAlias, datasetIndex):
  """
  Construct the step name for a non-temporal inference step.  May also be called
  by external code (e.g., ScanOTron) during generation of permutations.py

  datasetAlias:   'alias' property value from the dataset's element in
                  config['inferDatasets']
  datasetIndex:   0-based index of the dataset's element in
                  config['inferDatasets'] list (ignored, for now)

  Returns:        Name of the Non-temporal inference step corresponding to the
                  given dataset information
  """
  stepName = ("%s_nontemporal.prediction") % \
                (_normalizeDatasetAliasNameForStepName(datasetAlias),)

  return stepName



###############################################################################
def _normalizeDatasetAliasNameForStepName(datasetAlias):
  """ Process the given dataset alias name (from config['inferDatasets']) to
  make it suitable for inclusion in an inference step name
  """
  return datasetAlias.replace('_', '.')



###############################################################################
def _getCLAParams(encoder, config):
  """
  Generates CLA Parameters dictionary for consumpion by CLARegion.

  encoder:      the configured encoder that will be used with the CLARegion

  config:       configuration dictionary from description.py

  Returns:      CLA Parameters dictionary
  """

  # The inputs are long, horizontal vectors
  inputShape = (1, encoder.getWidth())

  # Layout the coincidences vertically stacked on top of each other, each
  # looking at the entire input field.
  coincidencesShape = (config['claRegionNColumns'], 1)
  inputBorder = inputShape[1]/2
  if inputBorder*2 >= inputShape[1]:
    inputBorder -= 1


  claParams = dict(
    # SP parameters
    spSeed = 1956,
    disableSpatial = 0 if config['spEnable'] else 1,
    spVerbosity = config['spVerbosity'],
    printPeriodicStats = int(config['spPrintStatsPeriodIter']),

    # TODO for Ron M.: [for inputShape through localAreaDensity] Once proper
    # defaults are in SP constructor, consider eliminating these from the
    # description file.
    inputShape = inputShape,
    inputBorder = inputBorder,
    coincidencesShape = coincidencesShape,
    coincInputRadius = inputShape[1]/2,
    coincInputPoolPct = 1.00,
    gaussianDist = 0,
    commonDistributions = 0,    # should be False if possibly not training

    localAreaDensity = -1, # this is an alternative to spNumActivePerInhArea
    numActivePerInhArea = config['spNumActivePerInhArea'],
    stimulusThreshold = 0,

    synPermInactiveDec = 0.01,
    synPermActiveInc = 0.1,
    synPermActiveSharedDec = 0.0,
    synPermOrphanDec = 0.0,

    dutyCyclePeriod = 1000,
    minPctDutyCycleBeforeInh = 0.001,
    minPctDutyCycleAfterInh = 0.001,
    globalInhibition = 1,

    # TP parameters
    tpSeed = 1960,
    disableTemporal = 0 if config['tpEnable'] else 1,
    temporalImp = config['tpImplementation'],
    nCellsPerCol = config['tpNCellsPerCol'] if config['tpEnable']  else 1,

    collectStats = 0,
    burnIn = 2,
    nMultiStepPrediction = 0,
    verbosity = config['tpVerbosity'],

    newSynapseCount = config['spNumActivePerInhArea'] \
                         if config['tpNewSynapseCount'] is None \
                         else config['tpNewSynapseCount'],

    minThreshold = 12 if ('tpMinSegmentMatchSynapseThreshold' not in config or
                          config['tpMinSegmentMatchSynapseThreshold'] == None)
                      else config['tpMinSegmentMatchSynapseThreshold'],

    activationThreshold = 16  if ('tpSegmentActivationThreshold' not in config or
                                  config['tpSegmentActivationThreshold'] == None)
                              else config['tpSegmentActivationThreshold'],

    initialPerm = config['tpInitialPerm'],
    connectedPerm = 0.5,
    permanenceInc = config['tpPermanenceInc'],
    permanenceDec = config['tpPermanenceInc']
                    if config['tpPermanenceDec'] is None
                    else config['tpPermanenceDec'],
    # globalDecay MUST be 0 for "fixed-resource CLA"
    globalDecay = 0.0,

    pamLength = 1,
    # maxAge MUST be 0 for "fixed-resource CLA"
    maxAge = 0,

    maxSegmentsPerCell = config['tpMaxSegmentsPerCell'],
    maxSynapsesPerSegment = config['tpMaxSynapsesPerSegment'],

    # General parameters
    # Control CLA top-down feedback (from TP to SP); Top-down feedback facilitates
    #  sensor predictions; without top-down feedback, only classification is possible.
    # 0=top-down feedback OFF; 1=top-down feedback ON;
    computeTopDown = 1,

    trainingStep = 'spatial',
    )

  if config.has_key('spReconstructionParam'):
    claParams['spReconstructionParam'] = config['spReconstructionParam']

  return claParams



###############################################################################
def _getDatasetEncoderConfig(config):
  """
  Generates an encoder configuration from config['dsEncoderSchema'] that
  describes the field encoders for this experiment's input dataset.

  Example:
    dsEncoderSchema = [
      dict(
        base=dict(fieldname='Name1', type='DateEncoder', timeOfDay=(5,5)),
        ),
      dict(
        base=dict(fieldname='Name2', type='ScalarEncoder',
                  name='Name2', minval=0, maxval=270, clipInput=True,
                  n=70, w=5),
        ),
      dict(
        base=dict(fieldname='Name3', type='SDRCategoryEncoder', name="Name3",
                  n=70, w=5),
        ),
      ]

  config:       configuration dictionary from description.py

  Returns: An encoder configuration tuple that is suitable for passing as an
  argument to nupic.encoders.MultiEncoder()
  """

  encoders = []

  # process field encoder specs in config['dsEncoderSchema']
  for spec in config['dsEncoderSchema']:
    # Get a copy of base field encoder dict from the config dict
    d = copy.deepcopy(spec['base'])

    # Append current field encoder dict to result
    encoders.append(d)

  #print "ENCODERS=", encoders

  return tuple(encoders)



###############################################################################
def _isSPTrainingEnabled(config):
  """
  config:       configuration dictionary from description.py

  Returns True if SP needs to be trained in the training phase
  """

  return (config['spEnable'] and config['spTrain'])



###############################################################################
def _isTPTrainingEnabled(config):
  """
  config:       configuration dictionary from description.py

  Returns True if TP needs to be trained in the training phase
  """
  # TP presently must be trained if it's enabled
  return (config['tpEnable'])



###############################################################################
def _datasetKeyFromInferenceDatasetIndex(index, config):
  """
  Returns a dataset key, given a 0-based index into the inference datasets
  list (config['inferDatasets']). Used by getBaseDatasets() to construct unique
  key names for the inference datasets in the datasets dictionary.
  See _getTrainingDatasetKey()

    index:        0-based index into the inference datasets
                   list (config['inferDatasets']).

    config:       configuration dictionary from description.py
  """
  return 'inferDataset.' + str(index) + '.' + config['inferDatasets'][index]['alias']


###############################################################################
def _getTrainingDatasetKey(config):
  """
  Returns the dataset key for the training dataset.  Used by getBaseDatasets() to
  construct a unique key name for the training dataset in the datasets dictionary.
  NOTE: presently, we only support a single training dataset, so it suffices
    to return a simple string that differs from our other dataset key prefixes.
  See _datasetKeyFromInferenceDatasetIndex()

    config:       configuration dictionary from description.py
  """
  return 'trainDataset'





################################################################################
##"""
##Callback for controlling CLARegion's learning
## NOTE: This was intended to be used for controlling CLARegion's SP/TP learning
##  parameters in the inference phase configuration.  We decided to punt on it
##  for now, but this function may come in handy later.
##"""
##class setCLARegionParameter(object):
##  """Callback for controlling CLARegion's learning parameters. This callback
##  is distinct from the setAttribute() callback in that it calls the region's
##  setParameter() method, that may do more than merely set the attribute's value"""
##  def __init__(self, regionName, parameterName, value):
##    """
##      regionName:     region name string (e.g., 'level1');
##
##      parameterName:  parameterName string (e.g., "trainingStep")
##
##      value:          a value that's appropriate for the parameter
##    """
##    self.regionName = regionName
##    self.parameterName = parameterName
##    self.value = value;
##
##  def __call__(self, experiment, iteration=0):
##    r = experiment.network.regions[self.regionName]
##    assert isinstance(r, CLARegion)
##
##    r.setParameter(self.parameterName, self.value)
