#! /usr/local/bin/python

# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have purchased from
# Numenta, Inc. a separate commercial license for this software code, the
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


from math import sqrt
import numpy
import itertools
import operator




# These are derived from from nupic.support.compress in nupic1
def _parseFloat(x):
  try:
    return float(x)
  except:
    # Special case for Windows. It serializes infinities in a way that it
    # cannot read back.
    if x.endswith("#INF"):
      import numpy
      return float(x.rsplit("#", 1)[0]) * numpy.inf
    else:
      raise
def _parseFloatArray(s):
  """Parses a string representing an array of space-separated floats"""
  if len(s) == 0:
    return []
  try:
    nums = tuple(_parseFloat(i) for i in s.split())
    return nums
  except Exception, e:
    raise RuntimeError("Failed to parse an array of floats from '%s': %s"
                       % (s, str(e)))

from nupic.support.datafiles import processCategoryFile

# these methods are used by RunInference in VF2.
__all__ = ["InferenceAnalysis", "Aggregator"]

def ReadInference(filename, skipLines=0):
  """Reads a file output by VectorFileEffector containing
  HTM inference. The file format is ASCII text, with each
  line describing a a discrete probability distribution as a space-separated
  list of numbers. All lines should have the same length list of numbers,
  and each number is assumed to be in floating point decimal form.

  Returns a list of lists of floating point numbers, with the length of
  the outer list being the number of lines in the file (not counting the
  skipped lines, see 'skipLines' below) and the length of the list associated
  with each line being the number of space-separated numbers that were
  read from that line.

  Example:
  inference = ReadInference("results.txt", skipLines=0)

  Parameters
  ----------
  filename: (string)
  The filesystem path to load the file from.

  skipLines: (int)
  Optional number of lines at the beginning to skip.
  Defaults to 0.
  """
  #from dbgp.client import brk; brk(port=9019)
  skipLines = int(skipLines)
  # lines = file(filename).readlines()[skipLines:]
  # Pre-test the existence of results in the files.
  testRead = open(filename)

  for i in xrange(skipLines):
    result = testRead.readline()
    if not result:
      raise RuntimeError("Unable to skip line %d, file too short: %s" %
        (i+1, filename))
  remainingLines = testRead.readlines()
  testRead.close()
  if not remainingLines:
    raise RuntimeError("File '%s' does not contain any data lines." % filename)

  dataFile = open(filename)
  lineNumber = 0
  # Skip lines.
  for i in xrange(skipLines):
    result = dataFile.readline()
    if not result: # Should never reach here, as pre-detect should catch.
      raise RuntimeError("Unable to skip line %d, file too short: %s" %
        (i+1, filename))

  # Cannot use matplotlib.mlab.load, as it does not handle some strange outputs
  # from VectorFileEffector on Windows.

  # Instead, read a line at a time so that we can produce a good error message.
  # Should read incrementally, but will return full array anyway.
  allLines = dataFile.readlines()
  nr = len(allLines)
  if nr:
    nc = len(allLines[0].strip().split())
    if not nc:
      raise RuntimeError("No data in line %d of file: %s" % (skipLines+1, filename))
    results = numpy.zeros((nr, nc))
    for i, line in enumerate(allLines):
      values = _parseFloatArray(line)

      if len(values) > nc:
        raise RuntimeError("Too many columns (%d > %d) at line %d of file: %s" %
          (len(values), nc, skipLines+i+1, filename))
      elif len(values) < nc:
        raise RuntimeError("Too few columns (%d < %d) at line %d of file: %s" %
          (len(values), nc, skipLines+i+1, filename))
      results[i,...] = values
  else:
    results = numpy.zeros((0, 0))
  return results

def optArgMax(y):
  if len(y): return numpy.argmax(y)
  else: return 0

def optAllMaxArgs(y):
  if len(y):
    return list(numpy.where(y==y.max())[0])
  else: return [0]

