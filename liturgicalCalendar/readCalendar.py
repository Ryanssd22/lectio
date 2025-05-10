#!/usr/bin/env python

import sys
import datetime
import ephem


def getNextSunday(date, delta=1):
    for i in range(delta):
        date += datetime.timedelta(days=1)
        while date.strftime("%a") != "Sun":
            date += datetime.timedelta(days=1)
    return date


def getPrevSunday(date, delta=1):
    for i in range(delta):
        date += datetime.timedelta(days=-1)
        while date.strftime("%a") != "Sun":
            date += datetime.timedelta(days=-1)
    return date


# "Paschal's Full Moon," yeah kinda crazy ik
def getEaster(yr):
    g = yr % 19 + 1
    s = (yr - 1600) // 100 - (yr - 1600) // 400
    l = ((yr // 100 - 14) * 8) // 25
    p = (3 - 11 * g + s - l) % 30
    if p == 29 or (p == 28 and g > 11):
        p -= 1
    d = (yr + (yr // 4) - (yr // 100) + (yr // 400)) % 7
    x = (4 - d - p) % 7 + 1
    e = p + x
    easter = datetime.datetime(year, 3, 21)
    easter += datetime.timedelta(days=e)
    return easter


def getAdventStart(yr):
    christmas = datetime.datetime(year, 12, 25)
    return getPrevSunday(christmas, 4)


def getEpiphany(yr):
    jan6 = datetime.datetime(yr - 1, 12, 31)
    return getNextSunday(jan6)


def getAshWednesday(yr):
    ashWednesday = getEaster(yr)
    ashWednesday += datetime.timedelta(days=-46)
    return ashWednesday


def getChristmasEnd(epiphany):
    if epiphany.day in [6, 7]:
        return epiphany + datetime.timedelta(days=1)
    else:
        return getNextSunday(epiphany)


def getWeeksBeforeLent(ashWednesday, christmasEnd):
    weeks = 0
    sundayIndex = ashWednesday
    while sundayIndex > christmasEnd:
        sundayIndex = getPrevSunday(sundayIndex)
        weeks += 1
    return weeks


def getPentecostStartOT(pentecost, adventStart, weeksBeforeLent):
    weeks = 0
    sundayIndex = adventStart
    while sundayIndex > pentecost:
        sundayIndex = getPrevSunday(sundayIndex)
        weeks += 1
    if weeks + weeksBeforeLent != 34:
        pentecostStart = weeksBeforeLent + 2
    else:
        pentecostStart = weeksBeforeLent + 1
    return pentecostStart


if len(sys.argv) != 2:
    print(f"Usage: {sys.argv[0]} year")
    sys.exit()

year = int(sys.argv[1])
weekdayCycle = year % 2
sundayCycle = (year - 1) % 3 + 1  # 1 - A, 2 - B, 3 - C
easterDate = getEaster(year)
epiphany = getEpiphany(year)
ashWednesday = getAshWednesday(year)
pentecost = easterDate + datetime.timedelta(days=49)
christmasEnd = getChristmasEnd(epiphany)
adventStart = getAdventStart(year)
weeksBeforeLent = getWeeksBeforeLent(ashWednesday, christmasEnd)
pentecostStartOT = getPentecostStartOT(pentecost, adventStart, weeksBeforeLent)

print("Weekday cycle:", weekdayCycle)
print("Sunday cycle:", sundayCycle)
print("Feast of Epiphany:", epiphany.strftime("%x"))
print("End of Christmas (Baptism of our Lord):", christmasEnd.strftime("%x"))
print("Ash Wednesday:", ashWednesday.strftime("%x"))
print("Easter:", easterDate.strftime("%x"))
print("Pentecost:", pentecost.strftime("%x"))
print("Advent start:", adventStart.strftime("%x"))
print("Weeks of OT before lent:", weeksBeforeLent)
print("Starting OT after pentecost:",pentecostStartOT)
