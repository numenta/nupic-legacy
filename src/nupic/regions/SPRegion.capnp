@0xf4a1336f535a66ba;

using import "/nupic/proto/SpatialPoolerProto.capnp".SpatialPoolerProto;

# Next ID: 7
struct SPRegionProto {
  spatialPooler @0 :SpatialPoolerProto;
  columnCount @1 :UInt32;
  inputWidth @2 :UInt32;
  learningMode @3 :UInt32;
  inferenceMode @4 :UInt32;
  anomalyMode @5 :UInt32;
  topDownMode @6 :UInt32;
}
