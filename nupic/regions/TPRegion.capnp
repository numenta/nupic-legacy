@0xf0efb05e82c5561b;

using import "../bindings/proto/TemporalMemoryV1.capnp".TemporalMemoryV1Proto;

struct TemporalMemoryV1RegionProto {
  temporalImp @0 :Text;
  temporalInstance @1 :TemporalMemoryV1Proto;

  columnCount @2 :UInt32;
  inputWidth @3 :UInt32;
  cellsPerColumn @4 :UInt32;
  learningMode @5 :Bool;
  inferenceMode @6 :Bool;
  anomalyMode @7 :Bool;
  topDownMode @8 :Bool;
  computePredictedActiveCellIndices @9 :Bool;

  orColumnOutputs @10 :Bool;

  breakPdb @11 :Bool;
  breakKomodo @12 :Bool;

  storeDenseOutput @13 :Bool;
  cellsSavePath @14 :Text;
}
