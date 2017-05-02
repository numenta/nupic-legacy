## Algorithm API

There are several components to an HTM system:

1. encoding data into SDR using [Encoders](encoders.html)
1. passing encoded data through the [Spatial Pooler](spatial-pooler.html)
1. running [Temporal Memory](temporal-memory.html) over the Spatial Pooler's active columns
1. extracting predictions using a [Classifier](classifiers.html)
1. extracting anomalies using [`Anomaly` and `AnomalyLikelihood`](anomaly-detection.html)

Each of these components can be run independently of each other. The only communication between the are binary arrays (SDRs) representing cell activations. Spatial representations are maintained within the _proximal_ synapse permanences between the Spatial Pooler's columns and the input space. Temporal representations are maintained within the _distal_ synapse permanences between the cells in the Temporal Memory representation.

See the low-level APIs for [Encoders](encoders.html) and [Algorithms](algorithms.html).
