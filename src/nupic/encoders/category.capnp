@0xb639caa166140b0f;

using import "/nupic/encoders/scalar.capnp".ScalarEncoderProto;

# Next ID: 5
struct CategoryEncoderProto {

  # Next ID: 2
  struct CategoryMapping {
    index @0 :UInt32;
    category @1 :Text;
  }

  width @0 :UInt32;
  indexToCategory @1 :List(CategoryMapping);
  name @2 :Text;
  verbosity @3 :UInt8;
  encoder @4 :ScalarEncoderProto;
}