def ClassifyInference(inference, columns=None, allowWinnerTies=False):
  """Finds the index of the mode of each discrete probability distribution in a
  list of distributions passed in. The data passed in should be inference from
  an HTM system, in the form returned by ReadInference(), a list of lists of
  floating point numbers. Can be configured to only calculate the maximum over
  the subset of each probability distribution.

  Returns a list of maximum indices of the same length as the outer list passed
  in as the 'inference' argument.

  Example:
  inference = ReadInference("results.txt", skipLines=0)
  winners = ClassifyInference(inference, columns=None)

  Parameters
  ----------
  inference: (list of lists of floats)
  A list of probability distributions over which the max index will be
  calculated for each distribution.

  columns: (integer or None)
  If None, the maximum over all entries in the probability distributions is
  calculated. If an integer smaller than the number of entries in each
  distribution, only calculates the max over entries [0, columns).

  allowWinnerTies: (bool)
  if set to False (the default), then each element in the list will be
  a single scaler - which is the argmax of the distribution for that
  sample. If set to True, then an element in the list could be a tuple,
  containing ALL of the elements of the distribution that have the same
  max value.
  """

  if allowWinnerTies:
    if columns is not None:
      return [optAllMaxArgs(y[0:columns]) for y in inference]
    else:
      return [optAllMaxArgs(y) for y in inference]

  else:
    if columns is not None:
      return [optArgMax(y[0:columns]) for y in inference]
    else:
      return [optArgMax(y) for y in inference]

def CompareClassifications(classifications, knownCategories,
    unlabeledClassifications):
  """
  Match a list of inferred classifications (from ClassifyInference())
  against a list of known categories. Can perform exact matches, or matches
  that take into account the possibility that the indices may differ, but
  there should be a one-to-one mapping.

  Returns a 3-tuple with the first entry being the number of correct
  classifications, the second entry being the total number of known
  answers, and the third entry being a list of indices into the original
  classifications that were incorrect.

  Example:
  knownCategories = nupic.support.datafiles.processCategoryFile(
    file("categories.txt"), format=2)
  inference = ReadCategoryFile("results.txt", skipLines=0)
  inferredClassifications = ClassifyInference(inference, columns=None)
  CompareClassifications(inferredClassifications, knownCategories,
    unlabeledClassifications=False)

  If unlabeledClassifications is False, assumes that the indices in the
  inferredClassifications and the knownCategories should match exactly.
  If unlabeledClassifications is True, empirically builds a table of mappings
  and calculates the most likely mapping between the inferred indices and the
  known categories. Then uses that mapping to calculate the matches.

  If the lists of classifications and knownCategories are of different lengths,
  only performs matching and error checking on the first 'n' entries,
  where 'n' is the minimum of the two lengths.

  Parameters
  ----------
  classifications: (list of integers)
  A list of inferred classification category indices produced by an
  HTM system in the format output by ClassifyInference().

  knownCategories: (list of integers, or a list of lists)
  A list of known category indices of the same length of the list of inferred
  classifications; if a list of lists, means that any of the listed answers
  will be considered 'correct' at each time point.

  unlabeledClassifications: (bool)
  If False, assumes the inferred classification indices match the known
  categories. If True, specifies that the mapping between the inferred
  classification indices and the known categories is unknown and attempts to
  calculate an optimal mapping.
  """


  # Truncate both sets of results to the length of the available categories.
  n = min(len(classifications), len(knownCategories))
  classifications = classifications[0:n]
  knownCategories = knownCategories[0:n]

  if unlabeledClassifications:
    # Build a table mapping one set of categories to the other.
    table = numpy.zeros((max(knownCategories)+1, max(classifications)+1),
      numpy.int32)
    for k, c in itertools.izip(knownCategories, classifications):
      table[k, c] += 1
    remap = {}
    for c in set(classifications):
      remap[c] = numpy.argmax(table[..., c])
    remappedClassifications = [remap[c] for c in classifications]
    classifications = remappedClassifications

  # ------------------------------------------------------------------------
  # If both knowCategories and classifications are simple vectors of scalars,
  #  we can do a simply numpy array comparison to get the matches
  catIsIter = hasattr(knownCategories[0], '__iter__')
  classIsIter = hasattr(classifications[0], '__iter__')
  if not catIsIter and not classIsIter:
    matches = (numpy.array(classifications) == numpy.array(knownCategories))

  # ------------------------------------------------------------------------
  # If either or both are lists, then do an intersection of the items
  else:
    items = itertools.izip(xrange(n), classifications, knownCategories)
    matches = numpy.zeros(n, dtype='bool')

    # classifications are lists, knownCategories (sensor data) are scalars:
    if not catIsIter:
      for idx, outputs, correctCategory in items:
        if correctCategory in outputs:
          matches[idx] = True

    # classifications are scalars, knownCategories (sensor data) are lists:
    elif not classIsIter:
      for idx, output, correctCategories in items:
        if output in correctCategories:
          matches[idx] = True

    # both are lists:
    else:
      for idx, outputs, correctCategories in items:
        if len(set(outputs).intersection(correctCategories)) > 0:
          matches[idx] = True

  nCorrect = matches.sum()
  errors = list(numpy.logical_not(matches).nonzero()[0])

  return nCorrect, n, errors


