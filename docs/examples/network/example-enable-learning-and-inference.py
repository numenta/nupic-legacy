# Enable learning for all regions.
network.regions["SP"].setParameter("learningMode", 1)
network.regions["TM"].setParameter("learningMode", 1)
network.regions["classifier"].setParameter("learningMode", 1)

# Enable inference for all regions.
network.regions["SP"].setParameter("inferenceMode", 1)
network.regions["TM"].setParameter("inferenceMode", 1)
network.regions["classifier"].setParameter("inferenceMode", 1)
