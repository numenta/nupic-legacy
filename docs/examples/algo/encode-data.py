with open (_INPUT_FILE_PATH) as fin:
  reader = csv.reader(fin)
  for count, record in enumerate(reader):
    # Convert data string into Python date object.
    dateString = datetime.datetime.strptime(record[0], "%m/%d/%y %H:%M")
    # Convert data value string into float.
    consumption = float(record[1])

    # To encode, we need to provide zero-filled numpy arrays for the encoders
    # to populate.
    timeOfDayBits = numpy.zeros(timeOfDayEncoder.getWidth())
    weekendBits = numpy.zeros(weekendEncoder.getWidth())
    consumptionBits = numpy.zeros(scalarEncoder.getWidth())

    # Now we call the encoders create bit representations for each value.
    timeOfDayEncoder.encodeIntoArray(dateString, timeOfDayBits)
    weekendEncoder.encodeIntoArray(dateString, weekendBits)
    scalarEncoder.encodeIntoArray(consumption, consumptionBits)

    # Concatenate all these encodings into one large encoding for Spatial
    # Pooling.
    encoding = numpy.concatenate(
      [timeOfDayBits, weekendBits, consumptionBits]
    )

    # Print complete encoding to the console as a binary representation.
    print encoding.astype('int16')
