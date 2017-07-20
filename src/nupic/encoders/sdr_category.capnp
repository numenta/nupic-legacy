@0x8017c9c04559354c;

using import "/nupic/proto/RandomProto.capnp".RandomProto;

# Next ID: 7
struct SDRCategoryEncoderProto {
  n @0 :UInt32;
  w @1 :UInt32;
  random @2 :RandomProto;
  verbosity @3 :UInt8;
  name @4 :Text;
  categories @5 :List(Text);
  sdrs @6 :List(List(UInt8));
}
