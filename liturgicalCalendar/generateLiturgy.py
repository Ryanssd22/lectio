"""
Generates Lectionary using year and lectionaryTemplate.json (Generated from readLectionary.py)
"""

import json
import sys
import datetime
from readCalendar import getCalendar


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
    lectionary = json.load(f)

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
for date in liturgySeasons:
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
        # Sundays
        if date.weekday() == 6:
            weeksSinceStart = int((date - calendar.adventStart).days / 7 + 1)
            keySearch = (
                f"0{weeksSinceStart}-7-{sundayCycleIntToChar(calendar.sundayCycle)}"
            )
            liturgy[date] = [adventLectionary[keySearch]]


for date in liturgy:
    if liturgySeasons[date] == "ADVENT":
        print(f"{date.strftime('%x')} - {liturgy[date]}")
