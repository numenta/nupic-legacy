@0x8602f38429407eb0;

struct AnomalyLikelihoodProto {
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
    mean @1 :Float64;
    variance @2 :Float64;
    stdev @3 :Float64;
    movingAverage @4 :MovingAverage;
    historicalLikelihoods @5 :List(Float64);

    struct MovingAverage {
      windowSize @0 :UInt64;
      historicalValues @1 :List(Float64);
      total @2 :Float64;
    }
  }
}
