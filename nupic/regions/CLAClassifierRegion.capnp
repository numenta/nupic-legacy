@0xf091b1bb874049df;

using import "../bindings/proto/ClaClassifier.capnp".ClaClassifierProto;

# Next ID: ???
struct CLAClassifierRegionProto {
  version @0 :UInt16;

  classifierImp @1 :Text;
  classifierInstance @2 :ClaClassifierProto;

  learningMode @3 :Bool;
  inferenceMode @4 :Bool;
}
