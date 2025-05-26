"""
Four dictionaries:
    OT (Ordinary Time)
    LE (Lent)
    EA (Easter)
    MISC (Miscellaneous)

Array of verses

Verse Class:
    reading (Gen 3:9-15, 20)
    category (OLD, GOS, NEW, RES, NULL)
    weekdayYear (0 (for both), 1, 2)
    weekendYear (0 (for all), 1, 2, 3)
"""

#!/usr/bin/env python
import requests
import re
from bs4 import BeautifulSoup


class Verse:
    def __init__(self, reading, weekdayYear, weekendYear, category="NULL"):
        self.reading = reading
        self.weekdayYear = weekdayYear
        self.weekendYear = weekendYear
        self.category = category

    def setCategory(self, category):
        self.type = category

    def setWeekendYear(self, weekendYear):
        self.weekendYear = weekendYear

    def __repr__(self):
        return f"{{{self.reading}, {self.weekdayYear}, {self.weekendYear}, {self.category}}}"


def printDict(dict):
    for row in dict:
        print(f"{row:75} | {dict[row]}")


def replaceDayOfWeek(date):
    date = date.replace("Week ", "")
    date = date.replace(" Mon", "-1")
    date = date.replace(" Tues", "-2")
    date = date.replace(" Wed", "-3")
    date = date.replace(" Thurs", "-4")
    date = date.replace(" Fri", "-5")
    date = date.replace(" Sat", "-6")
    return date


def addVerseToDict(dict, date, reading):
    if not date in dict:
        dict[date] = [reading]
    else:
        dict[date].append(reading)


def addReading(dict, date, reading, misc=False):
    if not misc:
        # Fix one digit numbers
        if date[3] in ["-", " "]:
            date = date[:2] + "0" + date[2:]

        # Fix year note
        if "(Year C)" in date:
            date = date.replace(" (Year C)", "")
            reading.setWeekendYear(3)
        elif "(Year B)" in date:
            date = date.replace(" (Year B)", "")
            reading.setWeekendYear(2)
        elif "(Year A)" in date:
            date = date.replace(" (Year A)", "")
            reading.setWeekendYear(1)
        elif "(in Year A)" in date:
            date = date.replace(" (in Year A)", "")
            reading.setWeekendYear(1)

        # Fix resp. note
        if "(resp. - note 2)" in date:
            date = date.replace(" (resp. - note 2)", "")
            reading.setCategory("RES")

        # Fixes up Advent final week
        if "AD" in date and "Dec." in date:
            date = date.replace("Dec. ", "")

    addVerseToDict(dict, date, reading)


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

        # Determines type of reading
        category = ""
        match i:
            case 0:
                category = "OLD"
            case 1:
                category = "GOS"
            case 2:
                category = "NEW"
            case 3:
                category = "RESP"

        # Determines weekendYear
        weekendYear = 0
        if cols[2] in ["1", "2"]:
            weekendYear = int(cols[2])

        verse = Verse(cols[0], weekendYear, 0, category)

        if not date in [".", "Day", "Day or Feast"]:
            cols.pop(3)
            cols.pop(1)
            if "Ord. Time" in date:
                date = date.replace("Ord. Time ", "OT")
                date = replaceDayOfWeek(date)
                addReading(OT, date, verse)
            elif "Lent" in date:
                date = date.replace("Lent ", "LE")
                date = replaceDayOfWeek(date)
                addReading(LE, date, verse)
            elif "Easter" in date:
                date = date.replace("Easter ", "EA")
                date = replaceDayOfWeek(date)
                addReading(EA, date, verse)
            elif "Advent" in date:
                date = date.replace("Advent ", "AD")
                date = replaceDayOfWeek(date)
                addReading(AD, date, verse)
            else:
                addReading(MISC, date, verse, True)

OT = dict(sorted(OT.items()))
AD = dict(sorted(AD.items()))
EA = dict(sorted(EA.items()))
LE = dict(sorted(LE.items()))
MISC = dict(sorted(MISC.items()))

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
