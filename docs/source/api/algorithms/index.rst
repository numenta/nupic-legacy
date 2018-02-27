Algorithms
----------

There are several components to an HTM system:

#. encoding data into SDR using `Encoders <../algorithms/encoders.html>`_
#. passing encoded data through the :class:`.SpatialPooler`
#. running :class:`.TemporalMemory` over the Spatial Pooler's active columns
#. extracting predictions using a `Classifier <../algorithms/classifiers.html>`_
#. extracting anomalies using :class:`.Anomaly` and :class:`.AnomalyLikelihood`.

Each of these components can be run independently of each other. The only
communication between the are binary arrays (SDRs) representing cell
activations. Spatial representations are maintained within the *proximal*
synapse permanences between the Spatial Pooler's columns and the input space.
Temporal representations are maintained within the *distal* synapse permanences
between the cells in the Temporal Memory representation.

--------------------------------------------

.. toctree::
   :maxdepth: 3
   :caption: Contents:

   encoders
   spatial-pooling
   sequence-memory
   classifiers
   anomaly-detection
