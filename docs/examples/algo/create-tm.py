from nupic.algorithms.temporal_memory import TemporalMemory

tm = TemporalMemory(
  # Must be the same dimensions as the SP
  columnDimensions=(2048, ),
  # How many cells in each mini-column.
  cellsPerColumn=32,
  # A segment is active if it has >= activationThreshold connected synapses
  # that are active due to infActiveState
  activationThreshold=16,
  initialPermanence=0.21,
  connectedPermanence=0.5,
  # Minimum number of active synapses for a segment to be considered during
  # search for the best-matching segments.
  minThreshold=12,
  # The max number of synapses added to a segment during learning
  maxNewSynapseCount=20,
  permanenceIncrement=0.1,
  permanenceDecrement=0.1,
  predictedSegmentDecrement=0.0,
  maxSegmentsPerCell=128,
  maxSynapsesPerSegment=32,
  seed=1960
)
