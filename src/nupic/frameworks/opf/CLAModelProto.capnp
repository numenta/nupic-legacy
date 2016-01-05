@0xabf2792aa23483be;

using import "/nupic/proto/NetworkProto.capnp".NetworkProto;

# Next ID: 2
struct CLAModelProto {
  inferenceType @0 :InferenceType;
  numRunCalls @1 :UInt32;
  network @2 :NetworkProto;

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
