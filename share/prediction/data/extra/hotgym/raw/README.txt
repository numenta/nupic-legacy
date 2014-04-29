HotGym Dataset (gyms in Sidney, Australia)
------------------------------------------
The raw data comes in 4 CSV files:

1. gym_input.csv

Has information about 5 gyms for the period 2-jul-2010 through 31-dec-2010

Has the following header line:

"   ","SITE_LOCATION_NAME","TIMESTAMP","TOTAL_KWH"

Every record has the following fields:

 - running count (ignored)
 - gym name
 - timestamp (date and time in 15 minutes intervals)
 - consumption (in KWH units)
  
Here is a sample record from the file:

"17708","Lane Cove","3/07/2010 10:45:00 AM","18.9"

The file also has the following header line:

2. min_temps.csv

A very simple file that contains the minimum temperature in a certain day.

Has the following header line:

"   ","TIME_ID","MIN"

Every record has the following fields:

 - running count (ignored)
 - date
 - temperature (Celcius)

Here is a sample record from the file:

"8","13/07/2010","11"

3. max_temps.csv

Same as min_temps.csv except that it contains the maximum temperature.

The header is:

"   ","TIME_ID","MAX"

Sample record:

"8","13/07/2010","18"

4. club_hours.csv

This is a file that contains some general and aggregated data about each gym.
It is ignored at the moment. Here is the entire file for your enjoyment:

"   ","GYM","SQM","NATURAL_LIGHTING","CBUS","HOURS_OF_USE","KWHM2_BENCHMARK","KWHM2HR_BENCHMARK"
"1","Lane Cove","1891","Y","Y","95","140","1.47379498455287"
"2","Balgowlah Platinum","1166","Y","N","97.5","279","2.86646611250385"
"3","North Sydney - Walker St","1844","Y","N","95.5","311","3.26406065802773"
"4","Randwick","2270","Y","N","100.5","347","3.45732916913231"
"5","Mosman","2700","Y","N","100","486","4.86540955555556"

---------------------
makeDataset.py script
---------------------
The makeDataset.py script merges the information from numenta_air_cov.csv,
min_temps.csv and max_temps.csv. It generates a StandardFile that contains
for each record:

gym name, timestamp, consumption, min temperature, max temperature.

All the records from the same day will have the same min and max temperature.
Many records (24,960 out of 87840) don't have min and max temperature. At the
moment I put (min: 0, max: 40) for these records. Later we can extract the min/max
temperatures from some weather database.

The min/max files are synchronized (if there is a min temperature for certain
day then there is always also a max temperature for the same day)
