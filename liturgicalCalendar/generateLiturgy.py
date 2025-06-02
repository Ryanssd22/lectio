"""
Generates Lectionary using year and lectionaryTemplate.json (Generated from readLectionary.py)
"""

import json
import sys
import datetime
from readCalendar import getCalendar

from readLectionary import Readings, getOrdinalNumber, getDayOfWeekString


def sundayCycleIntToChar(number):
    match number:
        case 1:
            sundayCycle = "A"
        case 2:
            sundayCycle = "B"
        case 3:
            sundayCycle = "C"
    return sundayCycle


with open("lectionaryTemplate.json", "r") as f:
    jsonLectionary = json.load(f)
    lectionary = {}
    for season in jsonLectionary:
        lectionary[season] = {
            date: Readings(
                reading["title"],
                reading["first"],
                reading["responsal"],
                reading["second"],
                reading["gospel"],
            )
            for date, reading in jsonLectionary[season].items()
        }


if len(sys.argv) < 2:
    year = datetime.datetime.now().year
else:
    year = int(sys.argv[1])

calendar = getCalendar(year)
"""
Calendar Data:

weekdayCycle
sundayCycle
holyFamily
epiphany
christmasEnd
ashWednesday
easter
pentecost
adventStart
weeksBeforeLent
pentecostStartOT
"""

# Sets each date's saeson (Christmas, Lent, Ordinary time, etc.)
currentDate = datetime.datetime(year, 1, 1)
liturgySeasons = {}
while currentDate < datetime.datetime(year + 1, 1, 1):
    if currentDate <= calendar.christmasEnd:
        season = "CHRISTMAS"
    elif currentDate < calendar.ashWednesday:
        season = "ORDINARY"
    elif currentDate < calendar.easter - datetime.timedelta(days=3):
        season = "LENT"
    elif currentDate <= calendar.pentecost:
        season = "EASTER"
    elif currentDate < calendar.adventStart:
        season = "ORDINARY"
    elif currentDate < datetime.datetime(year, 12, 25):
        season = "ADVENT"
    else:
        season = "CHRISTMAS"
    liturgySeasons[currentDate] = season
    currentDate += datetime.timedelta(days=1)

liturgy = {}

