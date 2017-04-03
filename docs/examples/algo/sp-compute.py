# Create an array to represent active columns, all initially zero. This
# will be populated by the compute method below. It must have the same
# dimensions as the Spatial Pooler.
activeColumns = numpy.zeros(2048)

# Execute Spatial Pooling algorithm over input space.
sp.compute(encoding, True, activeColumns)
activeColumnIndices = numpy.nonzero(activeColumns)[0]

print activeColumnIndices
