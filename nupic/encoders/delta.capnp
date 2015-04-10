@0xdf5bd1fedf76298f;

using import "/nupic/encoders/adaptivescalar.capnp".AdaptiveScalarEncoderProto;

struct DeltaEncoderProto {
  width @0 :UInt32;
  name @1 :Text;
  n @2 :UInt32;
  adaptiveScalarEnc @3 :AdaptiveScalarEncoderProto;
  prevAbsolute @4 :Float32;
  prevDelta @5 :Float32;
  stateLock @6 :Bool;
}
