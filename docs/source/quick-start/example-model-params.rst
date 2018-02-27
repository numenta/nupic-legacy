Example Model Params
====================

This raw model params file is used in the `Quick Start <index.html>`_. These
parameters are used to create an
:class:`~nupic.frameworks.opf.htm_prediction_model.HTMPredictionModel`, which will
create an HTM with specified encoders and connect them to both a
:class:`~nupic.algorithms.spatial_pooler.SpatialPooler` and
:class:`~nupic.algorithms.backtracking_tm.BacktrackingTM` (or
:class:`~nupic.algorithms.backtracking_tm_cpp.BacktrackingTMCPP` if
``modelParams.tmParams.temporalImp==cpp``).

To see detailed algorithm parameters for the algorithms see their API documentation at:

* :class:`~nupic.algorithms.spatial_pooler.SpatialPooler`
* :class:`~nupic.algorithms.backtracking_tm.BacktrackingTM`
* :class:`~nupic.algorithms.sdr_classifier.SDRClassifier`

.. literalinclude:: ../../examples/params/model.yaml