class Aggregator(object):
  """This class aggregates inference results

  It is designed to be used with explorers such as the
  EyeMovementExplorer that provide multiple presentations
  that need to be grouped together into a single conceptual inference.

  You don't use an aggregator directly. Instead, you may pass an aggregator
  to InferenceAnalysis. You instantiate it and provide
  an aggregator function that accepts a list of inference results
  (as read by ReadInference) and returns a single inference.

  Aggregator comes with several built-in aggregation functions:
  * 'sum'
  * 'average'
  * 'max'
  * 'product'

  The default is 'sum', so if you don't provide your ownfunction it will
  sum its results. You may specify the Aggregator.max function to get max
  aggregation or your own custom aggregation function.

  Inference analysis will invoke the aggregator to post-process the inference
  results of the EyeMovementExplorer.
  """
  def __init__(self, count, aggregateFunc=None):
    self.count = count
    self.aggregateFunc = aggregateFunc if aggregateFunc else self.sum

  @staticmethod
  def sum(inference_list):
    return [sum(x) for x in inference_list.transpose()]

  @staticmethod
  def average(inference_list):
    return [sum(x) / len(x) for x in inference_list.transpose()]

  @staticmethod
  def product(inference_list):
    return [reduce(operator.mul, x) for x in inference_list.transpose()]

  @staticmethod
  def max(inference_list):
    return [max(x) for x in inference_list.transpose()]

  def _aggregate(self, results):
    """This is the generic aggregate method

    It breaks down the inference list ot chunks of size self.count
    and feeds each chunk to the aggregateFunc to distill each chunk
    to a single inference. Eventually, it returns the list of aggregated
    inferences.
    """
    assert isinstance(results, numpy.ndarray)
    assert results.ndim == 2

    count = self.count
    if count == 1:
      return results
    r = []
    start = 0
    for i in range(len(results) / count):
      end = min(len(results), start + count)
      agg = self.aggregateFunc(results[start:end])
      r.append(agg)
      start = end
    return r

