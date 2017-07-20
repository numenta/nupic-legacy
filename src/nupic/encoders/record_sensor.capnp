@0xad4890be062550a2;

using import "/nupic/encoders/multi.capnp".MultiEncoderProto;

# Next ID: 5
struct RecordSensorProto {
  encoder @0 :MultiEncoderProto;
  disabledEncoder @1 :MultiEncoderProto;
  topDownMode @2 :UInt32;
  verbosity @3 :UInt32;
  numCategories @4 :UInt32;
}
