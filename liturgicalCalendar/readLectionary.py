#!/usr/bin/env python

import requests
from bs4 import BeautifulSoup

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
        date = cols[1]
        if not date in [".", "Day", "Day or Feast"]:
            cols.pop(1)
            cols.pop(2)
            if not date in tableData:
                tableData[date] = [cols]
            else:
                tableData[date].append(cols)


for row in tableData:
    print(f"{row:75} | {tableData[row]}")
