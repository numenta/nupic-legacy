from nupic.algorithms.spatial_pooler import SpatialPooler

encodingWidth = timeOfDayEncoder.getWidth() \
  + weekendEncoder.getWidth() \
  + scalarEncoder.getWidth()

sp = SpatialPooler(
  # How large the input encoding will be.
  inputDimensions=(encodingWidth),
  # How many mini-columns will be in the Spatial Pooler.
  columnDimensions=(2048),
  # What percent of the columns's receptive field is available for potential
  # synapses?
  potentialPct=0.85,
  # This means that the input space has no topology.
  globalInhibition=True,
  localAreaDensity=-1.0,
  # Roughly 2%, giving that there is only one inhibition area because we have
  # turned on globalInhibition (40 / 2048 = 0.0195)
  numActiveColumnsPerInhArea=40.0,
  # How quickly synapses grow and degrade.
  synPermInactiveDec=0.005,
  synPermActiveInc=0.04,
  synPermConnected=0.1,
  # boostStrength controls the strength of boosting. Boosting encourages
  # efficient usage of SP columns.
  boostStrength=3.0,
  # Random number generator seed.
  seed=1956,
  # Determines if inputs at the beginning and end of an input dimension should
  # be considered neighbors when mapping columns to inputs.
  wrapAround=False
)
