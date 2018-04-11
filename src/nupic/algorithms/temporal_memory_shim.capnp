@0xbf2d8ef193440c2f

using import "/nupic/algorithms/backtracking_tm_cpp_capnp".BacktrackingTMCppProto;
using import "/nupic/proto/ConnectionsProto_capnp".ConnectionsProto;

# Next ID: 3
struct TemporalMemoryShimProto {
  baseTM @0 :BacktrackingTMCppProto;
  predictiveCells @1 :List(UInt32);
  connections @2 :ConnectionsProto;
}
