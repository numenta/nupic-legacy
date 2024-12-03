# Copyright 2013 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

"""
This file describes the interfaces for adapting
:class:`~nupic.frameworks.opf.opf_task_driver.OPFTaskDriver` to specific
environments.

These interfaces encapsulate external specifics, such as
data source (e.g., .csv file or database, etc.), prediction sink (.csv file or
databse, etc.), report and serialization destination,  etc.
"""



from abc import ABCMeta, abstractmethod
from collections import namedtuple



class PredictionLoggerIface(object):
  """
  This class defines the interface for OPF prediction logger implementations.
  """
  __metaclass__ = ABCMeta

  @abstractmethod
  def close(self):
    """ Closes connect to output store and cleans up any resources associated
    with writing.
    """

  @abstractmethod
  def writeRecord(self, modelResult):
    """ Emits a set of inputs data, inferences, and metrics from a model
    resulting from a single record.

    :param modelResult: (:class:`nupic.frameworks.opf.opf_utils.ModelResult`)
           contains the model input and output for the current timestep.
    """


  @abstractmethod
  def writeRecords(self, modelResults, progressCB=None):
    """
    Same as :meth:`writeRecord`, but emits multiple rows in one shot.

    :param modelResults: (list) of
           :class:`nupic.frameworks.opf.opf_utils.ModelResult` objects, each
           represents one record.
    :param progressCB: (func) optional callback method that will be called after
           each batch of records is written.

    """

  @abstractmethod
  def setLoggedMetrics(self, metricNames):
    """ Sets which metrics should be written to the prediction log.

    :param metricNames: (list) metric names that match the labels of the
                      metrics that should be written to the prediction log
    """

  @abstractmethod
  def checkpoint(self, checkpointSink, maxRows):
    """ Save a checkpoint of the prediction output stream. The checkpoint
    comprises up to maxRows of the most recent inference records.

    :param checkpointSink: A File-like object where predictions checkpoint data,
           if any, will be stored.
    :param maxRows: (int) Maximum number of most recent inference rows to
           checkpoint.
    """



# PredictionLoggingElement class
#
# This named tuple class defines an element in the sequence of predictions
# that are passed to PredictionLoggerIface.emit()
#
# predictionKind:   A PredictionKind constant representing this prediction
# predictionRow:    A sequence (list, tuple, or nupic array) of field values
#                   comprising the prediction.  The fields are in the order as
#                   described for the inputRecordSensorMappings arg of the
#                   PredictionLoggerIface.__call__ method
PredictionLoggingElement = namedtuple("PredictionLoggingElement",
                                      ("predictionKind", "predictionRow",
                                       "classification"))
