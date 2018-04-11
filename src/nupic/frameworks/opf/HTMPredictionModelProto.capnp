@0xabf2792aa23483be;

using import "/nupic/proto/NetworkProto.capnp".NetworkProto;
using import "/nupic/frameworks/opf/model.capnp".ModelProto;
using import "/nupic/frameworks/opf/opf_utils.capnp".InferenceType;

# Next ID: 15
struct HTMPredictionModelProto {
  modelBase @0 :ModelProto;
  numRunCalls @1 :UInt32;
  minLikelihoodThreshold @2 :Float32;
  maxPredictionsPerStep @3 :UInt32;
  network @4 :NetworkProto;
  spLearningEnabled @5 :Bool;
  tpLearningEnabled @6 :Bool;
  predictedFieldIdx :union {
    none @12 :Void;
    value @7 :UInt32;
  }
  predictedFieldName :union {
    none @13 :Void;
    value @8 :Text;
  }
  trainSPNetOnlyIfRequested @9: Bool;
  finishedLearning @10: Bool;
  numFields :union {
    none @14 :Void;
    value @11 :UInt32;
  }
}
