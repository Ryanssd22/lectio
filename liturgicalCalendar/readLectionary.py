#!/usr/bin/env python

import requests
import re
from bs4 import BeautifulSoup


def printDict(dict):
    for row in dict:
        print(f"{row:75} | {dict[row]}")

def addReading(dict, date, reading):
    if not date in dict:
        dict[date] = [reading]
    else:
        dict[date].append(reading)

    if "(resp. - note 2)" in date:
        dict.pop(date)
        date = date.replace(" (resp. - note 2)", "")
        reading.append("RESP")
        if not date in dict:
            dict[date] = [reading]
        else:
            dict[date].append(reading)

weekdayPage = requests.get(
    "https://catholic-resources.org/Lectionary/Index-Weekdays.htm"
)
weekdaySoup = BeautifulSoup(weekdayPage.text, "html.parser")
tables = weekdaySoup.find_all("table")
tableData = {}

OT = {}
LE = {}
EA = {}
AD = {}
MISC = {}
# TODO: Fix up key names
# TODO: Figure out a way to organize gospel, reading, and response somehow
# TODO: Sort dictionary
# TODO: Separate specific dates into their own dictionary

for i, table in enumerate(tables):
    rows = table.find_all("tr")
    for row in rows:
        cols = row.find_all("td")
        cols = [col.text.strip() for col in cols]

        # cols[0] = Reading
        # cols[1] = Day/Feast
        # cols[2] = Year
        # cols[3] = Lec#

        date = cols[1]
        date = date.replace(",", "")
        date = date.replace("Ord. Time ", "OT")
        date = date.replace("Lent ", "LE")
        date = date.replace("Advent ", "AD")
        date = date.replace("Easter ", "EA")
        date = date.replace("Week ", "")
        date = date.replace(" Mon", "-1")
        date = date.replace(" Tues", "-2")
        date = date.replace(" Wed", "-3")
        date = date.replace(" Thurs", "-4")
        date = date.replace(" Fri", "-5")
        date = date.replace(" Sat", "-6")

        if any(word in date for word in ["OT", "LE", "AD", "EA"]) and date[3] in ["-", " "]:
            date = date[:2] + "0" + date[2:]

        if not date in [".", "Day", "Day or Feast"]:
            cols.pop(3)
            cols.pop(1)
            if "OT" in date:
                addReading(OT, date, cols)
            if "LE" in date:
                addReading(LE, date, cols)
            if "EA" in date:
                addReading(EA, date, cols)
            if "AD" in date:
                addReading(AD, date, cols)


OT = dict(sorted(OT.items()))
AD = dict(sorted(AD.items()))
EA = dict(sorted(EA.items()))
LE = dict(sorted(LE.items()))


print("ADVENT:")
printDict(AD)
print("ORDINARY TIME:")
printDict(OT)
print("LENT:")
printDict(LE)
print("EASTER:")
printDict(EA)
print("MISCELLANEOUS:")
printDict(MISC)
# printDict(OT)
