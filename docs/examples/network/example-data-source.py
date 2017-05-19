from nupic.data.file_record_stream import FileRecordStream

_INPUT_FILE_PATH = "/path/to/your/data.csv"
dataSource = FileRecordStream(streamID=_INPUT_FILE_PATH)

# Add the data source to the sensor region.
sensorRegion = network.regions["sensor"].getSelf()
sensorRegion.dataSource = dataSource