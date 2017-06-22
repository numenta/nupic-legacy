@0xf6c2ce76663e3361;

using import "/nupic/algorithms/knn_classifier.capnp".KNNClassifierProto;
using import "/nupic/proto/RandomProto.capnp".RandomProto;

# Next ID: 27
struct KNNClassifierRegionProto {
    version @0 :Int32;
    knnParams @1 :KNNClassifierParamsProto;
    knn @2 :KNNClassifierProto;
    rgen @3 :RandomProto;
    verbosity @4 :Int32;
    firstComputeCall @5 :Bool;
    keepAllDistances @6 :Bool;
    learningMode @7 :Bool;
    inferenceMode @8 :Bool;
    doSphering @9 :Bool;
    outputProbabilitiesByDist @10 :Bool;
    epoch @11 :UInt32;
    maxStoredPatterns @12 :Int32;
    maxCategoryCount @13 :Int32;
    bestPrototypeIndexCount @14 :Int32;
    acceptanceProbability @15 :Float32;
    useAuxiliary @16 :Bool;
    justUseAuxiliary @17 :Bool;
    protoScoreCount @18 :Int32;
    confusion @19 :List(List(Int32));
    normOffset @20 :List(Float32);
    normScale @21 :List(Float32);
    samples @22 :List(List(Float32));
    labels @23 :List(Int32);
    partitions @24 :List(Int32);
    protoScores @25 :List(Float32);
    categoryDistances @26:List(Float32);
}

# Next ID: 18
struct KNNClassifierParamsProto {
    k @0 :Int32;
    distanceNorm @1 :Float32;
    distanceMethod @2 :Text;
    distThreshold @3 :Float32;
    doBinarization @4 :Bool;
    binarizationThreshold @5 :Float32;
    useSparseMemory @6 :Bool;
    sparseThreshold @7 :Float32;
    relativeThreshold @8 :Bool;
    numWinners @9 :Int32;
    numSVDSamples @10 :Int32;
    numSVDDims @11 :Int32;
    fractionOfMax @12 :Float32;
    verbosity @13 :Int8;
    replaceDuplicates @14 :Bool;
    cellsPerCol @15 :Int32;
    maxStoredPatterns @16 :Int32;
    minSparsity @17 :Float32;
}
