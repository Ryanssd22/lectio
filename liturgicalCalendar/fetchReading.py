import os
import sys

sys.path.append("./biblegateway")
from bibledata import BOOKS

BOOKS.update(
    {
        "Judith": "Judith",
        "Psalms": "Ps",
        "Song Of Songs": "Songs",
        "James": "James",
        "1 Peter": "1Peter",
        "2 Peter": "2Peter",
    }
)


# Fetches reading given a string and bible
def fetchReading(reading, bible):
    test = 1 + 1


# Reads a specific version of the bible from biblegate/bibles/ and parses it into a list
def readBible(version="NABRE"):
    scriptDir = os.path.dirname(os.path.abspath(__file__))
    biblePath = os.path.join(scriptDir, f"biblegateway/bibles/{version}.txt")
    try:
        with open(biblePath, "r", encoding="utf-8-sig") as file:
            bible = {}
            for line in file:
                if line.title().strip() in BOOKS:
                    currentBook = line.strip()
                    bible[currentBook] = []
                    verseNumber = 1
                    verses = []
                else:
                    verse = line.split(" ", 1)[1].strip()
                    if int(line[0]) != verseNumber:
                        bible[currentBook].append(verses)
                        verses = [verse]
                        verseNumber = int(line[0])
                    else:
                        verses.append(verse)
        return bible
    except Exception as e:
        print(f"Error: {e}")


bible = readBible()
fetchReading("Num 6:22-27", bible)
print(bible["JOHN"][2][15])
print(bible["JOHN"][2][16])
