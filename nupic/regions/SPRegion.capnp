@0x9c0abb4ca2e06884;

using import "../bindings/proto/SpatialPoolerProto.capnp".SpatialPoolerProto;

struct SpatialPoolerRegionProto {
  version @0 :UInt16;

  spatialImp @1 :Text;
  spatialInstance @2 :SpatialPoolerProto;

  columnCount @3 :UInt32;
  inputWidth @4 :UInt32;
  learningMode @5 :Bool;
  inferenceMode @6 :Bool;
  anomalyMode @7 :Bool;
  topDownMode @8 :Bool;

  breakPdb @9 :Bool;
  breakKomodo @10 :Bool;
}