christmasLectionary = lectionary["CHRISTMAS"]
adventLectionary = lectionary["ADVENT"]
ordinaryLectionary = lectionary["ORDINARY"]
lentLectionary = lectionary["LENT"]
for date in liturgySeasons:
    dayOfTheWeek = date.isoweekday()
    # ####################
    # ||                ||
    # ||   CHRISTMAS    ||
    # ||                ||
    # ####################
    if liturgySeasons[date] == "CHRISTMAS":
        liturgy[date] = []
        match date.month:
            case 1:
                month = "Jan"
            case 12:
                month = "Dec"
        dateSearch = f"{month}{date.day}"

        if date == datetime.datetime(year, 12, 25):  # CHRISTMAS
            liturgy[date] = [
                christmasLectionary["CHRISTMAS-VIGIL"],
                christmasLectionary["CHRISTMAS-NIGHT"],
                christmasLectionary["CHRISTMAS-DAWN"],
                christmasLectionary["CHRISTMAS-DAY"],
            ]
        elif date == calendar.holyFamily:  # HOLY FAMILY
            nextSundayCycle = calendar.sundayCycle % 3 + 1
            keySearch = f"HOLYFAMILY-{sundayCycleIntToChar(nextSundayCycle)}"
            if nextSundayCycle == 1:
                liturgy[date] = [christmasLectionary[keySearch]]
            else:
                liturgy[date] = [
                    christmasLectionary["HOLYFAMILY-A"],
                    christmasLectionary[keySearch],
                ]
        elif dateSearch in christmasLectionary and (  # CHRISTMASDAYS
            date < calendar.epiphany or date > datetime.datetime(year, 12, 25)
        ):
            liturgy[date].append(christmasLectionary[dateSearch])
        elif date == calendar.christmasEnd:  # BAPTISM OF OUR LORD
            keySearch = f"BAPTISM-{sundayCycleIntToChar(calendar.sundayCycle)}"
            if calendar.sundayCycle == 1:
                liturgy[date].append(christmasLectionary["BAPTISM-A"])
            else:
                liturgy[date] = [
                    christmasLectionary["BAPTISM-A"],
                    christmasLectionary[keySearch],
                ]
        else:  # EPIPHANY
            if date == calendar.epiphany:
                liturgy[date].append(christmasLectionary["EPIPHANY"])
            else:
                daysFromEpiphany = (date - calendar.epiphany).days
                liturgy[date].append(
                    christmasLectionary[f"EPIPHANY-{daysFromEpiphany}"]
                )

    # ####################
    # ||                ||
    # ||     ADVENT     ||
    # ||                ||
    # ####################
    if liturgySeasons[date] == "ADVENT":
        weeksSinceStart = int((date - calendar.adventStart).days / 7 + 1)
        # Specific Dates
        if date.day >= 17 and date.day <= 24:
            keySearch = f"Dec{date.day}"
            title = f"{getOrdinalNumber(weeksSinceStart)} {getDayOfWeekString(dayOfTheWeek - 1)} of Advent"
            readings = adventLectionary[keySearch]
            readings.title = title[0].upper() + title[1:]
            liturgy[date] = [readings]

        # Sundays
        elif dayOfTheWeek == 7:
            keySearch = (
                f"{weeksSinceStart}-7-{sundayCycleIntToChar(calendar.sundayCycle)}"
            )
            liturgy[date] = [adventLectionary[keySearch]]

        # Weekdays
        else:
            keySearch = f"{weeksSinceStart}-{dayOfTheWeek}"
            liturgy[date] = [adventLectionary[keySearch]]

    # ####################
    # ||                ||
    # || ORDINARY TIME  ||
    # ||                ||
    # ####################
    if liturgySeasons[date] == "ORDINARY":
        if date < calendar.ashWednesday:
            weeksSinceStart = int((date - calendar.epiphany).days / 7)
        else:
            weeksSinceStart = int(
                (date - calendar.pentecost).days / 7 + calendar.pentecostStartOT
            )

        if weeksSinceStart < 10:
            weeksSinceStart = "0" + str(weeksSinceStart)

        if dayOfTheWeek == 7:
            keySearch = (
                f"{weeksSinceStart}-7-{sundayCycleIntToChar(calendar.sundayCycle)}"
            )
            readings = ordinaryLectionary[keySearch]
            title = f"{getOrdinalNumber(weeksSinceStart)} Sunday of Ordinary Time"
        else:
            keySearch = f"{weeksSinceStart}-{dayOfTheWeek}-{calendar.weekdayCycle}"
            readings = ordinaryLectionary[keySearch]

        liturgy[date] = [readings]

    # ####################
    # ||                ||
    # ||      LENT      ||
    # ||                ||
    # ####################
    if liturgySeasons[date] == "LENT":
        weeksSinceAsh = int((date - calendar.ashWednesday).days / 7)

        if dayOfTheWeek == 7:
            if weeksSinceAsh + 1 == 6:
                keySearch = f"6-7-{sundayCycleIntToChar(calendar.sundayCycle)}"
                liturgy[date] = [
                    lentLectionary[keySearch + "-MASS"],
                    lentLectionary[keySearch + "-PROC"],
                ]
            else:
                keySearch = f"{weeksSinceAsh + 1}-7-{sundayCycleIntToChar(calendar.sundayCycle)}"
                liturgy[date] = lentLectionary[keySearch]


for date in liturgy:
    if liturgySeasons[date] == "LENT":
        print(f"{date.strftime('%x')} - {liturgy[date]}")
