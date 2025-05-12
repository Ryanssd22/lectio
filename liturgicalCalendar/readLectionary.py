#!/usr/bin/env python

import requests
from bs4 import BeautifulSoup


def printTableData(key):
    print(f"{row:75} | {sortedTableData[row]}")


weekdayPage = requests.get(
    "https://catholic-resources.org/Lectionary/Index-Weekdays.htm"
)
weekdaySoup = BeautifulSoup(weekdayPage.text, "html.parser")
tables = weekdaySoup.find_all("table")
tableData = {}

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
        date = date.replace("Ord. Time", "OT")
        date = date.replace("Lent", "LE")
        date = date.replace("Advent", "AD")
        date = date.replace("Easter", "EA")
        if not date in [".", "Day", "Day or Feast"]:
            cols.pop(3)
            cols.pop(1)
            if not date in tableData:
                tableData[date] = [cols]
            else:
                tableData[date].append(cols)

sortedTableData = dict(sorted(tableData.items()))

for row in tableData:
    if "OT" in row:
        printTableData(row)
