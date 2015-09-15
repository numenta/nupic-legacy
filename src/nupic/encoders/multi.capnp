@0xf07c1f24bf12fe13;

using import "/nupic/encoders/adaptivescalar.capnp".AdaptiveScalarEncoderProto;
using import "/nupic/encoders/category.capnp".CategoryEncoderProto;
using import "/nupic/encoders/coordinate.capnp".CoordinateEncoderProto;
using import "/nupic/encoders/date.capnp".DateEncoderProto;
using import "/nupic/encoders/delta.capnp".DeltaEncoderProto;
using import "/nupic/encoders/geospatial_coordinate.capnp".GeospatialCoordinateEncoderProto;
using import "/nupic/encoders/log.capnp".LogEncoderProto;
using import "/nupic/encoders/pass_through.capnp".PassThroughEncoderProto;
using import "/nupic/encoders/random_distributed_scalar.capnp".RandomDistributedScalarEncoderProto;
using import "/nupic/encoders/scalar.capnp".ScalarEncoderProto;
using import "/nupic/encoders/sdrcategory.capnp".SDRCategoryEncoderProto;
using import "/nupic/encoders/sparse_pass_through_encoder.capnp".SparsePassThroughEncoderProto;

# Next ID: 3
struct MultiEncoderProto {
  # Next ID: 14
  struct EncoderUnion {
    union {
      adaptiveScalarEncoder @0 :AdaptiveScalarEncoderProto;
      categoryEncoder @1 :CategoryEncoderProto;
      coordinateEncoder @2 :CoordinateEncoderProto;
      dateEncoder @3 :DateEncoderProto;
      deltaEncoder @4 :DeltaEncoderProto;
      geospatialCoordinateEncoder @5 :GeospatialCoordinateEncoderProto;
      logEncoder @6 :LogEncoderProto;
      passThroughEncoder @7 :PassThroughEncoderProto;
      randomDistributedScalarEncoder @8 :RandomDistributedScalarEncoderProto;
      scalarEncoder @9 :ScalarEncoderProto;
      sdrCategoryEncoder @10 :SDRCategoryEncoderProto;
      sparsePassThroughEncoder @11 :SparsePassThroughEncoderProto;
    }
    name @12 :Text;
    offset @13 :UInt32;
  }

  name @0 :Text;
  encoders @1 :List(EncoderUnion);
}
