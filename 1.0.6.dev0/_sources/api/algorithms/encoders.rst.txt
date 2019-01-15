Encoders
--------

.. automodule:: nupic.encoders.base

Base Encoder
^^^^^^^^^^^^

.. autoclass:: nupic.encoders.base.Encoder
   :show-inheritance:
   :members:

Encoder Result
^^^^^^^^^^^^^^

.. autoclass:: nupic.encoders.base.EncoderResult

Category Encoders
^^^^^^^^^^^^^^^^^

.. autoclass:: nupic.encoders.category.CategoryEncoder
   :show-inheritance:

.. autoclass:: nupic.encoders.sdr_category.SDRCategoryEncoder
   :show-inheritance:

Scalar Encoders
^^^^^^^^^^^^^^^

.. autoclass:: nupic.encoders.scalar.ScalarEncoder
   :show-inheritance:

.. autoclass:: nupic.encoders.adaptive_scalar.AdaptiveScalarEncoder
   :show-inheritance:

.. autoclass:: nupic.encoders.random_distributed_scalar.RandomDistributedScalarEncoder
   :members: mapBucketIndexToNonZeroBits
   :show-inheritance:

.. autoclass:: nupic.encoders.scalar_space.ScalarSpaceEncoder
   :show-inheritance:

.. autoclass:: nupic.encoders.delta.DeltaEncoder
   :show-inheritance:

.. autoclass:: nupic.encoders.logarithm.LogEncoder
   :show-inheritance:


Date Encoder
^^^^^^^^^^^^

.. autoclass:: nupic.encoders.date.DateEncoder
   :members: getScalars
   :show-inheritance:

Coordinate Encoders
^^^^^^^^^^^^^^^^^^^

.. autoclass:: nupic.encoders.coordinate.CoordinateEncoder
   :show-inheritance:

.. autoclass:: nupic.encoders.geospatial_coordinate.GeospatialCoordinateEncoder
   :members: coordinateForPosition, radiusForSpeed
   :show-inheritance:

Multi Encoder
^^^^^^^^^^^^^

.. autoclass:: nupic.encoders.multi.MultiEncoder
   :members: addEncoder, addMultipleEncoders
   :show-inheritance:

Pass Through Encoders
^^^^^^^^^^^^^^^^^^^^^

Used to pass raw SDRs through to the algorithms when data is already encoded.

.. autoclass:: nupic.encoders.pass_through.PassThroughEncoder
   :members: closenessScores
   :show-inheritance:

.. autoclass:: nupic.encoders.sparse_pass_through.SparsePassThroughEncoder
   :show-inheritance:
