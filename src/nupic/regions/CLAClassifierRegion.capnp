@0x86ee045dcbcfbf3f;

using import "/nupic/proto/ClaClassifier.capnp".ClaClassifierProto;

# Next ID: 6
struct CLAClassifierRegionProto {
  classifierImp @0 :Text;
  claClassifier @1 :ClaClassifierProto;
  steps @2 :Text;
  alpha @3 :Float32;
  verbosity @4 :UInt32;
  maxCategoryCount @5 :UInt32;
}
