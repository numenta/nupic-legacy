Models
======

Base Model
^^^^^^^^^^

.. automodule:: nupic.frameworks.opf.model

.. autoclass:: nupic.frameworks.opf.model.Model
   :members:


HTMPredictionModel
^^^^^^^^^^^^^^^^^^

.. automodule:: nupic.frameworks.opf.htm_prediction_model

.. autoclass:: nupic.frameworks.opf.htm_prediction_model.HTMPredictionModel
   :members: getParameter,getRuntimeStats
   :show-inheritance:

   .. automethod:: nupic.frameworks.opf.htm_prediction_model.HTMPredictionModel.setAnomalyParameter(param, value)
   .. automethod:: nupic.frameworks.opf.htm_prediction_model.HTMPredictionModel.getAnomalyParameter(param)
   .. automethod:: nupic.frameworks.opf.htm_prediction_model.HTMPredictionModel.anomalyRemoveLabels(start, end, labelFilter)
   .. automethod:: nupic.frameworks.opf.htm_prediction_model.HTMPredictionModel.anomalyAddLabel(start, end, labelName)
   .. automethod:: nupic.frameworks.opf.htm_prediction_model.HTMPredictionModel.anomalyGetLabels(start, end)


TwoGramModel
^^^^^^^^^^^^

.. autoclass:: nupic.frameworks.opf.two_gram_model.TwoGramModel
   :members:
   :show-inheritance:

ModelFactory
^^^^^^^^^^^^

.. autoclass:: nupic.frameworks.opf.model_factory.ModelFactory
   :members:
