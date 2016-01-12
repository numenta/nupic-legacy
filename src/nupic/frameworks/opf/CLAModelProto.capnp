@0xabf2792aa23483be;

using import "/nupic/proto/NetworkProto.capnp".NetworkProto;

# Next ID: 5
struct CLAModelProto {
  inferenceType @0 :InferenceType;
  numRunCalls @1 :UInt32;
  minLikelihoodThreshold @2 :Float32;
  maxPredictionsPerStep @3 :UInt32;
  network @4 :NetworkProto;

  enum InferenceType {
    temporalNextStep @0;
    temporalClassification @1;
    nontemporalClassification @2;
    temporalAnomaly @3;
    nontemporalAnomaly @4;
    temporalMultiStep @5;
    nontemporalMultiStep @6;
  }
}
