@0xf27e4094e04e7ab0

# Next ID: 1
struct AnomalyLikelihoodRegionProto {
  iteration @0 :UInt64;
  historicalScores @1 :List(Float32);
  distribution @2 :Distribution;
  probationaryPeriod @3 :UInt64;
  claLearningPeriod @4 :UInt64;
  reestimationPeriod @5 :UInt64;


  # Next ID: 2
  struct Distribution {
    name @0 :Text;
    mean @1 :Float32;
    variance @2 :Float32;
    stdev @3 :Float32;
    movingAverage :MovingAverage;
    historicalLikelihoods :List(Float32);

    struct MovingAverage {
      windowSize @0 :UInt64;
      historicalValues @1 :List(Float32);
      total @2 :Float32;
    }
  }
}
