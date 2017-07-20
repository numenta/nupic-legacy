@0xf4a1336f535a66ba;

using import "/nupic/proto/SpatialPoolerProto.capnp".SpatialPoolerProto;

# Next ID: 8
struct SPRegionProto {
  spatialImp @0 :Text;
  spatialPooler @1 :SpatialPoolerProto;
  columnCount @2 :UInt32;
  inputWidth @3 :UInt32;
  learningMode @4 :UInt32;
  inferenceMode @5 :UInt32;
  anomalyMode @6 :UInt32;
  topDownMode @7 :UInt32;
}
