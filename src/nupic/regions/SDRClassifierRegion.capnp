@0xa86c32f1ece85ed0;

using import "/nupic/proto/SdrClassifier.capnp".SdrClassifierProto;

# Next ID: 6
struct SDRClassifierRegionProto {
  implementation @0 :Text;
  sdrClassifier @1 :SdrClassifierProto;
  steps @2 :Text;
  alpha @3 :Float32;
  verbosity @4 :UInt32;
  maxCategoryCount @5 :UInt32;
}
