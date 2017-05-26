@0xad4890be062550a2;

using import "/nupic/encoders/multi.capnp".MultiEncoderProto;

# Next ID: 5
struct RecordSensorProto {
  encoder @0 :MultiEncoderProto;
  disabledEncoder @1 :MultiEncoderProto;
  verbosity @2 :UInt32;
  numCategories @3 :UInt32;
}