class InferenceAnalysis(object):
  """A class that performs all the steps necessary to postprocess HTM inference
  and calculate HTM classification performance given a list of known
  categories. The way of using this class is to construct an instance of
  InferenceAnalysis with all the necessary data, then query individual
  quantities that InferenceAnalysis can calculate.

  Example:
  inferenceAnalysis = InferenceAnalysis(
      resultsFilename="results.txt", unlabeledClassifications=False,
      categoryFilename="categories.txt", categoryFileFormat=2
    )
  accuracy = inferenceAnalysis.accuracy
  accuracyLowerBound, accuracyUpperBound = \
    inferenceAnalysis.getAccuracyIntervalEstimate(confidence=0.95)
  errors = inferenceAnalysis.errors

  On construction, performs the following operations:
  1. Reads the inference results and uses ClassifyInference() to convert them
     to one inferred classification index per input.
  2. Reads the known category indices.
  3. Matches the inferred classification indices against the known category
     indices, either exactly or by building a probabilistic mapping between the
     two sets of indices.
  4. Calculates classification accuracy.

  Parameters for specifying the inference results
  -----------------------------------------------
  resultsFilename: (string)
  Filesystem path to a file containing the HTM inference to be analyzed.
  The file format must be such that each line contains a list of ASCII
  decimal floating-point numbers, representing a single inference
  probability distribution.
  The file will be processed with ReadInference() and must match its format
  expectations. The processing of this file is also affected by parameters
  'skipLines' and 'resultColumns'.

  results: (None or list of discrete probability distributions)
  Optional argument that specifies the HTM inference to be analyzed.
  You must specify either 'results' or 'resultsFilename' but not both.
  The inference should be in the form produced by ReadInference(),
  a list of lists of floating point numbers, with each entry in the
  outer list representing the inference distribution produced for a
  given input.
  The list should be of the same length as the number of known categories
  in file 'categoryFilename'.
  The processing of this list is also affected by parameters
  'skipLines' and 'resultColumns'.

  unlabeledClassifications: (bool)
  If False, assumes that the inferred classification indices match the
  known category indices exactly.
  If True, specifies that the inferred classification indices do not match the
  known category indices, and the mapping must be performed by
  InferenceAnalysis. Will be passed to the 'unlabeledClassifications'
  argument of CompareClassifications().

  skipLines: (integer)
  An optional number of lines from the inference results to skip.
  Defaults to 0. Set to 1 if the results file contains a header line.
  Does not affect the processing of the the 'category' information.

  resultColumns: (integer or None)
  An optional number of columns from the inference results to process.
  If None, all the columns will be processed. If less than the number of
  columns in the inference results, all columns equal to greater than
  the 'resultColumns' parameter will be ignored.
  Will be passed to the 'columns' argument of ClassifyInference().

  Parameters for specifying the known categories
  ----------------------------------------------
  categoryFilename: (string)
  A filesystem path where the known categories are stored.
  This file should contain one line per input, with a single
  integer category index on each line.
  Processing of this file is controlled by the format specified in
  'categoryFileFormat'.

  categoryFileFormat: (None or one of a list of supported formats)
  The file format to be used when processing the file of known categories
  (specified in 'categoryFilename'). The file will be read by
  nupic.support.datafiles.processCategoryFile().
  Specify 'categoryFileFormat' or 'skipFirstCategoryLine' (deprecated), but
  not both.
  Available formats include:
  2   - The file contains exactly one line per known category index,
        and each category index is an ASCII-formatted decimal integer.
  0   - The file contains a single header line to be ignored, and then
        one line per known category index.

  categoryColumns: (None, or an integer)
  Indicates how many categories are active per timepoint (how many elements
  wide the category info is).  If 0, we'll determine this from the file.  If
  None (the default), means that the category info is 1 element wide, and
  that the any lists referring to the 'correct category' will just be a list
  of ints (rather than a list of lists).

  skipFirstCategoryLine: (bool)
  Deprecated in 1.4. Use 'categoryFileFormat' instead.
  Do not specify both 'skipFirstCategoryLine' and 'categoryFileFormat',
  exactly one of these two arguments is required.
  If False, treat the first line of the category file identically to all the
  other lines, as it contains a valid category index.
  If True, skip the first line of the category file, assuming that it contains
  header information.

  allowWinnerTies: (bool)
  This affects how classification accuracy is evalulated. If set to
  False (the default), then the expected category must have
  the highest output score (or, be the lowest category index with that
  output score) in order to be counted as a correct answer.
  If set to True, then as long as the expected category has the highest score
  OR is in a tie with other categories with that same highest score, it will
  be counted as a correct answer.

  """
  def __init__(self, results=None, resultsFilename=None,
      categoryFilename=None, skipFirstCategoryLine=None,
      resultColumns=None, skipLines=0, unlabeledClassifications=False,
      categoryFileFormat=None, categoryColumn=0, categoryColumns=None,
      aggregator=None, allowWinnerTies=False):
    self.classifications = None
    self.categories = None
    self.nClassified = 0
    self.nCorrect = None
    self.nKnown = 0
    self.errors = None
    self.accuracy = None
    self.seAccuracy = None

    hasResults = results is not None
    if hasResults:
      assert not resultsFilename, \
        "Specify exactly one of 'results' or 'resultsFilename'."
      results = results[skipLines:]
    elif resultsFilename:
      results = ReadInference(filename=resultsFilename, skipLines=skipLines)
    else:
      raise RuntimeError("Specify either 'results' or 'resultsFilename'.")

    # Aggregate results
    if aggregator:
      results = aggregator._aggregate(results)

    #from dbgp.client import brk; brk(port=9000)

    self.classifications = ClassifyInference(inference=results,
      columns=resultColumns, allowWinnerTies=allowWinnerTies)

    # Save these to support getTopNAccuracy()
    self.results = results

    self.nClassified = len(self.classifications)

    if categoryFileFormat is None:
      if skipFirstCategoryLine is None: categoryFileFormat = 0 # Old default.
      elif skipFirstCategoryLine: categoryFileFormat = 0
      else: categoryFileFormat = 2
    else:
      if skipFirstCategoryLine is not None:
        raise RuntimeError("'skipFirstCategoryLine' is not necessary or supported "
          "when specifying 'categoryFileFormat'.")

    if categoryFilename:
      allCategories = []
      # TODO NuPIC 2: an undocumented "feature" of this method was that
      # categoryFilename could be a list. Don't know of any
      # use for this, so remove it. Stage 1 of the removal is to detect
      # when we are passed a list and assert. If we run this way
      # for a while with no assertions, we'll change the code to expect
      # a single filename (stage 2)
      if hasattr(categoryFilename, "__iter__"):
        raise Exception("Internal error -- got multiple category filenames -- see comment in inferenceanalysis.py")

      categoryFilenames = [categoryFilename]

      for fn in categoryFilenames:
        count = aggregator.count if aggregator else 1
        numCat, categories = processCategoryFile(file(categoryFilename),
                                                 format=categoryFileFormat,
                                                 categoryColumn=categoryColumn,
                                                 categoryColumns=categoryColumns,
                                                 count=count)
        allCategories.extend(categories)
      self.categories = allCategories

      self.nCorrect, self.nKnown, self.errors = \
        CompareClassifications(classifications=self.classifications,
          knownCategories=self.categories,
          unlabeledClassifications=unlabeledClassifications)

    if self.nKnown:
      self.accuracy = float(self.nCorrect) / float(self.nKnown)
      self.seAccuracy = sqrt(self.accuracy * (1.0 - self.accuracy) / self.nKnown)

  def writeClassificationFile(self, filename, format=2):
    """Writes the list of inferred classification indices (calculated from the
    HTM inference results) to a file.
    New in 1.4, the default file format is '2', where each line contains a
    single classification index in ASCII decimal integer format, and no
    additional lines are written (there is no header line).
    This is a change from 1.3, where the default file format written was '0'
    (contained a single header line at the beginning of the file stating that
    the file contained 1 column).
    """
    assert format in [0, 2]
    classificationFile = file(filename, "w")
    if format == 0:
      print >>classificationFile, '1' # Header row.
    for c in self.classifications: print >>classificationFile, c
    del classificationFile # Close and flush.

  def getAccuracyIntervalEstimate(self, confidence):
    """Calculates a confidence interval for the 'accuracy': the proportion of
    correct classifications that this HTM could make in repeated independent
    and identically distributed trials.
    Calculated from the 'accuracy' estimate:
      (number correct / number of classifications)
    and a confidence level (e.g. 0.95).
    Uses a quick estimate that assumes a large sample size and a
    0.95 confidence level.
    """
    assert self.accuracy is not None, \
      "No accuracy was calculated."
    assert (self.accuracy >= 0.0) and (self.accuracy <= 1.0), \
      "Invalid accuracy detected."
    assert confidence == 0.95, \
      "Only 95%% confidence intervals are supported at present."
    qnorm = 1.96

    if (self.accuracy == 0.0) or (self.accuracy == 1.0):
      print "Warning: Classical interval estimates with all correct or " \
        "all incorrect answers are not valid."

    lower = self.accuracy - qnorm * self.seAccuracy,
    if lower < 0.0:
      print "Warning: Truncated normal distribution at 0.0."
      lower = 0.0
    upper = self.accuracy + qnorm * self.seAccuracy,
    if upper > 1.0:
      print "Warning: Truncated normal distribution at 1.0."
      lower = 1.0

    return (lower, upper)

  def convertToDict(self):
    """Returns all computed quantities in the form of a dictionary useful with
    NetExplorer experiments.
    Returned quantities in the dictionary include:
      'nClassified': The number of results compared against known categories.
      'nCorrect': The number of results that matched known categories.
      'accuracy': The accuracy of the classification: nCorrect / nClassified.
      'classifications': The list of inferred classification indices.
      'categories': The list of known category indices.
      'error', The locations in the classification list where errors occurred.
    """
    return {
        'nClassified': self.nClassified,
        'nCorrect': self.nCorrect,
        'nKnown': self.nKnown,
        'accuracy': self.accuracy, 'seAccuracy': self.seAccuracy,
        'classifications': self.classifications,
        'categories': self.categories,
        'errors': self.errors
      }

  def getTopNAccuracy(self, N):
    """
    Get the accuracy, counting a correct match if the correct category index
    is in the top N results.
    """

    if self.nKnown == 0:
      raise Exception("nKnown == 0")

    if N == 1:
      # Skip this expensive computation
      return self.accuracy

    if N >= self.results.shape[1]:
      return 1.0

    # Repeat the column-vector categories N times (to produce N columns)
    cats = numpy.array(self.categories)
    catsR = cats.repeat(N).reshape((cats.shape[0], N))
    # Sort the classifications (ascending), then use only the top N
    # Subtract the repeated categories; the result will have a 0 in the row
    # if there was a match
    diff = self.results.argsort()[:,-N:] - catsR
    # Count the matches by looking for a zero in each row
    matches = numpy.abs(diff).min(1) == 0
    nCorrect = matches.sum()

    return nCorrect / float(self.nKnown)