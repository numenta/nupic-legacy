@0x99e493bfb8fbad94;

# Next ID: 31
struct KNNClassifierProto {
  verbosity @0 :UInt8;

  cellsPerCol @1 :UInt32;
  k @2 :UInt32;
  distanceNorm @3 :Float32;
  distanceMethod @4 :Text;
  distanceThreshold @5 :UInt32;
  doBinarization @6 :Bool;
  binarizationThreshold @7 :Float32;
  useSparseMemory @8 :Bool;
  sparseThreshold @9 :Float32;
  relativeThreshold @10 :Bool;
  numWinners @11 :UInt32;
  numSVDSamples @12 :Int32;
  numSVDDims @13 :Int32;
  fractionOfMax @14 :Float32;
  replaceDuplicates @15 :Bool;
  maxStoredPatterns @16 :Int32;

  iterationIdx @17 :Int32;

  numPatterns @18 :Int32;
  memory @19 :List(List(Float32));
  m @20 :List(List(Float32));
  categoryList @21 :List(UInt32);
  categoryRecencyList @22 :List(Int32);
  partitionIdList @23 :List(Int32);
  partitionIdArray @24 :List(Int32);

  s @25 :List(Float64);
  vt @26 :List(List(Float64));
  mean @27 :List(Float64);

  specificIndexTraining @28 :Bool;
  nextTrainingIndices @29 :List(Int32);
}
