import csv
import datetime

# Open the file to loop over each row
with open ("gymdata.csv") as fileIn:
  reader = csv.reader(fileIn)
  # The first three rows are not data, but we'll need the field names when
  # passing data into the model.
  headers = reader.next()
  reader.next()
  reader.next()

  for record in reader:
    # Create a dictionary with field names as keys, row values as values.
    modelInput = dict(zip(headers, record))
    # Convert string consumption to float value.
    modelInput["consumption"] = float(modelInput["consumption"])
    # Convert timestamp string to Python datetime.
    modelInput["timestamp"] = datetime.datetime.strptime(
      modelInput["timestamp"], "%m/%d/%y %H:%M"
    )
    # Push the data into the model and get back results.
    result = model.run(modelInput)
