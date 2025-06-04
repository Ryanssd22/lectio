"""
Generates Lectionary using year and lectionaryTemplate.json (Generated from readLectionary.py)
"""

import json
import sys
import datetime
import os
from readCalendar import getCalendar, getNextSunday

from readLectionary import (
    Readings,
    getOrdinalNumber,
    getDayOfWeekString,
    lectionaryDateToDate,
)


def sundayCycleIntToChar(number):
    match number:
        case 1:
            sundayCycle = "A"
        case 2:
            sundayCycle = "B"
        case 3:
            sundayCycle = "C"
    return sundayCycle


def getPrevSaturday(date, delta=1):
    for i in range(delta):
        date += datetime.timedelta(days=-1)
        while date.strftime("%a") != "Sat":
            date += datetime.timedelta(days=-1)
    return date


def getNextThursday(date, delta=1):
    for i in range(delta):
        date += datetime.timedelta(days=1)
        while date.strftime("%a") != "Thu":
            date += datetime.timedelta(days=1)
    return date


def dateToLectionaryDate(date):
    months = {
        1: "Jan",
        2: "Feb",
        3: "Mar",
        4: "Apr",
        5: "May",
        6: "Jun",
        7: "Jul",
        8: "Aug",
        9: "Sep",
        10: "Oct",
        11: "Nov",
        12: "Dec",
    }
    return f"{months[date.month]}{date.day}"


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
                reading["rank"],
            )
            for date, reading in jsonLectionary[season].items()
        }


if len(sys.argv) < 2:
    year = datetime.datetime.now().year
else:
    year = int(sys.argv[1])

calendar = getCalendar(year)
sundayCycleChar = sundayCycleIntToChar(calendar.sundayCycle)
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
    elif currentDate < calendar.easter - datetime.timedelta(days=2):
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
easterLectionary = lectionary["EASTER"]
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
            keySearch = f"BAPTISM-{sundayCycleChar}"
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
    elif liturgySeasons[date] == "ADVENT":
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
            keySearch = f"{weeksSinceStart}-7-{sundayCycleChar}"
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
    elif liturgySeasons[date] == "ORDINARY":
        if date < calendar.ashWednesday:
            weeksSinceStart = int((date - calendar.christmasEnd).days / 7) + 1
        else:
            weeksSinceStart = int(
                (date - calendar.pentecost).days / 7 + calendar.pentecostStartOT
            )

        if weeksSinceStart < 10:
            weeksSinceStart = "0" + str(weeksSinceStart)

        if dayOfTheWeek == 7:
            keySearch = f"{weeksSinceStart}-7-{sundayCycleChar}"
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
    elif liturgySeasons[date] == "LENT":
        weeksSinceAsh = int(
            (date - calendar.ashWednesday + datetime.timedelta(days=2)).days / 7
        )

        if date + datetime.timedelta(days=3) == calendar.easter:  # Holy Thursday
            liturgy[date] = [lentLectionary["CHRISM"], easterLectionary["0-4"]]
        elif dayOfTheWeek == 7:
            if weeksSinceAsh + 1 == 6:
                keySearch = f"6-7-{sundayCycleChar}"
                liturgy[date] = [
                    lentLectionary[keySearch + "-MASS"],
                    lentLectionary[keySearch + "-PROC"],
                ]
            else:
                keySearch = f"{weeksSinceAsh + 1}-7-{sundayCycleChar}"
                liturgy[date] = [lentLectionary[keySearch]]
        else:
            keySearch = f"{weeksSinceAsh}-{dayOfTheWeek}"
            liturgy[date] = [lentLectionary[keySearch]]

    # ####################
    # ||                ||
    # ||     EASTER     ||
    # ||                ||
    # ####################
    elif liturgySeasons[date] == "EASTER":
        weeksSinceEaster = int((date - calendar.easter).days / 7 + 1)

        if date == calendar.easter - datetime.timedelta(days=1):
            liturgy[date] = [Readings("No Mass")]
        elif date == calendar.easter - datetime.timedelta(days=2):  # Good Friday
            liturgy[date] = [easterLectionary["0-5"]]
        elif date == calendar.easter:  # Easter
            liturgy[date] = [easterLectionary["0-7-VIGIL"], easterLectionary["0-7"]]
        elif date == calendar.pentecost:  # Pentecost
            liturgy[date] = [
                easterLectionary["PENTECOST-VIGIL"],
                easterLectionary[f"PENTECOST-A"],
            ]
            if calendar.sundayCycle != 1:
                liturgy[date].append(easterLectionary[f"PENTECOST-{sundayCycleChar}"])
        elif dayOfTheWeek == 7:  # Easter Sundays
            keySearch = f"{weeksSinceEaster - 1}-7-{sundayCycleChar}"
            liturgy[date] = [easterLectionary[keySearch]]
            if weeksSinceEaster == 6:  # Ascension
                liturgy[date].insert(
                    0,
                    easterLectionary[f"ASCENSION-{sundayCycleChar}"],
                )
        else:  # Easter Weekdays
            keySearch = f"{weeksSinceEaster}-{dayOfTheWeek}"
            liturgy[date] = [easterLectionary[keySearch]]


