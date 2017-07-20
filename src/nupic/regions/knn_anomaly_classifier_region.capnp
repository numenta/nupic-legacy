@0xc8ac55fe2407eceb;

using import "/nupic/regions/knn_classifier_region.capnp".KNNClassifierRegionProto;

# Next ID: 5
struct ClassificationRecord {
    rowid @0 :Int32;
    anomalyScore @1 :Float32;
    anomalyVector @2 :List(Int32);
    anomalyLabel @3 :List(Text);
    setByUser @4 :Bool;
}

# Net ID: 16
struct KNNAnomalyClassifierRegionProto {
    version @0 :Int32;
    maxLabelOutputs @1 :Int32;
    activeColumnCount @2 :Int32;
    prevPredictedColumns @3 :List(Int32);
    anomalyVectorLength @4 :Int32;
    classificationMaxDist @5 :Float32;
    iteration @6 :Int32;
    trainRecords @7 :Int32;
    anomalyThreshold @8 :Float32;
    cacheSize @9 :Int32;
    classificationVectorType @10 :Int32;
    knnclassifierArgs @11 :KNNClassifierArgsProto;
    knnclassifier @12 :KNNClassifierRegionProto;
    labelResults @13 :List(Text);
    savedCategories @14 :List(Text);
    recordsCache @15 :List(ClassificationRecord);
}

# Next ID: 26
struct KNNClassifierArgsProto {
    maxCategoryCount @0 :Int32;
    bestPrototypeIndexCount @1 :Int32;
    outputProbabilitiesByDist @2 :Bool;
    k @3 :Int32;
    distanceNorm @4 :Float32;
    distanceMethod @5 :Text;
    distThreshold @6 :Float32;
    doBinarization @7 :Bool;
    inputThresh @8 :Float32;
    useSparseMemory @9 :Bool;
    sparseThreshold @10 :Float32;
    relativeThreshold @11: Bool;
    winnerCount @12 :Int32;
    acceptanceProbability @13 :Float32;
    seed @14 :Int32;
    doSphering @15 :Bool;
    svdSampleCount @16 :Int32;
    svdDimCount @17 :Int32;
    fractionOfMax @18 :Int32;
    useAuxiliary @19 :Int32;
    justUseAuxiliary @20 :Int32;
    verbosity @21 :Int32;
    replaceDuplicates @22 :Bool;
    cellsPerCol @23 :Int32;
    maxStoredPatterns @24 :Int32;
    minSparsity @25 :Float32;
}

