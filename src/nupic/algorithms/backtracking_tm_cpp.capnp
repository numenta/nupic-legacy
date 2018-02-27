@0x929156e0dfbd37d6;

using import "/nupic/algorithms/backtracking_tm.capnp".BacktrackingTMProto;
using import "/nupic/proto/Cells4.capnp".Cells4Proto;

struct BacktrackingTMCppProto {
  baseTM @0 :BacktrackingTMProto;
  cells4 @1 :Cells4Proto;
  makeCells4Ephemeral @2 :Bool;
  seed @3 :Int64;
  checkSynapseConsistency @4 :Bool;
  initArgs @5 :Text;
}
