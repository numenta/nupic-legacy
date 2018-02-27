@0xd57f978f3e5edfcf;

# Next ID: 7
enum InferenceType {
    temporalNextStep @0;
    temporalClassification @1;
    nontemporalClassification @2;
    temporalAnomaly @3;
    nontemporalAnomaly @4;
    temporalMultiStep @5;
    nontemporalMultiStep @6;
}
