Algorithm API
-------------

There are several components to an HTM system:

#. encoding data into SDR using `Encoders <encoders.html>`_
#. passing encoded data through the `Spatial Pooler <spatial-pooler.html>`_
#. running `Temporal Memory <temporal-memory.html>`_ over the Spatial Pooler's active columns
#. extracting predictions using a `Classifier <classifiers.html>`_
#. extracting anomalies using ``Anomaly`` and ``AnomalyLikelihood`` (see `anomaly detection <anomaly-detection.html#>`_)

Each of these components can be run independently of each other. The only
communication between the are binary arrays (SDRs) representing cell
activations. Spatial representations are maintained within the *proximal*
synapse permanences between the Spatial Pooler's columns and the input space.
Temporal representations are maintained within the *distal* synapse permanences
between the cells in the Temporal Memory representation.

See the low-level APIs for `Encoders <encoders.html>`_ and `Algorithms <algorithms.html>`_.
