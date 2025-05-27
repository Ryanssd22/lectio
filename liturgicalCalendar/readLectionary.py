"""
Four dictionaries:
    OT (Ordinary Time)
    LE (Lent)
    EA (Easter)
    MISC (Miscellaneous)

Array of verses

Verse Class:
    reading (Gen 3:9-15, 20)
    category (FIR, SEC, GOS, RES, ALL, NULL)
"""

#!/usr/bin/env python
import requests
import re
from bs4 import BeautifulSoup


class Verse:
    def __init__(self, reading, category="NULL"):
        self.reading = reading
        self.category = category

    def setCategory(self, category):
        self.type = category

    def __repr__(self):
        return f"{{{self.reading}, {self.category}}}"


def printDict(dict):
    for row in dict:
        print(f"{row:75} | {dict[row]}")


def getDayOfWeek(date):
    day = "0"
    if "Mon" in date:
        day = "1"
    elif "Tues" in date:
        day = "2"
    elif "Wed" in date:
        day = "3"
    elif "Thurs" in date:
        day = "4"
    elif "Fri" in date:
        day = "5"
    elif "Sat" in date:
        day = "6"
    return day


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


def getTables(link):
    site = requests.get(link)
    soup = BeautifulSoup(site.text, "html.parser")
    tables = soup.find_all("table")
    return tables


def getRows(table):
    parsedRows = []
    rows = table.find_all("tr")
    for row in rows:
        cols = row.find_all("td")
        cols = [col.text.strip() for col in cols]
        parsedRows.append(cols)
    return parsedRows


# Links from cathoilic-resources.org/Lectionary
adventSunday = "https://catholic-resources.org/Lectionary/1998USL-Advent.htm"
adventWeekday = (
    "https://catholic-resources.org/Lectionary/2002USL-Weekdays-AdventChristmas.htm"
)

OT = {}
LE = {}
EA = {}
AD = {}
CH = {}
MISC = {}

# Advent Sunday
adventSundayTable = getTables(adventSunday)
adventSundayRows = getRows(adventSundayTable[0])
adventSundayRows.pop(0)
for row in adventSundayRows:
    date = row[2]
    cycle = date[-1]
    first = Verse(row[3], "FIR")
    resp = Verse(row[4], "RES")
    second = Verse(row[5], "SEC")
    gospel = Verse(row[7], "GOS")

    key = "0" + date[0] + "-7" + cycle
    AD[key] = [first, resp, second, gospel]

# Advent Weekday
adventWeekdayTable = getTables(adventWeekday)
adventWeekdayRows = getRows(adventWeekdayTable[0])
adventWeekdayRows.pop(18)
adventWeekdayRows.pop(0)
for row in adventWeekdayRows:
    date = row[2]
    first = Verse(row[3], "FIR")
    resp = Verse(row[4], "RES")
    gospel = Verse(row[6], "GOS")

    key = ""
    if "December" in date:
        key = "Dec" + date[9:11]
    else:
        day = getDayOfWeek(date)
        key = "0" + date[0] + "-" + day

    AD[key] = [first, resp, gospel]


# for i, table in enumerate(tables):
#     rows = table.find_all("tr")
#     for row in rows:
#         cols = row.find_all("td")
#         cols = [col.text.strip() for col in cols]
#
#         # cols[0] = Reading
#         # cols[1] = Day/Feast
#         # cols[2] = Year
#         # cols[3] = Lec#
#
#         date = cols[1]
#         date = date.replace(",", "")
#
#         # Determines type of reading
#         category = ""
#         match i:
#             case 0:
#                 category = "OLD"
#             case 1:
#                 category = "GOS"
#             case 2:
#                 category = "NEW"
#             case 3:
#                 category = "RESP"
#
#         # Determines weekendYear
#         weekendYear = 0
#         if cols[2] in ["1", "2"]:
#             weekendYear = int(cols[2])
#
#         verse = Verse(cols[0], weekendYear, 0, category)
#
#         if not date in [".", "Day", "Day or Feast"]:
#             cols.pop(3)
#             cols.pop(1)
#             if "Ord. Time" in date:
#                 date = date.replace("Ord. Time ", "OT")
#                 date = replaceDayOfWeek(date)
#                 addReading(OT, date, verse)
#             elif "Lent" in date:
#                 date = date.replace("Lent ", "LE")
#                 date = replaceDayOfWeek(date)
#                 addReading(LE, date, verse)
#             elif "Easter" in date:
#                 date = date.replace("Easter ", "EA")
#                 date = replaceDayOfWeek(date)
#                 addReading(EA, date, verse)
#             elif "Advent" in date:
#                 date = date.replace("Advent ", "AD")
#                 date = replaceDayOfWeek(date)
#                 addReading(AD, date, verse)
#             else:
#                 addReading(MISC, date, verse, True)
#
# OT = dict(sorted(OT.items()))
# AD = dict(sorted(AD.items()))
# EA = dict(sorted(EA.items()))
# LE = dict(sorted(LE.items()))
# MISC = dict(sorted(MISC.items()))
#
print("ADVENT:")
printDict(AD)
print("\n")
print("CHRISTMAS:")
printDict(CH)
print("\n")
print("ORDINARY TIME:")
printDict(OT)
print("\n")
print("LENT:")
printDict(LE)
print("\n")
print("EASTER:")
printDict(EA)
print("\n")
print("MISCELLANEOUS:")
printDict(MISC)
