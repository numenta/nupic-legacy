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

import sys
import os
import numpy
import pprint

from nupic.frameworks.prediction.experiment import Experiment
from nupic.engine import Network
from nupic.algorithms.KNNClassifier import KNNClassifier
from nupic.bindings.math import SM32, SparseBinaryMatrix

from classificationstats import  (ClassificationStats,
                                  ClassificationVsBaselineStats)
from inputpredictionstats import (InputPredictionStats,
                                  MultiStepPredictionStats)
from spstats import SPStats
from poormanstats import PoorMansStats
from ngramstats import NGramStats
from knnregressionstats import KNNRegressionStats
from linearregressionstats import LinearRegressionStats


#############################################################################
# utility functions
def _countLinesInFile(filename):
  f = open(filename)
  nlines = 0
  while True:
    line = f.readline()
    if not line:
      break
    nlines += 1
  f.close()
  return nlines


#############################################################################
def _readSparse01VecFromFile(f):
  """ Returns (nz, dense), where nz is the list of non-zeros and
  dense is the dense form of the data

  Returns (None, None) at end of file
  """
  line = f.readline()
  if not line:
    return (None, None)

  #print "filename: ", f.name

  values = numpy.fromstring(line.strip(), numpy.int, sep=" ")
  width = values[0]
  nz = values[1:]

  dense = numpy.zeros((width,), dtype='int')
  dense[nz] = 1
  return (nz, dense)

#############################################################################
def _readSparseVecFromFile(f):
  """ Returns a dense vector of floats.

  Returns None at end of file
  """
  line = f.readline()
  if not line:
    return None

  data = numpy.fromstring(line.strip(), numpy.float32, sep=" ")
  width = int(data[0])

  dense = numpy.zeros((width,), dtype=numpy.float32)
  nzValuePairs = data[1:]
  nzValuePairs.shape = (-1, 2)
  nz = nzValuePairs[:,0].astype('int')
  values = nzValuePairs[:,1]
  dense[nz] = values

  return dense


#############################################################################
def _readDenseVecFromFile(f):
  """ Returns a dense vector of floats

  Returns None at end of file
  """
  line = f.readline()
  if not line:
    return None
  values = numpy.fromstring(line.strip(), numpy.float32, sep=" ")
  return values


#############################################################################
def _readIntFromFile(f):
  line = f.readline()
  if not line:
    return None
  return int(line.strip())

#############################################################################
def _readMultiStepPrediction(f):
  nSteps = _readIntFromFile(f)
  if nSteps is None:
    return None
  multiStepPrediction = []
  for i in range(nSteps):
    spTopDownOut = _readDenseVecFromFile(f)
    multiStepPrediction.append(spTopDownOut)
  return multiStepPrediction


#############################################################################
def _getFilenameForOutputs(directory, datasetName, testVariant, outputName):
  return os.path.join(directory, "%s_%s_%s.txt" % (datasetName, testVariant,
                        outputName))


#############################################################################
def _analyzeTrainedNet(net, options):
  """ Analyze the trained network and return a dict containing auxiliary
  information that will be used when analyzing each inference run.

  Parameter:
  -----------------------------------------------------------
  net:              The trained network.
  options:          dictionary of post-processing options.

  retval:           Dictionary of auxiliary information about this network,
                      like the set of learned coincidences from the SP, etc.
  """

  print "\n-------------------------------------------------------------------"
  print "Analyzing the trained network..."

  # ---------------------------------------------------------------------------
  # Get the objects we need from the network
  sp = net.regions['level1'].getSelf()._sfdr
  encoder = net.regions['sensor'].getSelf().encoder

  if sp:
    # Reqired?
    sp._updateInhibitionObj()

    # ---------------------------------------------------------------------------
    # Get the learned coincidences for each column into cm.
    cm = SM32(0, sp.inputShape[0] * sp.inputShape[1])

    outputSize = sp.coincidencesShape[0] * sp.coincidencesShape[1]
    for i in xrange(outputSize):
      denseRow = sp.getLearnedCmRowAsDenseArray(i)
      cm.addRow(denseRow)

    # ===========================================================================
    # Print out the results
    print "\nSP Learning stats:"
    pprint.pprint(sp.getLearningStats())

  else:
    cm = None
    # sp output size is sp input size (if no sp)
    outputSize = net.regions['level1'].getInputData('bottomUpIn').shape[0]
  # ---------------------------------------------------------------------------
  # Parameters for multi-step prediction analysis
  nMultiStepPrediction = net.regions['level1'].getParameter("nMultiStepPrediction")
  burnIn = net.regions['level1'].getParameter("burnIn")

  # ===========================================================================
  # Return info
  return dict(net = net,
              sp = sp,
              cm = cm,
              encoder = encoder,
              outputSize = outputSize,
              nMultiStepPrediction=nMultiStepPrediction,
              burnIn=burnIn,
              )



