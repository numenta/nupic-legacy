@0x9ac6bf9fef7ba20d;

using import "/nupic/proto/SparseMatrixProto.capnp".SparseMatrixProto;

# Next ID: 31
struct KNNClassifierProto {
    # Public fields
    version @0 :Int32;
    k @1 :Int32;
    exact @2 :Bool;
    distanceNorm @3 :Float32;
    distanceMethod @4 :Text;
    distThreshold @5 :Float32;
    doBinarization @6 :Bool;
    binarizationThreshold @7 :Float32;
    useSparseMemory @8 :Bool;
    sparseThreshold @9 :Float32;
    relativeThreshold @10 :Bool;
    numWinners @11 :Int32;
    numSVDSamples @12 :Int32;
    numSVDDims @13 :Text;
    fractionOfMax @14 :Float32;
    verbosity @15 :Int8;
    maxStoredPatterns @16 :Int32;
    replaceDuplicates @17 :Bool;
    cellsPerCol @18 :Int32;
    minSparsity @19 :Float32;

    # Private State
    memory :union  {
        ndarray @20 :List(List(Float64));
        # NearestNeighbor inherits from SparseMatrix and shares the same schema
        nearestNeighbor @30 :SparseMatrixProto;
    }
    numPatterns @21 :Int32;
    m @22 :List(List(Float64));
    categoryList @23 :List(Int32);
    partitionIdList @24 :List(Float32);
    finishedLearning @25 :Bool;
    iterationIdx @26 :Int32;

    # Used by PCA
    s @27 :List(Float32);
    vt @28 :List(List(Float32));
    mean @29 :List(Float32);
}

