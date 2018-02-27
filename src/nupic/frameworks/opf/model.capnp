@0xa2163632a7294a0d;

using import "/nupic/frameworks/opf/opf_utils.capnp".InferenceType;

# Next ID: 5
struct ModelProto {
  inferenceType @0 :InferenceType;
  numPredictions @1 :UInt32;
  learningEnabled @2 :Bool;
  inferenceEnabled @3 :Bool;
  inferenceArgs @4 :Text;
}