#############################################################################
def _processTestOptions(optionsIn):

  """ Process the options given to an inference test run. This validates
  the options specified by the user as part of the 'ppOptions' dictionary
  key of the experiment's inference run.

  It returns a dict with all of the valid options, defaults filled in

  """

  # Default values of all options
  optionsOut = dict(
      help = False,
      onlyClassificationAcc = False,
      printLearnedCoincidences = True,
      computeDistances = False,
      tpActivationThresholds = [8],
      verbosity = 0,
      nGrams = None,
      burnIns = [1],
      ipsAt = [],
      ipsDetailsFor = None,
      displayMultiStepPrediction = False,
      plotTemporalHistograms = False,
      knnRegression = 'None,None',
      linearRegression = 'None,None',
      logPredictions = False,
      )


  # Create the total list of options
  validKeys = optionsOut.keys()

  # Special treatment for the onlyClassificationAcc option - it turns off all
  #  other print options by default
  if optionsIn.get('onlyClassificationAcc', False):
    optionsOut['printLearnedCoincidences'] = False

  # Replace all defaults from the passed in options.
  for key in optionsIn.keys():
    if key not in validKeys:
      print
      print "ERROR: Unsupported inference test option specified: %s" % key
      optionsOut['help'] = True
      break
    optionsOut[key] = optionsIn[key]

  # Print help
  if optionsOut['help']:
    print
    print "Valid options include:"
    print "  onlyClassificationAcc=BOOL    : [False] Only calculate classification" \
              " accuracy"
    print "  printLearnedCoincidences=BOOL : [False] Print learned coincidences" \
              " in order of frequency of use in the inference run"
    print "  computeDistances=BOOL         : [False] Compute distance between" \
              " the SP input and output representations"
    print "  tpActivationThresholds=LIST   : [[8]] List of TP activation "\
              "thresholds to calculate the TP fitness score for."
    print "  verbosity=INT                 : [0] verbosity level: 0, 1, or 2"
    print "  nGrams=TYPE                   : [None] if TYPE is 'train', then " \
              " train a set of n-grams using this dataset. If TYPE is 'test', " \
              " then evaluate prediction ability using the previously trained " \
              " n-grams."
    print "  burnIns=LIST                  : [[1]] List of burn-ins to evaluate "\
              "input prediction scores with. "
    print "  ipsAt=LIST                    : [[]] List of element offsets to " \
              " evaluate input prediction scores at. This differs from burn-in " \
              " in that it reports on the prediction accuracy if you ONLY " \
              " measure it at these element offsets."
    print "  ipsDetailsFor=STR             : [None] Compute and print extensive " \
              " details about the input prediction score as computed at a " \
              " given offset within each sequence, or at every offset. This " \
              " includes a breakdown of the accuracy by path leading up to " \
              " the element. The format of this option is: " \
              " 'fieldname,offset,maxPathLen', where offset can be None to " \
              " compute it for every element. Examples: 'name,2,2' or " \
              " 'name,None,2'. "
    print "  displayMultiStepPrediction=BOOL: [False] Plot multistep predictions"
    print "  plotTemporalHistograms=BOOL:     [False] Plot temporal histograms"
    print "  knnRegression=MODE,FIELD              : ['None,None']" \
              " if MODE is 'train', then train a knn classifier to learn to "\
              " predict the FIELD field using all other fields. If MODE is 'test'"\
              " then evaluate the ability to predict the FIELD using all other"\
              "fields"
    print "  linearRegression=MODE,FIELD           : ['None,None']" \
              " if MODE is 'train', then train a linear model to learn to "\
              " predict the FIELD field using all other fields. If MODE is 'test'"\
              " then evaluate the ability to predict the FIELD using all other"\
              "fields"
    print "  logPredictions=BOOL    : [False] Save the actual and predicted values" \
              "to a file."
    print
    raise RuntimeError("")

  return optionsOut


