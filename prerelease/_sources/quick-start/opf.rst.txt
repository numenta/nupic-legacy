.. include:: common.rst

Online Prediction Framework (OPF)
---------------------------------

See the `OPF Guide <../guides/opf.html>`_ for an overview of this API.

Here is the complete program we are going to use as an example. In sections
below, we'll break it down into parts and explain what is happening (without
some of the plumbing details).

.. literalinclude:: ../../examples/opf/complete-opf-example.py

Model Parameters
^^^^^^^^^^^^^^^^

Before you can create an OPF model, you need to have model parameters defined in
a file. These model parameters contain many details about how the HTM
network will be constructed, what encoder configurations will be used, and
individual algorithm parameters that can drastically affect how a model
operates. The model parameters we're using in this Quick Start
`can be found here <example-model-params.html>`_.

To use model parameters, they can be written to a file and imported into
your script. In this example, our model parameters existing in a
`YAML <http://yaml.org/>`_ file called ``params.yaml`` and are identical to
those `linked above <example-model-params.html>`_.

Create an OPF Model
^^^^^^^^^^^^^^^^^^^

The easiest way to create a model once you have access to model parameters is by
using the :class:`.ModelFactory`.

.. literalinclude:: ../../examples/opf/create-model-example.py

The resulting ``model`` will be an instance of :class:`.HTMPredictionModel`.

Feed the Model Data
^^^^^^^^^^^^^^^^^^^

The raw input data file is described `here <example-data.html>`_ in detail.

Our `model parameters <example-model-params.html>`_ define how this data will be
encoded in the ``encoders`` section:

.. literalinclude:: ../../examples/opf/example-model-param-encoders.yaml

Notice that three semantic values are being encoded into the input space. The
first is the scalar energy ``consumption`` value, which is being encoded with
the :class:`.RandomDistributedScalarEncoder`. The next two values represent two
different aspects of time using the :class:`.DateEncoder`. The encoder called
``timestamp_timeOfDay`` encodes the time of day, while the ``timestamp_weekend``
encoder will output different representations for weekends vs weekdays. The
:class:`.HTMPredictionModel` will combine these encodings using the
:class:`.MultiEncoder`.

    For details about encoding and how these encoders work, see the
    `HTM School <https://numenta.org/htm-school/>`_ episodes on encoders.

Now that you see the raw input data and how it is configured to be encoded into
binary arrays for the HTM to process it, let's see the code that actually reads
the CSV data file and runs it through our ``model``.

.. literalinclude:: ../../examples/opf/load-model-example.py

Extract the results
^^^^^^^^^^^^^^^^^^^

In the classifier configuration of our `model parameters <example-model-params.html>`_,
identified as ``modelParams.clParams``, the ``steps`` value tells the model how
many steps into the future to predict. In this case, we are predicting both one
and five steps into the future as shown by the value ``1,5``.

This means the ``results`` object will have prediction information keyed by both
``1`` and ``5``.

.. literalinclude:: ../../examples/opf/results-example.py

As you can see in the example above, the ``results`` object contains an
``inferences`` property that contains all the information about predictions.
This includes the following keys:

* ``multiStepBestPredictions``: Contains information about the *best* prediction
    that was returned for the last row of data.
* ``multiStepPredictions``: Contains information about *all* predictions for the
    last row of data, including confidence values for each prediction.

Each of these dictionaries should have a key corresponding to the *steps ahead*
for each prediction. In this example, we are retrieving predictions for both
``1`` and ``5`` steps ahead (which was defined in the `Model Parameters`_).

In order to get both the best prediction as well as the confidence in the
prediction, we need to find the value for the best prediction from the
``multiStepBestPredictions`` structure, then use it to find the confidence in
the ``multiStepPredictions`` (for both ``1`` and ``5`` step predictions).

When this example program is run, you can see both predictions and their
confidences in the console output, which should look something like this:

::

    1-step:             35.7 (65.53%)	5-step:             35.7 (99.82%)
    1-step:             38.9 (65.73%)	5-step:             23.5 (99.82%)
    1-step:             36.6 (99.11%)	5-step:             35.7 (99.81%)
    1-step:             38.9 (85.73%)	5-step:             36.6 (99.96%)
    1-step:             38.2 (89.59%)	5-step:             38.2 (92.61%)

**Congratulations! You've got HTM predictions for a scalar data stream!**
