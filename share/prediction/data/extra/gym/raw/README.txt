Gym Dataset
-----------
The raw data comes in 3 CSV files of 2 kinds: attendance data and energy consumption data for Gyms in Australia for the months September 2010 and October 2010.

Attendance data is hourly data of gym attendance in the following format:

Bondi Platinum,,,,,,,,,,,,,,,,,,,
,,,,,,,,,,,,,,,,,,,
Date Of Swipe, < 6 am,6-7 am,7-8 am,8-9 am,9-10 am,10-11 am,11-12 am,12-1 pm,1-2 pm,2-3 pm,3-4 pm,4-5 pm,5-6 pm,6-7 pm,7-8 pm,8-9 pm,9-10 pm,> 10 pm,Totals
1-Sep-10,73,179,83,147,145,90,55,62,34,45,72,102,130,182,91,23,4,0,1517

The header contains the Gym name and hourly segement. Each data record (line) contain the date and the attendance at each hour (before 6AM and after 10PM are aggregated) for an entire day. There are multiple clubs (each with its own header) in the files. The attendance data comes in two monthly files: Attendance_Clubs_Sep.csv and Attendance_Clubs_Oct.csv


The consumption data is in 15 minutes intervals and comes in a single file: all_group1_clubs_detail.csv:

"   ","SITE_LOCATION_NAME","TIMESTAMP","TOTAL_KWH"
"4","Bondi Platinum","1/09/2010 12:45:00 AM","14.39"
"5","Bondi Platinum","1/09/2010 1:00:00 AM","13.92"
"6","Bondi Platinum","1/09/2010 1:15:00 AM","14.71"
"7","Bondi Platinum","1/09/2010 1:30:00 AM","15.01"

There is a single header line for the entire file. Each line contains the Gym name, date and usually time and the energy consumption for a 15 minutes period.

Issues
------
- Consumption data is 24 hours (in 15 minutes intervals) but attendance data is only 6AM through 10PM and then there are two numbers for "< 6a" and "> 10PM". To simplify I assume that <6AM means 5-6 and <5 is always 0. Also >10PM is 10-11 and >11PM is always 0. To match the consumption to attendance data the merged file will be in 1 hour resolution. The 4 consumption readings in an hour will be summed or averaged over one hour. If the data is total KW in each 15 minutes it will be summed, but if it is in KWH (as the title says) then it will be averaged.

- There is significant consumption data when attendance is 0 (upto 80% of max consumption and sometimes more than at times when attendance > 0). That points out that attendance is not the only variable that impacts consumption. For example, it's possbile that some equipment is automatically started in the morning before people arrive and the startup process consumes a lot of energy.

- Gym name inconsistencies. In attendance files: "Melbourne Central". In consumption file: "Melbourne CBD - Melbourne Central". I assume it's the same gym using my human deduction skills. Same thing with "North Sydney" vs. "North Sydney - Elizabeth Plaza". 

- North Sydney is a big trouble maker it is missing attendance data for Sep-4 and Sep-5. Other clubs miss attendance data too. The script prints out missing data.

- Inconsistent attendance file format. Sometimes one empty line and sometimes two empty lines between club data.

- Inconsistent consumption file format. The first record in each day doesn't include the time (not a problem, it's 12AM of course). 


- The consumption data has double quotes around every field (gets in the way of direct comparison)

- Different date formats (dd-mmm-yy vs. dd/mm/yyyy). Again prevents direct comparison and requires conversion of one of them.
Script

- Consumption date file is a Unicode file and has a BOM at the beginning. Brrr...

- The attendance data containes totals (not needed)

- The consumption data contains line numbers (not needed)

- \r EOL characters (old Mac format)

Script
------
I assume that we will get more data files in the same format so I fixed all the issues in the script and not manually (e.g. replacing \r with \n in an editor or manually removing redundant empty lines).

The gym name fixes are especially annoying since they are hard-coded.