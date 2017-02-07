@0x9a7d99fd22a73750;

using import "/nupic/proto/TemporalMemoryProto.capnp".TemporalMemoryProto;

# Next ID: 11
struct TPRegionProto {
  temporalImp @0 :Text;
  temporalMemory @1 :TemporalMemoryProto;
  columnCount @2 :UInt32;
  inputWidth @3 :UInt32;
  cellsPerColumn @4 :UInt32;
  learningMode @5 :UInt32;
  inferenceMode @6 :UInt32;
  anomalyMode @7 :UInt32;
  topDownMode @8 :UInt32;
  computePredictedActiveCellIndices @9 :UInt32;
  orColumnOutputs @10 :UInt32;
}

