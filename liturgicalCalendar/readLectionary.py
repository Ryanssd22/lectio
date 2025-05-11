#!/usr/bin/env python

import requests
from bs4 import BeautifulSoup

weekdayPage = requests.get(
    "https://catholic-resources.org/Lectionary/Index-Weekdays.htm"
)
weekdaySoup = BeautifulSoup(weekdayPage.text, "html.parser")
tables = weekdaySoup.find_all("table")
tableData = []

for i, table in enumerate(tables):
    rows = table.find_all("tr")
    tableData.append([])
    for row in rows:
        cols = row.find_all("td")
        cols = [col.text.strip() for col in cols]
        tableData[i].append(cols)

for table in tableData:
    for row in table:
        print(f"{row[0]:40} | {row[1]:55} | {row[2]:4} | {row[3]:10}")
