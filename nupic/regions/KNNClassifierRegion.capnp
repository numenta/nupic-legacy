@0x9409f71f146380ac;

using import "../bindings/proto/RandomProto.capnp".RandomProto;
using import "../algorithms/KNNClassifier.capnp".KNNClassifierProto;

struct KNNClassifierRegionProto {
  verbosity @0 :UInt8;
  random @1 :RandomProto;

  classifierInstance @2 :KNNClassifierProto;

  learningMode @3 :Bool;
  inferenceMode @4 :Bool;

  outputProbabilitiesByDist @5 :Bool;
  epoch @6 :UInt32;
  acceptanceProbability @7 :Float32;
  confusion @8: List(List(Float32));
  keepAllDistances @9 :Bool;
  protoScoreCount @10 :UInt32;
  useAuxiliary @11 :Bool;
  justUseAuxiliary @12 :Bool;

  doSphering @13 :Bool;
  normOffset @14 :Float32;
  normScale @15 :Float32;
  samples @16 :List(Float32);
  labels @17 :List(Float32);

  doSelfValidation @18 :Bool;

  maxCategoryCount @19 :UInt32;
  bestPrototypeIndexCount @20 :UInt32;
}
