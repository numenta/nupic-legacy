@0x99e493bfb8fbad94;

# Next ID: 31
struct KNNClassifierProto {
  verbosity @0 :UInt8;

  cellsPerCol @1 :UInt32;
  k @2 :UInt32;
  exact @3 :Bool;
  distanceNorm @4 :Float32;
  distanceMethod @5 :Text;
  distanceThreshold @6 :UInt32;
  doBinarization @7 :Bool;
  binarizationThreshold @8 :Float32;
  useSparseMemory @9 :Bool;
  sparseThreshold @10 :Float32;
  relativeThreshold @11 :Bool;
  numWinners @12 :UInt32;
  numSVDSamples @13 :Int32;
  numSVDDims @14 :Int32;
  fractionOfMax @15 :Float32;
  replaceDuplicates @16 :Bool;
  maxStoredPatterns @17 :Int32;

  iterationIdx @18 :Int32;

  numPatterns @19 :Int32;
  memory @20 :List(List(Float32));
  m @21 :List(List(Float32));
  categoryList @22 :List(UInt32);
  categoryRecencyList @23 :List(Int32);
  partitionIdList @24 :List(Int32);
  partitionIdArray @25 :List(Int32);

  s @26 :List(Float64);
  vt @27 :List(List(Float64));
  mean @28 :List(Float64);

  specificIndexTraining @29 :Bool;
  nextTrainingIndices @30 :List(Int32);
}