#############################################################################
def _analyzeTestRun(experiment, netInfo, options, datasetName, testVariantName,
            baseline=None):
  """ Analyze the results from a test run.

  Parameter:
  -----------------------------------------------------------
  experiment:       The experiment object for this experiment. .
  netInfo:          Dictionary of information about the trained network, returned
                     from _analyzeTrainedNet
  options:          dictionary of post-processing options that were provided
                      under the 'ppOptions' key of the infer step.
  datasetName:      The name of the dataset for this inference run. This is the
                      first part of the name of the infer step (the
                      portion of the name preceding the '_').
  testVariantName:  The name of the test variant, i.e. "baseline",
                      "noise0.05", etc. This is the second part of the name
                      of the infer step (the portion of the name after the '_').
  baseline:         Results returned from the processing of the baseline
                      test that goes with this test variant. For example, if
                      this is datasetName='gym', testVariantName='noise0.05',
                      then baseline will be the results from analyze when the
                      datasetName='gym', testVariantName='baseline'
                      test were analyzed.

  retval:           Dictionary of results for this test. This includes the
                      trained classifier, among other things, which is used
                      when comparing a dataset's baseline results with the
                      variants.
  """

  print "\n-------------------------------------------------------------------"
  print "Post-processing results from the %s_%s test" % (datasetName,
          testVariantName),

  if baseline is not None:
    print "and checking classification accuracy against the baseline results " \
          "from the %s_%s test" % (baseline['datasetName'],
          baseline['testVariantName']),


  # ---------------------------------------------------------------------------
  # Check for valid options. Include 'help' in the options for
  #  a help listing of the available options. This is a convenient way to
  #  find out the available options directly from the experiment's
  #  description file.
  options = _processTestOptions(options)


  # ---------------------------------------------------------------------------
  # Open up all available log files
  logs = dict()
  inferenceDir = experiment.getInferenceDirectory()
  logNameReaders = [('reset',               _readIntFromFile),
                    ('sensorBUOut',         _readSparse01VecFromFile),
                    ('spBUOut',             _readSparse01VecFromFile),
                    ('spTDOut',             _readSparseVecFromFile),
                    ('spReconstructedIn',   _readDenseVecFromFile),
                    ('sourceScalars',       _readDenseVecFromFile),
                    ('multiStepPrediction', _readMultiStepPrediction)
                    ]
  for (logName, readerFunc) in logNameReaders:
    filename = _getFilenameForOutputs(inferenceDir, datasetName,
                        testVariantName, logName)
    if os.path.exists(filename):
      fileObj = open(filename)
      logs[logName] = (fileObj, readerFunc)

  if len(logs) == 0:
    raise RuntimeError("Unable to find any logs in the inference directory %s" % inferenceDir)

  updateEvery = 1000

  options['multiStepDisplayFilename'] = _getFilenameForOutputs(inferenceDir,
                                 datasetName, testVariantName, 'multiStep')
  options['temporalHistogramFilename'] = _getFilenameForOutputs(inferenceDir,
                                 datasetName, testVariantName, 'temporalHistogram')
  options['predictionLogFilename'] = _getFilenameForOutputs(inferenceDir,
                                 datasetName, testVariantName, 'predictionLog')

  # =========================================================================
  # Instantiate the stats collecting objects applicable to this test set
  #  and network
  statsCollectors = []
  logNames = logs.keys()
  classificationStats = None
  spStats = None
  for statsClass in [ClassificationStats, ClassificationVsBaselineStats,
                    SPStats, InputPredictionStats, MultiStepPredictionStats,
                    PoorMansStats, NGramStats,
                    KNNRegressionStats, LinearRegressionStats]:
    if statsClass.isSupported(netInfo, options, baseline, logNames):
      statsObj = statsClass(netInfo, options, baseline, logNames)
      if isinstance(statsObj, ClassificationStats):
        classificationStats = statsObj
      if isinstance(statsObj, SPStats):
        spStats = statsObj
      statsCollectors.append(statsObj)



  # Get the names of the fields
  sourceFieldNames = netInfo['encoder'].getScalarNames()

  # =========================================================================
  # Run through each input and compute statistics on each available sample
  sampleIdx = -1
  done = False
  while not done:

    # Progress indicator
    sampleIdx += 1
    if (sampleIdx % updateEvery == 0):
      print ".",
      sys.stdout.flush()

    # Read in the inputs and outputs for this time sample
    # The SP input
    logData = dict()
    for (name, (fileObj, readerFunc)) in logs.items():
      data = readerFunc(fileObj)
      if data is None:
        done = True
        break
      logData[name] = data
      #print data
    if done:
      break


    # Verbose printing
    if options['verbosity'] >= 2:
      (buInputNZ, buInput) = logData['sensorBUOut']
      resetOutput = logData['reset']
      sensorBUInput = logData['sourceScalars']
      print
      print "----- %d: -" % (sampleIdx),
      if resetOutput:
        print "RESET"
      else:
        print
      print "     srcBUOut:", netInfo['encoder'].scalarsToStr(
                                                sensorBUInput,
                                                sourceFieldNames)
      netInfo['encoder'].pprintHeader(prefix=" " * 14)
      netInfo['encoder'].pprint(buInput, prefix=" encoderBUOut:")


    # Feed data into each of the stats collectors
    for statsObj in statsCollectors:
      statsObj.compute(sampleIdx=sampleIdx, data=logData)


  # =========================================================================
  # Close the log files now
  for (name, (fileObj, readerFunc)) in logs.items():
    fileObj.close()

  # --------------------------------------------------------------------
  # Collect all stats into one dict
  stats = dict()
  for statsObj in statsCollectors:
    statsObj.getStats(stats)


  # --------------------------------------------------------------------
  # Compute the "meta-metrics", which are combinations of 2 other metrics
  pmPred = 'inputPredScore_PM'
  pred = 'inputPredScore_burnIn1'
  if pmPred in stats and pred in stats:
    stats['inputPredScore-ipsPM'] = stats[pred] - stats[pmPred]
  fieldNames = netInfo['encoder'].getScalarNames()
  for fieldName in fieldNames:
    pmPred = 'inputPredScore_%s_PM' % fieldName
    pred = 'inputPredScore_%s' % fieldName
    if pmPred in stats and pred in stats:
      stats['inputPredScore_%s-ipsPM' % fieldName] = stats[pred] - stats[pmPred]


  # ----------------------------------------------------------------------
  # Pretty print the stats now
  if options['onlyClassificationAcc']:
    print
    print 'classificationSamples   :', stats['classificationSamples']
    print 'classificationAccPct    :', stats['classificationAccPct']
    for threshold in options['tpActivationThresholds']:
      keyName = 'tpFitnessScore%d' % threshold
      print '%-20s    :' % keyName, stats[keyName]

  else:
    print "\nStats:"
    print "---------------------"
    _pprintInferStats(netInfo['encoder'], stats, options['verbosity'])


  # ----------------------------------------------------------------------
  # Save results to the experiment results dict
  experiment.results["postProc_%s_%s" % (datasetName, testVariantName)] = stats

  # ----------------------------------------------------------------------
  # Return baseline info
  if testVariantName == 'baseline':
    if spStats is not None:
      inputBitActiveCount = spStats.inputBitActiveCount
    else:
      inputBitActiveCount = None
    return dict(classificationStats = classificationStats,
                inputBitActiveCount = inputBitActiveCount,
                datasetName = datasetName,
                testVariantName = testVariantName)
  else:
    return None



