@0xf07c1f24bf12fe13;

using import "adaptivescalar.capnp".AdaptiveScalarEncoderProto;
using import "category.capnp".CategoryEncoderProto;
using import "coordinate.capnp".CoordinateEncoderProto;
using import "date.capnp".DateEncoderProto;
using import "delta.capnp".DeltaEncoderProto;
using import "geospatial_coordinate.capnp".GeospatialCoordinateEncoderProto;
using import "log.capnp".LogEncoderProto;
using import "pass_through.capnp".PassThroughEncoderProto;
using import "random_distributed_scalar.capnp".RandomDistributedScalarEncoderProto;
using import "scalar.capnp".ScalarEncoderProto;
using import "sdrcategory.capnp".SDRCategoryEncoderProto;
using import "sparse_pass_through_encoder.capnp".SparsePassThroughEncoderProto;

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
