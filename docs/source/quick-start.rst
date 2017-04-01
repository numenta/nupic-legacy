Quick Start
===========

Install NuPIC
-------------

.. code-block:: bash

   pip install nupic [--user]

The ``--user`` is in brackets because it is optional. See the
`pip reference guide <https://pip.pypa.io/en/stable/reference/pip_install/#cmdoption-user>`_
for details.

The output of this command should end with:

    Successfully installed nupic-X.X.X nupic.bindings-X.X.X

If your installation was unsuccessful, you can find help on
`NuPIC Forums <https://discourse.numenta.org/c/nupic/>`_ and on
`Github <https://github.com/numenta/nupic/issues/>`_.

Choose Your API
---------------

See the `OPF <guide-opf.html>`_ and `Network API <guide-network-api.html>`_
sections of the `Guide <guide.html>`_.

OPF
---

Here is the complete program we are going to use as an example. In sections
below, we'll break it down into parts and explain what is happening (wintout
some of the plumbing details).

.. literalinclude:: ../examples/complete-example.py

Model Parameters
^^^^^^^^^^^^^^^^

Before you can create an OPF model, you need to have model parameters defined in
a python file. These model parameters contain many details about how the HTM
network will be constructed, what encoder configurations will be used, and
individual algorithm parameters that can drastically affect how a model
operates. The model parameters we're using in this Quick Start
`can be found here <example-model-params.html>`_.

To use model parameters, they can be written to a python file and imported into
your script. In this example, our model parameters existing in a python file
called ``model_params.py`` and are identical to those
`linked above <example-model-params.html>`_.

Create an OPF Model
^^^^^^^^^^^^^^^^^^^

The easiest way to create a model once you have access to model parameters is by
using the :class:`.ModelFactory`.

.. literalinclude:: ../examples/create-model-example.py

The resulting ``model`` will be an instance of :class:`.CLAModel`.

Feed the Model Data
^^^^^^^^^^^^^^^^^^^

The data we want to feed into the model looks like this:

.. literalinclude:: ../examples/gymdata-example.csv

Our `model parameters <example-model-params.html>`_ define how this data will be
encoded in the ``encoders`` section:

.. literalinclude:: ../examples/example-model-param-encoders.py

Notice that three semantic values are being encoded into the input space. The
first is the scalar energy ``consumption`` value, which is being encoded with
the :class:`.RandomDistributedScalarEncoder`. The next two values represent two
different aspects of time. The encoder called ``timestamp_timeOfDay`` encodes
the time of day, while the ``timestamp_weekend`` encoder will output different
representations for weekends vs weekdays.

    For details about encoding and how these encoders work, see the the
    `HTM School <https://numenta.org/htm-school/>`_ episodes on encoders.

Now that you see the raw input data and how it is configured to be encoded into
binary arrays for the HTM to process it, let's see the code that actually reads
the CSV data file and runs it through our ``model``.

.. literalinclude:: ../examples/load-model-example.py

Extract the results
^^^^^^^^^^^^^^^^^^^

In the classifier configuration of our `model parameters <example-model-params.html>`_,
identified as ``modelParams.clParams``, the ``steps`` value tells the model how
many steps into the future to predict. In this case, we are predicting both one
and five steps into the future as shown by the value ``1,5``.

This means the ``results`` object will have prediction information keyed by both
``1`` and ``5``.

.. literalinclude:: ../examples/results-example.py


Network API
-----------
