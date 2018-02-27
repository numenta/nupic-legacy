@0xff2c4ed09fa84975;

using import "/nupic/proto/RandomProto.capnp".RandomProto;

struct SegmentProto {
  # Segment.tm must be set after constructing Segment from serialization

  segID @0 :UInt32;
  isSequenceSeg @1 :Bool;
  lastActiveIteration @2 :UInt32;
  positiveActivations @3 :UInt32;
  totalActivations @4 :UInt32;
  lastPosDutyCycle @5 :Float64;
  lastPosDutyCycleIteration @6 :UInt32;

  struct SegmentSynapse {
    srcCellCol @0 :UInt32;
    srcCellIdx @1 :UInt32;
    permanence @2 :Float32;
  }
  synapses @7 :List(SegmentSynapse);
}

struct SegmentUpdateProto {
  columnIdx @0 :UInt32;
  cellIdx @1 :UInt32;
  lrnIterationIdx @2 :UInt32;
  segment @3 :SegmentProto;
  activeSynapses @4 :List(UInt32);
  sequenceSegment @5 :Bool;
  phase1Flag @6 :Bool;
  weaklyPredicting @7 :Bool;
}

struct BacktrackingTMProto {
  version @0 :UInt16;
  random @1 :RandomProto;
  numberOfCols @2 :UInt32;
  cellsPerColumn @3 :UInt32;
  #numberOfCells
  initialPerm @4 :Float32;
  connectedPerm @5 :Float32;
  minThreshold @6 :UInt32;
  newSynapseCount @7 :UInt32;
  permanenceInc @8 :Float32;
  permanenceDec @9 :Float32;
  permanenceMax @10 :Float32;
  globalDecay @11 :Float32;
  activationThreshold @12 :UInt32;
  doPooling @13 :Bool;
  segUpdateValidDuration @14 :UInt32;
  burnIn @15 :UInt32;
  collectStats @16 :Bool;
  verbosity @17 :UInt8;
  pamLength @18 :UInt32;
  maxAge @19 :UInt32;
  maxInfBacktrack @20 :UInt32;
  maxLrnBacktrack @21 :UInt32;
  maxSeqLength @22 :UInt32;
  maxSegmentsPerCell @23 :Int64;
  maxSynapsesPerSegment @24 :Int64;
  outputType @25 :Text;

  activeColumns @26 :List(UInt32);

  # First list indexed by column, inner list indexed by cell in the column
  cells @27 :List(List(List(SegmentProto)));

  lrnIterationIdx @28 :UInt32;
  iterationIdx @29 :UInt32;
  segID @30 :UInt32;
  currentOutput @31 :List(List(Bool));

  pamCounter @32 :UInt32;
  collectSequenceStats @33 :Bool;
  resetCalled @34 :Bool;
  avgInputDensity @35 :Float64;
  learnedSeqLength @36 :UInt32;
  avgLearnedSeqLength @37 :Float64;

  # List of past inputs, where each input is a list of active indices
  prevLrnPatterns @38 :List(List(UInt32));
  prevInfPatterns @39 :List(List(UInt32));

  struct SegmentUpdateWrapperProto {
    lrnIterationIdx @0 :UInt32;
    segmentUpdate @1 :SegmentUpdateProto;
  }
  struct CellSegmentUpdatesProto {
    columnIdx @0 :UInt32;
    cellIdx @1 :UInt32;
    segmentUpdates @2 :List(SegmentUpdateWrapperProto);
  }
  segmentUpdates @40 :List(CellSegmentUpdatesProto);

  cellConfidenceT @41 :List(List(Float32));
  cellConfidenceT1 @42 :List(List(Float32));
  cellConfidenceCandidate @43 :List(List(Float32));

  colConfidenceT @44 :List(Float32);
  colConfidenceT1 @45 :List(Float32);
  colConfidenceCandidate @46 :List(Float32);

  lrnActiveStateT @47 :List(List(Int8));
  lrnActiveStateT1 @48 :List(List(Int8));

  infActiveStateT @49 :List(List(Int8));
  infActiveStateT1 @50 :List(List(Int8));
  infActiveStateBackup @51 :List(List(Int8));
  infActiveStateCandidate @52 :List(List(Int8));

  lrnPredictedStateT @53 :List(List(Int8));
  lrnPredictedStateT1 @54 :List(List(Int8));

  infPredictedStateT @55 :List(List(Int8));
  infPredictedStateT1 @56 :List(List(Int8));
  infPredictedStateBackup @57 :List(List(Int8));
  infPredictedStateCandidate @58 :List(List(Int8));

  # From mixin class
  consolePrinterVerbosity @59 :UInt8;
}
