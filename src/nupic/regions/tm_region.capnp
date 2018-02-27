@0xb9d11462f08c1dee;

using import "/nupic/algorithms/backtracking_tm.capnp".BacktrackingTMProto;
using import "/nupic/algorithms/backtracking_tm_cpp.capnp".BacktrackingTMCppProto;
using import "/nupic/proto/TemporalMemoryProto.capnp".TemporalMemoryProto;

# Next ID: 13
struct TMRegionProto {
  temporalImp @0 :Text;
  union {
    temporalMemory @1 :TemporalMemoryProto;
    backtrackingTM @11 :BacktrackingTMProto;
    backtrackingTMCpp @12 :BacktrackingTMCppProto;
  }
  columnCount @2 :UInt32;
  inputWidth @3 :UInt32;
  cellsPerColumn @4 :UInt32;
  learningMode @5 :Bool;
  inferenceMode @6 :Bool;
  anomalyMode @7 :Bool;
  topDownMode @8 :Bool;
  computePredictedActiveCellIndices @9 :Bool;
  orColumnOutputs @10 :Bool;
}

