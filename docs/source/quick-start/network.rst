.. include:: common.rst

Network API
-----------

See the `Network API Guide <../guides/network.html>`_ for an overview of this API.

Here is the complete program we are going to use as an example. In sections
below, we'll break it down into parts and explain what is happening (without
some of the plumbing details).

.. literalinclude:: ../../examples/network/complete-network-example.py

Network Parameters
^^^^^^^^^^^^^^^^^^

Before you can create an HTM network, you need to have model (or network) parameters
defined in a file. These model parameters contain many details about how the HTM
network will be constructed, what encoder configurations will be used, and
individual algorithm parameters that can drastically affect how a model
operates. The model parameters we're using in this Quick Start
`can be found here <example-model-params.html>`_.

To use model parameters, they can be written to a file and imported into
your script. In this example, our model parameters existing in a
`YAML <http://yaml.org/>`_ file called ``params.yaml`` and are identical to
those `linked above <example-model-params.html>`_.


To import the model params from a YAML file:

.. literalinclude:: ../../examples/network/example-yaml-import.py

The dictionary ``modelParams`` is what you will use to parametrize your
HTM network. We'll do that in the next sections of this example.

Create a Network
^^^^^^^^^^^^^^^^

Create an HTM network with :class:`.Network`:

.. literalinclude:: ../../examples/network/example-create-network.py

Now we need to add several regions to this network:

- Sensor Region (:class:`nupic.regions.record_sensor.RecordSensor`)
- Spatial Pooler Region (:class:`nupic.regions.sp_region.SPRegion`)
- Temporal Memory Region (:class:`nupic.regions.tm_region.TMRegion`)
- Classifier Region (:class:`nupic.regions.sdr_classifier_region.SDRClassifierRegion`)

The regions will be linked serially. In the next sections, we'll cover how to
create regions with the right parameters and how to link them.


Add a Sensor Region
^^^^^^^^^^^^^^^^^^^

Let's add a region of type :class:`.RecordSensor`.

.. literalinclude:: ../../examples/network/example-add-sensor-region.py

This region is in charge of sensing the input data. It does not require any
particular parameters (hence the ``'{}'``) but it does need a Data Source
as well as an Encoder. We'll add that next.


Add a Data Source to the Sensor Region
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A data source is in charge of producing the data that will be fed to the HTM
network. You can create a data source that reads from a CSV file
with :class:`.FileRecordStream`.

.. literalinclude:: ../../examples/network/example-data-source.py

.. note::
    The input CSV needs to have specific headers.
    More details `here <example-data.html>`_.


Add an Encoder to the Sensor Region
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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

Let's create an encoder and add it the Sensor Region:

 .. literalinclude:: ../../examples/network/example-create-encoder.py


Add a Spatial Pooler Region
^^^^^^^^^^^^^^^^^^^^^^^^^^^

When creating a region, we always need to make sure that the output width of
the previous region matches the input width of the following region. In the
case of the Spatial Pooler region, the input width was not specified in the
``modelParams``, so we need to set it.

 .. literalinclude:: ../../examples/network/example-add-sp.py

Add a Temporal Memory Region
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

 .. literalinclude:: ../../examples/network/example-add-tm.py


Add a Classifier Region
^^^^^^^^^^^^^^^^^^^^^^^

 .. literalinclude:: ../../examples/network/example-add-classifier.py


Link all Regions
^^^^^^^^^^^^^^^^

Now that we have created all regions, we need to link them together. Links
are responsible for passing information from one region to the next.

First, we'll add the link in charge of passing the data from ``sensorRegion``
to ``spRegion``. Then we'll create 2 ``feedForward`` links: one from the
SP to the TM and another from the TM to the Classifier. Finally, we'll add a
couple of special links between ``sensorRegion`` and ``classifierRegion``.
These links make it possible for the classifier to map predicted cell states
to actual values learned from the input data.


.. literalinclude:: ../../examples/network/example-link-all.py


Set the Predicted Field Index
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To be able to make predictions, the network needs to know what field we want
to predict. So let's set the predicted field index.


.. literalinclude:: ../../examples/network/example-set-predicted-field.py

Make sure that the predicted field index that you are passing to the classifier
region is using the same indexing as the data source. This is the role of the
first line in the code snippet above.


Enable Learning and Inference
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
If you want the network to learn on the input data, you need to enable learning.
Note that enabling learning is independent from enabling inference. So if you
want the network to output predictions, you need to enable inference as well.
Let's enable both in our case, because we want the network to learn and make predictions.

.. literalinclude:: ../../examples/network/example-enable-learning-and-inference.py


Run the Network
^^^^^^^^^^^^^^^
Before running the network, you need to initialize it. After that, you can run
the network ``N`` iterations at a time.

.. literalinclude:: ../../examples/network/example-run-network.py

Here we run the network ``1`` iteration at a time because we want to extract
the prediction results at each time step.


Getting Predictions
^^^^^^^^^^^^^^^^^^^

In the classifier configuration of our `model parameters <example-model-params.html>`_,
identified as ``modelParams.clParams``, the ``steps`` value tells the model how
many steps into the future to predict. In this case, we are predicting both one
and five steps into the future as shown by the value ``1,5``.

You can use the method ``getOutputData()`` to get output predictions from the
classifier region. In our case, we are interested in:

.. code-block:: python

    actualValues = classifierRegion.getOutputData("actualValues")
    probabilities = classifierRegion.getOutputData("probabilities")


Refer to the documentation of :class:`~nupic.regions.sdr_classifier_region.SDRClassifierRegion` for
more information about output values and their structure.

We'll use the helper function below to extract predictions more easily from
the classifier region:

.. literalinclude:: ../../examples/network/example-extract-results.py

Once you put all this together and run the `full example <network.html>`_,
you can see both predictions and their confidences in the console output,
which should look something like this:

::

    1-step:    45.6100006104 (96.41%)	5-step:              0.0 (0.1883%)
    1-step:    43.4000015259 (3.969%)	5-step:              0.0 (0.1883%)
    1-step:    43.4000015259 (4.125%)	5-step:              0.0 (0.1883%)

**Congratulations! You've got HTM predictions for a scalar data stream!**
