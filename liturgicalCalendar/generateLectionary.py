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

# Christmas
christmasLectionary = lectionary["CHRISTMAS"]
for date in liturgySeasons:
    if liturgySeasons[date] == "CHRISTMAS":
        liturgy[date] = []
        match date.month:
            case 1:
                month = "Jan"
            case 12:
                month = "Dec"
        dateSearch = f"{month}{date.day}"

        # Default Christmas Readings
        if date == datetime.datetime(year, 12, 25):
            liturgy[date] = [
                christmasLectionary["CHRISTMAS-VIGIL"],
                christmasLectionary["CHRISTMAS-NIGHT"],
                christmasLectionary["CHRISTMAS-DAWN"],
                christmasLectionary["CHRISTMAS-DAY"],
            ]
        elif date == calendar.holyFamily:
            nextSundayCycle = (calendar.sundayCycle + 1) % 3
            keySearch = f"HOLYFAMILY-{sundayCycleIntToChar(nextSundayCycle)}"
            if nextSundayCycle == 1:
                liturgy[date] = [christmasLectionary[keySearch]]
            else:
                liturgy[date] = [
                    christmasLectionary["HOLYFAMILY-A"],
                    christmasLectionary[keySearch],
                ]
        elif dateSearch in christmasLectionary and (
            date < calendar.epiphany or date > datetime.datetime(year, 12, 25)
        ):
            liturgy[date].append(christmasLectionary[dateSearch])
        elif date == calendar.christmasEnd:
            keySearch = f"BAPTISM-{sundayCycleIntToChar(calendar.sundayCycle)}"
            liturgy[date].append(christmasLectionary[keySearch])
        else:
            if date == calendar.epiphany:
                liturgy[date].append(christmasLectionary["EPIPHANY"])
            else:
                daysFromEpiphany = (date - calendar.epiphany).days
                liturgy[date].append(
                    christmasLectionary[f"EPIPHANY-{daysFromEpiphany}"]
                )


for date in liturgySeasons:
    if liturgySeasons[date] == "CHRISTMAS":
        print(f"{date.strftime('%x')} - {liturgy[date]}")