solemnityLectionary = lectionary["SOLEMNITY"]
trinitySunday = getNextSunday(calendar.pentecost)
bodyBlood = getNextSunday(trinitySunday)
sacredHeart = bodyBlood + datetime.timedelta(days=5)
startHolyWeek = calendar.easter - datetime.timedelta(days=6)

saintLectionary = lectionary["SAINTPROPER"]
thanksgiving = getNextThursday(datetime.datetime(year, 10, 31), 4)
liturgy[thanksgiving].append(saintLectionary["THANKSGIVING"])
for date in liturgySeasons:
    dayOfTheWeek = date.isoweekday()
    lectionaryDate = dateToLectionaryDate(date)

    # ####################
    # ||                ||
    # ||     MAJOR      ||
    # ||  SOLEMNITIES   ||
    # ||                ||
    # ####################
    if date == trinitySunday:
        liturgy[date].insert(0, solemnityLectionary[f"TrinSun-{sundayCycleChar}"])
    elif date == bodyBlood:
        liturgy[date].insert(0, solemnityLectionary[f"BodyBlood-{sundayCycleChar}"])
    elif date == sacredHeart:
        liturgy[date].insert(0, solemnityLectionary[f"SacHeart-{sundayCycleChar}"])

    if lectionaryDate in solemnityLectionary:
        if date == datetime.datetime(year, 3, 19):  # Solemnity of St. Joseph
            if startHolyWeek < date < calendar.easter:
                josephDate = getPrevSaturday(date)
            elif dayOfTheWeek == 7 and liturgySeasons[date] == "LENT":
                josephDate = date + datetime.timedelta(days=1)
            else:
                josephDate = date
            liturgy[josephDate].insert(0, solemnityLectionary["Mar19"])

        elif date == datetime.datetime(year, 3, 25):  # Annunciation of the Lord
            annunciationDate = date
            if dayOfTheWeek == 7 and liturgySeasons[date] == "LENT":
                annunciationDate = datetime.datetime(year, 3, 26)
            if startHolyWeek <= annunciationDate < getNextSunday(calendar.easter):
                annunciationDate = calendar.easter + datetime.timedelta(days=8)
            liturgy[annunciationDate].insert(0, solemnityLectionary["Mar25"])

        elif date == datetime.datetime(
            year, 6, 24
        ):  # The Nativity of St. John the Baptist
            if date == sacredHeart:
                baptistDate = datetime.datetime(year, 6, 23)
            else:
                baptistDate = date

            liturgy[baptistDate][:0] = [
                solemnityLectionary["Jun24"],
                solemnityLectionary["Jun24-VIGIL"],
            ]

        elif date == datetime.datetime(year, 12, 8):  # Conception of Mary
            if dayOfTheWeek == 7 and liturgySeasons[date] == "ADVENT":
                conceptionDate = datetime.datetime(year, 12, 9)
            else:
                conceptionDate = date
            liturgy[conceptionDate].insert(0, solemnityLectionary["Dec8"])
        else:
            if f"{lectionaryDate}-VIGIL" in solemnityLectionary:
                liturgy[date][:0] = [
                    solemnityLectionary[lectionaryDate],
                    solemnityLectionary[f"{lectionaryDate}-VIGIL"],
                ]
            else:
                liturgy[date].insert(0, solemnityLectionary[lectionaryDate])

    # ####################
    # ||                ||
    # ||   PROPER OF    ||
    # ||     SAINTS     ||
    # ||                ||
    # ####################
    if lectionaryDate in saintLectionary:
        readings = saintLectionary[lectionaryDate]
        if dayOfTheWeek == 7:
            liturgy[date].append(readings)
        else:
            liturgy[date].insert(0, readings)


for date in liturgy:
    print(f"{date.strftime('%x')} - {liturgy[date]}")

# Parsing for JSON
parsedLiturgy = {}
for date, readings in liturgy.items():
    # print(readings[0].toDict())
    dateReadings = [reading.toDict() for reading in readings]
    parsedLiturgy[date.strftime("%Y-%m-%d")] = dateReadings

os.makedirs("./liturgies", exist_ok=True)
with open(f"./liturgies/liturgy{year}.json", "w") as f:
    json.dump(parsedLiturgy, f, indent=2)
