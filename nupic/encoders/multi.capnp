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

# Next ID: 14
struct MultiEncoderProto {
  struct IntType {
    value @0 :UInt32;
  }

  # Next ID: 4
  struct EncoderDetails(Index, Name, Encoder, Offset) {
    index @0 :Index;
    name @1 :Name;
    encoder @2 :Encoder;
    offset @3 :Offset;
  }

  width @0 :UInt32;

  struct EncoderUnion {
    union {
      adaptiveScalarEncoder @0 :EncoderDetails(IntType, Text, AdaptiveScalarEncoderProto, IntType);
      categoryEncoder @1 :EncoderDetails(IntType, Text, CategoryEncoderProto, IntType);
      coordinateEncoder @2 :EncoderDetails(IntType, Text, CoordinateEncoderProto, IntType);
      dateEncoder @3 :EncoderDetails(IntType, Text, DateEncoderProto, IntType);
      deltaEncoder @4 :EncoderDetails(IntType, Text, DeltaEncoderProto, IntType);
      geospatialCoordinateEncoder @5 :EncoderDetails(IntType, Text, GeospatialCoordinateEncoderProto, IntType);
      logEncoder @6 :EncoderDetails(IntType, Text, LogEncoderProto, IntType);
      passThroughEncoder @7 :EncoderDetails(IntType, Text, PassThroughEncoderProto, IntType);
      randomDistributedScalarEncoder @8 :EncoderDetails(IntType, Text, RandomDistributedScalarEncoderProto, IntType);
      scalarEncoder @9 :EncoderDetails(IntType, Text, ScalarEncoderProto, IntType);
      sdrCategoryEncoder @10 :EncoderDetails(IntType, Text, SDRCategoryEncoderProto, IntType);
      sparsePassThroughEncoder @11 :EncoderDetails(IntType, Text, SparsePassThroughEncoderProto, IntType);
    }
  }

  name @1 :Text;
  allEncoders @2 :List(EncoderUnion);
}