##############################################################################
def _pprintInferStats(encoder, inferStats, verbosity = 0):
  """ Pretty print the inference stats

  Parameters:
  --------------------------------------------------------------------
  encoder:      The input encoder. This can be queried for input field
                  descriptions
  inferStats:   the inference stats
  verbosity:    if > 0, print inputReconstruction statistics

  """

  keys = inferStats.keys()
  keys.sort()

  maxLen = max([len(x) for x in keys])
  formatStr = "%%-%ds: " % (maxLen)
  specialFields = ['inputBitDutyCycles', 'inputBitInLearnedCoinc',
                  'inputBitErrAvg', 'inputBitErrWhenOnAvg',
                  'inputBitErrWhenOffAvg']

  # -------------------------------------------------------------------
  # Default print for most of the fields
  for key in keys:
    if key in specialFields:
      continue
    value = inferStats[key]
    print formatStr % (key),
    if isinstance(value, dict) or isinstance(value, list):
      print
      pprint.pprint(value, indent=maxLen)
    else:
      print value


  # -----------------------------------------------------------------------
  # Special case fields
  # Print the reconstructed error by input in sorted order
  if (verbosity > 0) and 'inputBitDutyCycles' in inferStats:
    print formatStr % ("inputReconstruction")
    if 'inputBitErrAvg' in inferStats:
      includeReconstructErrs = True
      values = inferStats['inputBitErrAvg']
    else:
      includeReconstructErrs = False
      values = inferStats['inputBitDutyCycles']
    sorted = values.argsort()[::-1]

    if includeReconstructErrs:
      print "%5s: %-20s : %-12s %-12s %-12s %-8s %-8s" \
            % ("bit#", "field[offset]", "err", "errWhenOn", "errWhenOff",
                "onPct", "numCells")
      errs =  inferStats['inputBitErrAvg']
      errsWhileOn =  inferStats['inputBitErrWhenOnAvg']
      errsWhileOff =  inferStats['inputBitErrWhenOffAvg']
    else:
      print "%5s: %-20s : %-8s %-8s" \
            % ("bit#", "field[offset]", "onPct", "numCells")

    dutyCycles = inferStats['inputBitDutyCycles']
    numCoincs = inferStats['inputBitInLearnedCoinc']
    for bitOffset in sorted:
      if includeReconstructErrs and \
          (errsWhileOn[bitOffset] == 0 and errsWhileOff[bitOffset] == 0):
        break
      (fieldName, fieldOffset) = encoder.encodedBitDescription(bitOffset)
      desc = "(%s[%d])" % (fieldName, fieldOffset)
      if includeReconstructErrs:
        print "%5d: %-20s : %4.2f         %4.2f         %4.2f        %6.2f %5d" \
                % (bitOffset, desc, errs[bitOffset], errsWhileOn[bitOffset],
                errsWhileOff[bitOffset],  100.0*dutyCycles[bitOffset],
                numCoincs[bitOffset])
      else:
        print "%5d: %-20s : %6.2f   %5d" \
                % (bitOffset, desc, 100.0*dutyCycles[bitOffset],
                numCoincs[bitOffset])
  print






