Encoders
--------

.. automodule:: nupic.encoders.base

Base Encoder
^^^^^^^^^^^^

.. autoclass:: nupic.encoders.base.Encoder
   :members:

Encoder Result
^^^^^^^^^^^^^^

.. autoclass:: nupic.encoders.base.EncoderResult

Category Encoders
^^^^^^^^^^^^^^^^^

.. autoclass:: nupic.encoders.category.CategoryEncoder
   :show-inheritance:

.. autoclass:: nupic.encoders.sdrcategory.SDRCategoryEncoder
   :show-inheritance:

Scalar Encoder
^^^^^^^^^^^^^^

.. autoclass:: nupic.encoders.scalar.ScalarEncoder
   :show-inheritance:

Adaptive Scalar Encoder
^^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: nupic.encoders.adaptivescalar.AdaptiveScalarEncoder
   :show-inheritance:


Random Distributed Scalar Encoder
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: nupic.encoders.random_distributed_scalar.RandomDistributedScalarEncoder
  :members: mapBucketIndexToNonZeroBits
  :show-inheritance:

DateEncoder
^^^^^^^^^^^

.. autoclass:: nupic.encoders.date.DateEncoder
   :members: getScalars
   :show-inheritance:

CoordinateEncoder
^^^^^^^^^^^^^^^^^

.. autoclass:: nupic.encoders.coordinate.CoordinateEncoder
   :show-inheritance:

GeospatialCoordinateEncoder
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: nupic.encoders.geospatial_coordinate.GeospatialCoordinateEncoder
   :members: coordinateForPosition, radiusForSpeed
   :show-inheritance:

DeltaEncoder
^^^^^^^^^^^^

.. autoclass:: nupic.encoders.delta.DeltaEncoder
   :show-inheritance:

Logarithm Encoder
^^^^^^^^^^^^^^^^^

.. autoclass:: nupic.encoders.logenc.LogEncoder
   :show-inheritance:

MultiEncoder
^^^^^^^^^^^^

.. autoclass:: nupic.encoders.multi.MultiEncoder
   :members:
   :show-inheritance:
