Metrics
=======

Prediction Metrics Manager
--------------------------

.. automodule:: nupic.frameworks.opf.prediction_metrics_manager

.. autoclass:: nupic.frameworks.opf.prediction_metrics_manager.MetricsManager
   :members:

Interface
---------

.. automodule:: nupic.frameworks.opf.metrics

.. autoclass:: nupic.frameworks.opf.metrics.MetricsIface
   :members:

.. autoclass:: nupic.frameworks.opf.metrics.MetricSpec
   :members:

.. autoclass:: nupic.frameworks.opf.metrics.CustomErrorMetric
   :members:
   :show-inheritance:

.. autoclass:: nupic.frameworks.opf.metrics.MetricSpec
   :members:

.. autoclass:: nupic.frameworks.opf.metrics.AggregateMetric
   :members:
   :show-inheritance:

Helpers
-------

.. automethod:: nupic.frameworks.opf.metrics.getModule

Available Metrics
-----------------

.. autoclass:: nupic.frameworks.opf.metrics.MetricNegativeLogLikelihood
   :show-inheritance:

.. autoclass:: nupic.frameworks.opf.metrics.MetricRMSE
   :show-inheritance:

.. autoclass:: nupic.frameworks.opf.metrics.MetricNRMSE
   :show-inheritance:

.. autoclass:: nupic.frameworks.opf.metrics.MetricAAE
   :show-inheritance:

.. autoclass:: nupic.frameworks.opf.metrics.MetricAltMAPE
   :show-inheritance:

.. autoclass:: nupic.frameworks.opf.metrics.MetricMAPE
   :show-inheritance:

.. autoclass:: nupic.frameworks.opf.metrics.MetricPassThruPrediction
   :show-inheritance:

.. autoclass:: nupic.frameworks.opf.metrics.MetricMovingMean
   :show-inheritance:

.. autoclass:: nupic.frameworks.opf.metrics.MetricMovingMode
   :show-inheritance:

.. autoclass:: nupic.frameworks.opf.metrics.MetricTrivial
   :show-inheritance:

.. autoclass:: nupic.frameworks.opf.metrics.MetricTwoGram
   :show-inheritance:

.. autoclass:: nupic.frameworks.opf.metrics.MetricAccuracy
   :show-inheritance:

.. autoclass:: nupic.frameworks.opf.metrics.MetricAveError
   :show-inheritance:

.. autoclass:: nupic.frameworks.opf.metrics.MetricNegAUC
   :members: accumulate
   :show-inheritance:

.. autoclass:: nupic.frameworks.opf.metrics.MetricMultiStep
   :show-inheritance:

.. autoclass:: nupic.frameworks.opf.metrics.MetricMultiStepProbability
   :show-inheritance:

.. autoclass:: nupic.frameworks.opf.metrics.MetricMulti
   :show-inheritance:
