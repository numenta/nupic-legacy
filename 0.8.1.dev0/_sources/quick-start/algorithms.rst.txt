.. include:: common.rst

Algorithms API
--------------

See the `Algorithms API <../api/algorithms/>`_ for an overview of this API.

Here is the complete program we are going to use as an example. Descriptions of
the algorithm parameters we're using in this Quick Start
`can be found here <example-model-params.html>`_. In sections below, we'll
break it down into parts and explain what is happening (without some of the
plumbing details).

.. literalinclude:: ../../examples/algo/complete-algo-example.py


Encoding Data
^^^^^^^^^^^^^

For this quick start, we'll be using the same raw input data file described
`here <example-data.html>`_ in detail and used for the
`OPF Quick Start <opf.html>`_. But we will be ignoring the file format and just
looping over the CSV, encoding one row at a time programmatically before sending
encodings to the Spatial Pooler and Temporal Memory algorithms.

One Row Of Data
+++++++++++++++

Each row of data in this input file is formatted like this:

::

    7/2/10 9:00,41.5

We need to encode this into three encodings:

* time of day
* weekend or not
* scalar value for energy consumption

Creating Encoders
+++++++++++++++++

First, let's create the encoders we'll use to encode different semantics
of our input data stream:

.. literalinclude:: ../../examples/algo/create-encoders.py

Encoding Data
+++++++++++++

With these encoders created, we can loop over each row of data, encode it into
bits, and concatenate them together to form a complete representation for the next
step:

.. literalinclude:: ../../examples/algo/encode-data.py

Each encoding will print to the console and look something like this:

::

    [0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
     0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
     0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
     0 0 0 0 0 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 0 0 0 0 0 0 0 0 0 0 0
     0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
     0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
     0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
     0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
     0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
     0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
     0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
     0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
     0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
     0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
     0 0 0 0 0 0 0 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 0 0 0 0 0 0 0 0 0
     0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 0 0 1 0 0 0 0 1 0 1 1 0 0 0 0
     0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0
     0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
     0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
     1 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 0 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
     0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
     0 0 0 0 0 1 0 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
     0 0 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
     0 0 0 0 0 0 0 0 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0
     0 0 0 0 0 0 0 0 0 0 0 0 1 0 1 0 0 0 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
     0 0 0 0 0 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0]

By visually inspecting this output, you can see the buckets of continuous on
bits representing the different encodings for time of day and weekend. Near the
bottom of the encoding are the bits representing scalar data, distributed
throughout the space by the :class:`.RandomDistributedScalarEncoder`.

Spatial Pooling
^^^^^^^^^^^^^^^

Now that we have data encoded into a binary format with semantic meaning, we can
pass each encoding to into the Spatial Pooling algorithm.

Creating the SP
+++++++++++++++

First, we must identify parameters for the creation of the
:class:`.SpatialPooler` instance. We will be using the same parameters
identified in the `OPF Quick Start <opf.html>`_ document's
`model parameters <example-model-params.html>`_ (see the ``spParams`` section).

.. literalinclude:: ../../examples/algo/create-sp.py

Running the SP
++++++++++++++

The :class:`.SpatialPooler` instance should be created once, and each encoded
row of data passed into its :meth:`~.SpatialPooler.compute` function.

.. literalinclude:: ../../examples/algo/sp-compute.py

This will print out the indices of the active mini-columns in the SP at each
time step, and will look something like this:

::

    [ 929  932  938  939  940  941  942  943  944  945  946  949  950  951  953
      955  956  957  958  960  961  962  964  965  966  968  969  970  971  973
      974  975  977  978  979  980 1105 1114 1120 1129]

Temporal Memory
^^^^^^^^^^^^^^^

The :class:`.TemporalMemory` algorithm works within the active mini-columns
created by the :class:`.SpatialPooler`. Given a list of active columns, it
performs sequence memory operations by activating individual cells within each
mini-column structure.

Creating the TM
+++++++++++++++

Just like the SP, we must create an instance of the
:class:`.TemporalMemory` with parameters we identified in the
`OPF Quick Start <opf.html>`_ document's
`model parameters <example-model-params.html>`_ (see the ``tmParams`` section).

.. literalinclude:: ../../examples/algo/create-tm.py

Running the TM
++++++++++++++

Now, after :meth:`.SpatialPooler.compute`, we will run the
:meth:`.TemporalMemory.compute` function using the active columns presented by
the SP. Then we can call :meth:`.TemporalMemory.getActiveCells` to return the
indices of the active cells within the structure. All active cells will fall
within active mini-columns.

.. literalinclude:: ../../examples/algo/tm-compute.py

Now we have an array of indices for each active cell in the HTM structure. When
printed to the console, each step looks like this:

::

    [13817, 13856, 14003, 14078, 14104, 14159, 14259, 14313, 14351, 14377, 14415,
    14524, 14563, 14594, 14652, 14686, 14715, 14763, 14863, 14950, 15037, 15053,
    15107, 15209, 15258, 15412, 15449, 35008, 35009, 35010, 35011, 35012, 35013,
    35014, 35015, 35016, 35017, 35018, 35019, 35020, 35021, 35022, 35023, 35024,
    35025, 35026, 35027, 35028, 35029, 35030, 35031, 35032, 35033, 35034, 35035,
    35036, 35037, 35038, 35039, 35040, 35041, 35042, 35043, 35044, 35045, 35046,
    35047, 35048, 35049, 35050, 35051, 35052, 35053, 35054, 35055, 35056, 35057,
    35058, 35059, 35060, 35061, 35062, 35063, 35064, 35065, 35066, 35067, 35068,
    35069, 35070, 35071, 35360, 35361, 35362, 35363, 35364, 35365, 35366, 35367,
    35368, 35369, 35370, 35371, 35372, 35373, 35374, 35375, 35376, 35377, 35378,
    35379, 35380, 35381, 35382, 35383, 35384, 35385, 35386, 35387, 35388, 35389,
    35390, 35391, 35424, 35425, 35426, 35427, 35428, 35429, 35430, 35431, 35432,
    35433, 35434, 35435, 35436, 35437, 35438, 35439, 35440, 35441, 35442, 35443,
    35444, 35445, 35446, 35447, 35448, 35449, 35450, 35451, 35452, 35453, 35454,
    35455, 35488, 35489, 35490, 35491, 35492, 35493, 35494, 35495, 35496, 35497,
    35498, 35499, 35500, 35501, 35502, 35503, 35504, 35505, 35506, 35507, 35508,
    35509, 35510, 35511, 35512, 35513, 35514, 35515, 35516, 35517, 35518, 35519,
    35584, 35585, 35586, 35587, 35588, 35589, 35590, 35591, 35592, 35593, 35594,
    35595, 35596, 35597, 35598, 35599, 35600, 35601, 35602, 35603, 35604, 35605,
    35606, 35607, 35608, 35609, 35610, 35611, 35612, 35613, 35614, 35615, 35616,
    35617, 35618, 35619, 35620, 35621, 35622, 35623, 35624, 35625, 35626, 35627,
    35628, 35629, 35630, 35631, 35632, 35633, 35634, 35635, 35636, 35637, 35638,
    35639, 35640, 35641, 35642, 35643, 35644, 35645, 35646, 35647, 35648, 35649,
    35650, 35651, 35652, 35653, 35654, 35655, 35656, 35657, 35658, 35659, 35660,
    35661, 35662, 35663, 35664, 35665, 35666, 35667, 35668, 35669, 35670, 35671,
    35672, 35673, 35674, 35675, 35676, 35677, 35678, 35679, 35840, 35841, 35842,
    35843, 35844, 35845, 35846, 35847, 35848, 35849, 35850, 35851, 35852, 35853,
    35854, 35855, 35856, 35857, 35858, 35859, 35860, 35861, 35862, 35863, 35864,
    35865, 35866, 35867, 35868, 35869, 35870, 35871, 35936, 35937, 35938, 35939,
    35940, 35941, 35942, 35943, 35944, 35945, 35946, 35947, 35948, 35949, 35950,
    35951, 35952, 35953, 35954, 35955, 35956, 35957, 35958, 35959, 35960, 35961,
    35962, 35963, 35964, 35965, 35966, 35967, 35968, 35969, 35970, 35971, 35972,
    35973, 35974, 35975, 35976, 35977, 35978, 35979, 35980, 35981, 35982, 35983,
    35984, 35985, 35986, 35987, 35988, 35989, 35990, 35991, 35992, 35993, 35994,
    35995, 35996, 35997, 35998, 35999, 36352, 36353, 36354, 36355, 36356, 36357,
    36358, 36359, 36360, 36361, 36362, 36363, 36364, 36365, 36366, 36367, 36368,
    36369, 36370, 36371, 36372, 36373, 36374, 36375, 36376, 36377, 36378, 36379,
    36380, 36381, 36382, 36383, 36576, 36577, 36578, 36579, 36580, 36581, 36582,
    36583, 36584, 36585, 36586, 36587, 36588, 36589, 36590, 36591, 36592, 36593,
    36594, 36595, 36596, 36597, 36598, 36599, 36600, 36601, 36602, 36603, 36604,
    36605, 36606, 36607]

That's a lot of active cells! But remember our structure is 65,536 cells total
(2,048 columns, each with 32 cells), so these active cells represent only about
2% of the total number of cells.

Predictive Cells
++++++++++++++++

The :class:`.TemporalMemory` interface has many methods of getting cellular
state information. In the section above, we used the
:meth:`.TemporalMemory.getActiveCells` function to get the indices of active
cells. We can also get predictive cells by calling
:meth:`.TemporalMemory.getPredictiveCells`, which returns an array of indices of
cells in a depolarized, or predictive, state.

Getting Predictions
^^^^^^^^^^^^^^^^^^^

In order to associate the predictive cells in the TM to an input pattern, we use
a non biological method of classification. This requires that we add a
`Classifier <../api/algorithms/classifiers.html>`_ to do this work. We will be using the
:class:`.SDRClassifier` to do this.

The goal is to extract a prediction for the value of `consumption` that was
passed into the system.

Creating an SDR Classifier
++++++++++++++++++++++++++

We will use the :class:`.SDRClassifierFactory` for this and use the default
factory settings.

.. literalinclude:: ../../examples/algo/create-classifier.py

Running the Classifier
++++++++++++++++++++++

In order to call :meth:`.SDRClassifier.compute` on the classifier, we need pass
it both the actual ``consumption`` value and the ``bucketIdx`` (bucket index),
which we can get from the encoder itself. This will allow the encoder to
classify predictions into a previously seen value.

.. literalinclude:: ../../examples/algo/classifier-compute.py

The ``classiferResult`` contains predicted values. Running the code above will
print the best prediction and its associated probability to the console:

::

    1-step:    5.11804943107 (52.12%)

**Congratulations! You've got HTM predictions for a scalar data stream!**
