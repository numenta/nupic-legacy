# Make sure all objects are initialized.
network.initialize()

N = 1  # Run the network, N iterations at a time.
for iteration in range(0, numRecords, N):
  network.run(N)
