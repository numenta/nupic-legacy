predictedIdx = dataSource.getFieldNames().index("consumption")

network.regions["sensor"].setParameter("predictedFieldIdx", predictedIdx)