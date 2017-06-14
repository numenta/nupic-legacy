@0xabf2792aa23483be;

using import "/nupic/proto/NetworkProto.capnp".NetworkProto;
using import "/nupic/frameworks/opf/opf_utils.capnp".InferenceType;

# Next ID: 5
struct HTMPredictionModelProto {
  inferenceType @0 :InferenceType;
  numRunCalls @1 :UInt32;
  minLikelihoodThreshold @2 :Float32;
  maxPredictionsPerStep @3 :UInt32;
  network @4 :NetworkProto;
}
