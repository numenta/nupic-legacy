@0xfa7d16f86048a6e4;

struct ScalarEncoderProto {
  # ScalarEncoder() constructor signature

  w @0 :UInt32;
  minval @1 :Float32;
  maxval @2 :Float32;
  periodic @3 :Bool;
  n @4 :UInt32;
  radius @5 :Float32;
  resolution @6 :Float32;
  name @7 :Text;
  verbosity @8 :UInt8;
  clipInput @9 :Bool;

  # The following are not required part of the ScalarEncoder() constructor
  # signature, but are derived in __init__() and represent the internal state
  # of an instance that must be preserved between write and read

  halfwidth @10 :UInt32;
  padding @11 :UInt32;
  rangeInternal @12 :Float32;
  nInternal @13 :UInt32;
  range @14 :UInt32;
}
