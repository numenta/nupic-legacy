@0x8602f38429407eb0;

struct AnomalyLikelihoodRegionProto {
  iteration @0 :UInt64;
  historicalScores @1 :List(Score);
  distribution @2 :Distribution;
  probationaryPeriod @3 :UInt32;
  learningPeriod @4 :UInt32;
  reestimationPeriod @5 :UInt32;
  historicWindowSize @6 :UInt32;

  struct Score {
    value @0 :Float64;
    anomalyScore @1 :Float64;
  }

  struct Distribution {
    name @0 :Text;
    mean @1 :Float32;
    variance @2 :Float32;
    stdev @3 :Float32;
    movingAverage @4 :MovingAverage;
    historicalLikelihoods @5 :List(Float32);

    struct MovingAverage {
      windowSize @0 :UInt64;
      historicalValues @1 :List(Float32);
      total @2 :Float32;
    }
  }
}
