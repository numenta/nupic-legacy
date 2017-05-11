@0x94b5c39874f24431;

using import "/nupic/encoders/scalar.capnp".ScalarEncoderProto;

struct LogEncoderProto {
  verbosity @0 :UInt8;
  minScaledValue @1 :Float32;
  maxScaledValue @2 :Float32;
  clipInput @3 :Bool;
  minval @4 :Float32;
  maxval @5 :Float32;
  encoder @6 :ScalarEncoderProto;
  name @7 :Text;
}
