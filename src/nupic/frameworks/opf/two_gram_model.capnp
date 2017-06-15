@0xc938bfbf36a3bdc3;

using import "/nupic/frameworks/opf/opf_utils.capnp".InferenceType;
using import "/nupic/encoders/multi.capnp".MultiEncoderProto;

# Next ID: 7
struct TwoGramModelProto {
    inferenceType @0 :InferenceType;
    reset @1 :Bool;
    hashToValueDict @2 :List(HashMapping);
    learningEnabled @3 :Bool;
    encoder @4 :MultiEncoderProto;
    prevValues @5 :List(Int32);
    twoGramDicts @6 :List(List(TwoGramMapping));
}

struct HashMapping {
    hash @0 :Int32;
    value @1 :Float32;
}

struct TwoGramMapping {
    value @0 :Int32;
    buckets @1: List(BucketMapping);
}

struct BucketMapping {
    index @0: Int32;
    count @1: Int32;
}
