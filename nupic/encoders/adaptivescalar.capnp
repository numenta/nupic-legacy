@0xf11485b8c813b489;

using import "/nupic/movingaverage.capnp".MovingAverageProto;

# Next ID: 10
struct AdaptiveScalarEncoderProto {
  w @0 :UInt32;
  minval @1 :Float32;
  maxval @2 :Float32;
  periodic @3 :Bool;
  n @4 :UInt32;
  name @5 :Text;
  verbosity @6 :UInt8;
  clipInput @7 :Bool;
  recordNum @8 :UInt32;
  slidingWindow @9 :MovingAverageProto;
}
