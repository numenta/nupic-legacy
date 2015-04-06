@0xf07c1f24bf12fe13;

using import "adaptivescalar.capnp".AdaptiveScalarEncoderProto;
using import "category.capnp".CategoryEncoderProto;
using import "coordinate.capnp".CoordinateEncoderProto;
using import "date.capnp".DateEncoderProto;
using import "delta.capnp".DeltaEncoderProto;
using import "geospatial_coordinate.capnp".GeospatialCoordinateEncoderProto;
using import "logenc.capnp".LogEncoderProto;
using import "pass_through_encoder.capnp".PassThroughEncoderProto;
using import "random_distributed_scalar.capnp".RandomDistributedScalarEncoderProto;
using import "scalar.capnp".ScalarEncoderProto;
using import "sdrcategory.capnp".SDRCategoryEncoderProto;
using import "sparse_pass_through_encoder.capnp".SparsePassThroughEncoderProto;

# Next ID: 14
struct MultiEncoderProto {
  struct IntType {
    value @0 :UInt32;
  }

  #Next ID 1
  struct EncoderMap(Index, Name, Encoder, Offset) {
    encoders @0 :List(EncoderDetails);

    # Next ID: 4
    struct EncoderDetails {
      index @0 :Index;
      name @1 :Name;
      encoder @2 :Encoder;
      offset @3 :Offset;
    }
  }

  width @0 :UInt32;
  adaptiveScalarEncoders @1 :EncoderMap(IntType, Text, AdaptiveScalarEncoderProto, IntType);
  categoryEncoders @2 :EncoderMap(IntType, Text, CategoryEncoderProto, IntType);
  coordinateEncoders @3 :EncoderMap(IntType, Text, CoordinateEncoderProto, IntType);
  dateEncoders @4 :EncoderMap(IntType, Text, DateEncoderProto, IntType);
  deltaEncoders @5 :EncoderMap(IntType, Text, DeltaEncoderProto, IntType);
  geospatialCoordinateEncoders @6 :EncoderMap(IntType, Text, GeospatialCoordinateEncoderProto, IntType);
  logEncoders @7 :EncoderMap(IntType, Text, LogEncoderProto, IntType);
  passThroughEncoders @8 :EncoderMap(IntType, Text, PassThroughEncoderProto, IntType);
  randomDistributedScalarEncoders @9 :EncoderMap(IntType, Text, RandomDistributedScalarEncoderProto, IntType);
  scalarEncoders @10 :EncoderMap(IntType, Text, ScalarEncoderProto, IntType);
  sdrCategoryEncoders @11 :EncoderMap(IntType, Text, SDRCategoryEncoderProto, IntType);
  sparsePassThroughEncoders @12 :EncoderMap(IntType, Text, SparsePassThroughEncoderProto, IntType);
  name @13 :Text;
}
