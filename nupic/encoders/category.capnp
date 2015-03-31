@0xb639caa166140b0f;

using import "scalar.capnp".ScalarEncoderProto;

# Next ID: 6
struct CategoryEncoderProto {

  # Next ID: 2
  struct CategoryMapping {
    index @0 :UInt32;
    category @1 :Text;
  }

  width @0 :UInt32;
  categoryToIndex @1 :List(CategoryMapping);
  indexToCategory @2 :List(CategoryMapping);
  name @3 :Text;
  verbosity @4 :UInt8;
  encoder @5 :ScalarEncoderProto;
}