#############################################################################
def postProcess(experiment):

  if not isinstance(experiment, Experiment):
    experiment = Experiment(experiment)

  inferenceDir = experiment.getInferenceDirectory()

  # Use level1 rather than level1_sp because the latter
  # is still in learning mode
  # use "all" rather than level1 because level1_sp is not created by default
  experiment.loadNetwork("all")
  net = experiment.network


  # Analyze the trained network and extract the auxiliary data structures
  netInfo = _analyzeTrainedNet(net=net, options=dict())


  # ------------------------------------------------------------------------
  # Get the list of tests, and the list of baselines required
  testNames = [test['name'] for test in experiment.description['infer']]
  testOptions = [test.get('ppOptions', dict()) for test in experiment.description['infer']]
  standaloneTests = list(testNames)
  options = dict(zip(testNames, testOptions))

  baselineTestNames = set()
  for testName in testNames:
    (datasetName, testVariant) = testName.split('_')
    if testVariant == 'baseline':
      baselineTestNames.add(testName)


  # ------------------------------------------------------------------------
  # For each baseline, train the classifier, and then run each variant that uses
  #  that baseline
  for baselineTestName in baselineTestNames:
    (baseDatasetName, baseVariantName) = baselineTestName.split('_')
    assert(baseVariantName == 'baseline')
    standaloneTests.remove(baselineTestName)
    baseline = _analyzeTestRun(experiment, netInfo=netInfo,
            options=options[baselineTestName],
            datasetName=baseDatasetName, testVariantName=baseVariantName,
            baseline=None)

    # Now, run each variant that uses this baseline
    for testName in testNames:
      (datasetName, variantName) = testName.split('_')
      if datasetName != baseDatasetName or variantName == 'baseline':
        continue
      standaloneTests.remove(testName)
      _analyzeTestRun(experiment, netInfo=netInfo, options=options[testName],
            datasetName=datasetName, testVariantName=variantName,
            baseline=baseline)


  # Run each standalone test
  for testName in standaloneTests:
    (datasetName, variantName) = testName.split('_')
    _analyzeTestRun(experiment, netInfo=netInfo, options=options[testName],
            datasetName=datasetName, testVariantName=variantName,
            baseline=None)



#############################################################################
if __name__ == "__main__":
  success = postProcess(sys.argv[1])
  if success:
    sys.exit(0)
  else:
    sys.exit(1)
