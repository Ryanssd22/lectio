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
import inflect
from typing import Dict, List, Union, Optional, Tuple
from bs4 import BeautifulSoup
import json
import copy

from biblegateway.bibledata import LECTIONARYTOBIBLEGATEWAY


def fixNewLine(string):
    return " ".join(string.split()).strip()


parse_free_list = [
    "Good Friday",
    "Easter Sunday",
    "Pentecost",
    "4th Week of Easter - Mon",
]


def readings_verse_parse(verseString, date):
    if date:
        for ban in parse_free_list:
            if ban in date:
                return None
    updatedVerse = fixNewLine(verseString) if verseString not in [None, "x"] else None
    if not updatedVerse:
        return None

    reading = {
        "rawReading": updatedVerse,
        "reading": parse_bible_citation_structured(updatedVerse),
    }

    # This loop is so crap lol, remove duplicates
    newUniqueReadings = []
    for readingItem in reading["reading"]:
        uniqueReadings = copy.deepcopy(readingItem)
        uniqueReadings["verses"] = []
        for item in readingItem["verses"]:
            if item not in uniqueReadings["verses"]:
                uniqueReadings["verses"].append(item)
        newUniqueReadings.append(uniqueReadings)
    reading["reading"] = newUniqueReadings

    # print(date)

    return reading


class Readings:
    def __init__(
        self,
        title=None,
        first=None,
        responsal=None,
        second=None,
        gospel=None,
        rank=None,
        date=None,
    ):
        self.title = title
        self.first = readings_verse_parse(first, date)
        self.responsal = readings_verse_parse(responsal, date)
        self.second = readings_verse_parse(second, date)
        self.gospel = readings_verse_parse(gospel, date)
        self.rank = rank if rank else None

    def __repr__(self):
        string = ""
        if self.rank:
            string += f"{self.rank}: "
        if self.title:
            string += f"{self.title}:"
        if self.first:
            string += f" [FIRST: {self.first}]"
        if self.responsal:
            string += f" [RESPONSAL: {self.responsal}]"
        if self.second:
            string += f" [SECOND: {self.second}]"
        if self.gospel:
            string += f" [GOSPEL: {self.gospel}]"

        return "{" + string + "}"

    def toDict(self):
        return {
            "title": self.title,
            "first": self.first,
            "responsal": self.responsal,
            "second": self.second,
            "gospel": self.gospel,
            "rank": self.rank,
        }


# Compile regex patterns once for better performance
PATTERNS = {
    "verse_letters": re.compile(r"[a-zA-Z]"),
    "trailing_notes": re.compile(r"[-–—]\s*[A-Za-z]"),
    "parenthetical": re.compile(r"\(.*?\)"),
    "year_cleanup": re.compile(r"\bor.*?\bYear [ABC]\b.*", re.IGNORECASE),
    "hash_brackets": re.compile(r"\s*[\(\[]\s*#.*?[\)\]]"),
    "hash_standalone": re.compile(r"\s*#\d+(?:\.\d+)?[\)\.,;:]*"),
    "square_brackets": re.compile(r"\[.*?\]"),
    "trailing_asterisks": re.compile(r"\*+$"),
    "trailing_punct": re.compile(r"[\(,;:\s]+$"),
    "or_digit_glue": re.compile(r"(?<=\d)or(?=\s*[A-Za-z])", re.IGNORECASE),
    "or_normalize": re.compile(r"\bor\b", re.IGNORECASE),
    "verse_suffix_period": re.compile(r"(\d[ab]+)\."),
    "period_comma_fix": re.compile(r"(?<!\+)(\d[ab]?)\.\s*(\d)"),
    "book_chapter_verse": re.compile(r"^([1-3]?\s?(?:[A-Za-z]+\s?)+)\s+(\d+):(.+)"),
    "chapter_verse": re.compile(r"^(\d+):(.+)"),
    "verse_separators": re.compile(r"[,+]"),
    "citation_separators": re.compile(r"\s+(?:and|or)\s+"),
    "dash_variants": re.compile(r"[–—]"),
}


class VerseRange:
    """Represents a verse or range of verses"""

    __slots__ = ["chapter", "verse", "range_end"]

    def __init__(self, chapter: int, verse: int, range_end: Optional[Dict] = None):
        self.chapter = chapter
        self.verse = verse
        self.range_end = range_end

    def to_dict(self) -> Dict:
        result = {"chapter": self.chapter, "verse": self.verse}
        if self.range_end:
            result["range_end"] = self.range_end
        return result


class BibleReading:
    """Represents a complete Bible reading with book and verses"""

    __slots__ = ["book", "verses"]

    def __init__(self, book: str, verses: List[VerseRange]):
        self.book = book.strip()
        self.verses = verses

    def to_dict(self) -> Dict[str, Union[str, List[Dict]]]:
        return {"book": self.book, "verses": [v.to_dict() for v in self.verses]}

    def is_valid(self) -> bool:
        return bool(self.book and self.verses)


def clean_verse_num(verse: str) -> str:
    """Remove trailing letters and whitespace from verse numbers"""
    return PATTERNS["verse_letters"].sub("", verse).strip()


def parse_verse_part(verse_part: str) -> Tuple[Optional[int], int]:
    """Parse "chapter:verse" or "verse" string into integers"""
    if ":" in verse_part:
        chapter_str, verse_str = verse_part.split(":", 1)
        return int(chapter_str), int(verse_str)
    return None, int(verse_part)


def clean_citation_text(text: str) -> str:
    """Clean and normalize citation text using compiled patterns"""
    # Apply all cleaning patterns in sequence
    cleaners = [
        (PATTERNS["year_cleanup"], ""),
        (PATTERNS["hash_brackets"], ""),
        (PATTERNS["hash_standalone"], ""),
        (PATTERNS["parenthetical"], ""),
        (PATTERNS["square_brackets"], ""),
        (PATTERNS["dash_variants"], "-"),
        (PATTERNS["trailing_asterisks"], ""),
        (PATTERNS["trailing_punct"], ""),
        (PATTERNS["or_digit_glue"], " or "),
        (PATTERNS["or_normalize"], " or "),
        (PATTERNS["verse_suffix_period"], r"\1,"),
        (PATTERNS["period_comma_fix"], r"\1, \2"),
    ]

    for pattern, replacement in cleaners:
        text = pattern.sub(replacement, text)

    return text.strip()


def parse_verse_range(verse_str: str, current_chapter: int) -> List[VerseRange]:
    """Parse a single verse or range specification"""
    verses = []

    if "-" in verse_str:
        start_str, end_str = verse_str.split("-", 1)
        start_ch, start_verse = parse_verse_part(clean_verse_num(start_str))
        end_ch, end_verse = parse_verse_part(clean_verse_num(end_str))

        # Use current chapter if not specified
        start_ch = start_ch or current_chapter
        end_ch = end_ch or current_chapter

        if start_ch == end_ch:
            # Single chapter range
            verses.extend(
                VerseRange(start_ch, v) for v in range(start_verse, end_verse + 1)
            )
        else:
            # Multi-chapter range
            verses.append(
                VerseRange(
                    start_ch, start_verse, {"chapter": end_ch, "verse": end_verse}
                )
            )
    else:
        # Single verse
        verse_num = int(clean_verse_num(verse_str))
        verses.append(VerseRange(current_chapter, verse_num))

    return verses


def parse_single_reading(segment: str) -> Optional[BibleReading]:
    """Parse a single Bible reading segment"""
    segment = segment.strip()
    if not segment:
        return None

    # Clean the segment
    segment = PATTERNS["trailing_notes"].split(segment)[0].strip()
    segment = PATTERNS["parenthetical"].sub("", segment).strip(",; ")
    segment = PATTERNS["dash_variants"].sub("-", segment)

    verses = []
    book = ""
    current_chapter = None

    # Process semicolon-separated parts
    parts = [p.strip() for p in segment.split(";") if p.strip()]

    for part in parts:
        # Try to match book + chapter:verse pattern
        match = PATTERNS["book_chapter_verse"].match(part)
        if match:
            book, chapter_str, rest = match.groups()
            current_chapter = int(chapter_str)
        else:
            # Try chapter:verse pattern
            match = PATTERNS["chapter_verse"].match(part)
            if match:
                chapter_str, rest = match.groups()
                current_chapter = int(chapter_str)
            else:
                continue

        if current_chapter is None:
            continue

        # Parse verse specifications
        verse_parts = [
            v.strip() for v in PATTERNS["verse_separators"].split(rest) if v.strip()
        ]

        for verse_part in verse_parts:
            verses.extend(parse_verse_range(verse_part, current_chapter))

    if not book or not verses:
        return None

    # Lectionary book titles into biblegateway titles
    if book in LECTIONARYTOBIBLEGATEWAY:
        book = LECTIONARYTOBIBLEGATEWAY[book]

    reading = BibleReading(book, verses)
    return reading if reading.is_valid() else None


def parse_bible_citation_structured(
    citation: str,
) -> List[Dict[str, Union[str, List[Dict]]]]:
    """
    Parse a Bible citation string into structured data.

    Args:
        citation: Bible citation string (e.g., "Gen 1:1-5; 2:1-3 or Ex 20:1-17")

    Returns:
        List of dictionaries containing book and verses information
    """
    if not citation or not citation.strip():
        return []

    print(f"Input: {citation}")

    # Clean the citation text
    cleaned = clean_citation_text(citation)
    # print(f"Cleaned: {cleaned}")

    # Split on "and" or "or" separators
    segments = [
        s.strip() for s in PATTERNS["citation_separators"].split(cleaned) if s.strip()
    ]

    readings = []
    for segment in segments:
        # print(f"Segment: {segment}")

        reading = parse_single_reading(segment)
        if reading:
            readings.append(reading.to_dict())
            # print(f"Parsed: {reading.to_dict()}")
        # else:
        # print("Parsed: None")

    return readings


def printDict(dict):
    for row in dict:
        print(f"{row:30} | {dict[row]}")


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


def getOrdinalNumber(number):
    p = inflect.engine()
    return p.number_to_words(p.ordinal(number))


def lectionaryDateToDate(lectionaryDate):
    match lectionaryDate[:3]:
        case "Jan":
            month = 1
        case "Feb":
            month = 2
        case "Mar":
            month = 3
        case "Apr":
            month = 4
        case "May":
            month = 5
        case "Jun":
            month = 6
        case "Jul":
            month = 7
        case "Aug":
            month = 8
        case "Sep":
            month = 9
        case "Oct":
            month = 10
        case "Nov":
            month = 11
        case "Dec":
            month = 12
    day = int(lectionaryDate[3:])
    return datetime.datetime(month, day, year)


def getDayOfWeekString(number):
    day = "N/A"
    match number:
        case 0:
            day = "Monday"
        case 1:
            day = "Tuesday"
        case 2:
            day = "Wednesday"
        case 3:
            day = "Thursday"
        case 4:
            day = "Friday"
        case 5:
            day = "Saturday"
        case 6:
            day = "Sunday"
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


def getAdvent():
    adventSunday = "https://catholic-resources.org/Lectionary/1998USL-Advent.htm"
    adventWeekday = (
        "https://catholic-resources.org/Lectionary/2002USL-Weekdays-AdventChristmas.htm"
    )

    # Advent Sunday
    AD = {}
    adventSundayTable = getTables(adventSunday)
    adventSundayRows = getRows(adventSundayTable[0])
    adventSundayRows.pop(0)
    for row in adventSundayRows:
        date = row[2]
        cycle = date[-1]

        key = date[0] + "-7-" + cycle
        title = f"{getOrdinalNumber(date[0])} Sunday of Advent"
        title = title[0].upper() + title[1:]

        AD[key] = Readings(
            title,
            first=row[3],
            responsal=row[4],
            second=row[5],
            gospel=row[7],
            date=date,
        )

    # Advent Weekday
    adventWeekdayTable = getTables(adventWeekday)
    adventWeekdayRows = getRows(adventWeekdayTable[0])
    adventWeekdayRows.pop(18)
    adventWeekdayRows.pop(0)
    for row in adventWeekdayRows:
        date = row[2]

        key = ""
        if "December" in date:
            key = "Dec" + date[9:11]
            title = "TBD"
        else:
            day = getDayOfWeek(date)
            key = date[0] + "-" + day
            title = f"{getOrdinalNumber(date[0])} {getDayOfWeekString(int(day) - 1)} of Advent"
        title = title[0].upper() + title[1:]

        AD[key] = Readings(
            title, first=row[3], responsal=row[4], gospel=row[6], date=date
        )

    return AD


def getOrdinaryTime():
    ordinarySundayA = "https://catholic-resources.org/Lectionary/1998USL-OrdinaryA.htm"
    ordinarySundayB = "https://catholic-resources.org/Lectionary/1998USL-OrdinaryB.htm"
    ordinarySundayC = "https://catholic-resources.org/Lectionary/1998USL-OrdinaryC.htm"
    ordinaryWeekday1 = (
        "https://catholic-resources.org/Lectionary/2002USL-Weekdays-OT-I.htm"
    )
    ordinaryWeekday2 = (
        "https://catholic-resources.org/Lectionary/2002USL-Weekdays-OT-II.htm"
    )

    # Ordinary Time Sundays
    OT = {}
    ordinarySundayTableA = getTables(ordinarySundayA)
    ordinarySundayTableB = getTables(ordinarySundayB)
    ordinarySundayTableC = getTables(ordinarySundayC)
    ordinarySundayRows = [
        getRows(ordinarySundayTableA[0]),
        getRows(ordinarySundayTableB[0]),
        getRows(ordinarySundayTableC[0]),
    ]
    for i, rows in enumerate(ordinarySundayRows):
        rows.pop(0)
        weekendYear = ""
        match i:
            case 0:
                weekendYear = "A"
            case 1:
                weekendYear = "B"
            case 2:
                weekendYear = "C"

        for row in rows:
            date = row[2]
            if date[1] in ["n", "r", "t"]:
                date = "0" + date[0]
            if "Feast of the Baptism of the Lord" in date:
                date = "01"
            key = date[:2] + "-7-" + weekendYear

            otWeek = int(date[1]) if date[0] == "0" else int(date[:2])

            if otWeek == 34:
                title = f"Solemnity of Our Lord Jesus Christ the King"
            else:
                title = f"{getOrdinalNumber(otWeek)} Sunday of Ordinary Time"

            title = title[0].upper() + title[1:]

            OT[key] = Readings(
                title,
                first=row[3],
                responsal=row[4],
                second=row[5],
                gospel=row[7],
                date=date,
            )

    # Ordinary time Weekday
    ordinaryWeekdayTable1 = getTables(ordinaryWeekday1)
    ordinaryWeekdayTable2 = getTables(ordinaryWeekday2)
    ordinaryWeekdayRows = [
        getRows(ordinaryWeekdayTable1[0]),
        getRows(ordinaryWeekdayTable2[0]),
    ]
    for i, rows in enumerate(ordinaryWeekdayRows):
        for row in rows:
            date = row[1]
            if date != "Day":
                weekday = getDayOfWeek(date)

                key = date[5:7] + "-" + weekday
                if key[1] == " ":
                    key = key.replace(" ", "")
                    key = "0" + key

                key = key + "-" + str(i + 1)

                otWeek = int(key[1]) if key[0] == "0" else int(key[:2])
                title = f"{getOrdinalNumber(otWeek)} {getDayOfWeekString(int(key[3])-1)} of Ordinary Time"
                title = title[0].upper() + title[1:]

                OT[key] = Readings(
                    title=title,
                    first=row[2],
                    responsal=row[3],
                    gospel=row[5],
                    date=date,
                )

    return OT


def getChristmas():
    christmasSunday = "https://catholic-resources.org/Lectionary/1998USL-Christmas.htm"
    adventWeekday = (
        "https://catholic-resources.org/Lectionary/2002USL-Weekdays-AdventChristmas.htm"
    )

    # Christmas Sunday
    CH = {}
    christmasSundayTables = getTables(christmasSunday)
    christmasSundayRows = getRows(christmasSundayTables[0])
    christmasSundayRows.pop(0)
    for i, row in enumerate(christmasSundayRows):
        date = " ".join(row[2].split()).strip()

        if i == 4:  # Fix typo for Holy Family year A
            date = "The Holy Family - A"

        match i:
            case 0:
                date = "CHRISTMAS-VIGIL"
                title = "The Nativity of the Lord, Christmas Vigil"
            case 1:
                date = "CHRISTMAS-NIGHT"
                title = "The Nativity of the Lord, Christmas Night"
            case 2:
                date = "CHRISTMAS-DAWN"
                title = "The Nativity of the Lord, Christmas Dawn"
            case 3:
                date = "CHRISTMAS-DAY"
                title = "The Nativity of the Lord, Christmas Day"
            case 4:
                date = "HOLYFAMILY-A"
                title = "The Holy Family of Jesus, Mary, and Joseph"
            case 5:
                date = "HOLYFAMILY-B"
                title = "The Holy Family of Jesus, Mary, and Joseph (Opt. year B)"
            case 6:
                date = "HOLYFAMILY-C"
                title = "The Holy Family of Jesus, Mary, and Joseph (Opt. year C)"
            case 7:
                date = "Jan1"
                title = "Solemnity of the Blessed Virgin Mary, Mother of God"
            case 8:  # In US, this is always the epiphany
                date = "03-7"
                title = "Second Sunday after Christmas"
            case 9:
                date = "EPIPHANY"
                title = "The Epiphany of the Lord"
            case 10:
                date = "BAPTISM-A"
                title = "The Baptism of the Lord"
            case 11:
                date = "BAPTISM-B"
                title = "The Baptism of the Lord (Opt. year B)"
            case 12:
                date = "BAPTISM-C"
                title = "The Baptism of the Lord (Opt. year C)"

        CH[date] = Readings(
            title,
            first=row[3],
            responsal=row[4],
            second=row[5],
            gospel=row[7],
            date=date,
        )

    # Christmas Weekday
    christmasWeekdayTable = getTables(adventWeekday)[1]
    christmasWeekdayRows = getRows(christmasWeekdayTable)
    christmasWeekdayRows.pop(0)

    for i, row in enumerate(
        christmasWeekdayRows
    ):  # Readings already in chrismas Sundays
        if row[2] == "(see the Sunday Lectionary)":
            christmasWeekdayRows.pop(i)

    for i, row in enumerate(christmasWeekdayRows):
        title = None
        date = " ".join(row[1].split()).strip()
        date = date.replace("[", "")
        if date[:3] in ["Dec", "Jan"]:
            date = date[:3] + date[5:7]
            if date[4] in [" ", "]"]:
                date = date[:-1]
        else:
            date = "EPIPHANY-" + str(i - 11)
            title = f"{getDayOfWeekString(i-12)} after Epiphany"

        if date == "Dec26":
            title = "Feast of St. Stephen, the first martyr"
        elif date == "Dec27":
            title = "St. John, Apostle and Evangelist"
        elif date == "Dec28":
            title = "Feast of the Holy Innocents, martyrs"
        elif date == "Dec29":
            title = "Octave of Christmas, Day 5"
        elif date == "Dec30":
            title = "Octave of Christmas, Day 6"
        elif date == "Dec31":
            title = "Octave of Christmas, Day 7"
        elif "Jan" in date:
            title = "Christmas Weekday"

        CH[date] = Readings(
            title, first=row[2], responsal=row[3], gospel=row[5], date=date
        )

    return CH


def getLent():
    lentSunday = "https://catholic-resources.org/Lectionary/1998USL-Lent.htm"
    lentWeekday = "https://catholic-resources.org/Lectionary/2002USL-Weekdays-Lent.htm"

    # Lent Sunday
    LE = {}
    lentSundayTables = getTables(lentSunday)
    lentSundayRows = getRows(lentSundayTables[0])
    lentSundayRows.pop(0)
    for row in lentSundayRows:
        if len(row) == 8:
            date = row[2]

            first = row[3]
            responsal = row[4]
            second = row[5]
            gospel = row[7]
            if "Palm Sunday" in date:
                for i in ["A", "B", "C"]:
                    gospelReading = row[7].split(f"{i}:")
                    gospelReading = gospelReading[1].split("\n")[0].strip()
                    key = "6-7" + "-" + i
                    if "Procession" in date:
                        title = f"Palm Sunday Procession"
                        key = key + "-PROC"
                        first = None
                        responsal = None
                        second = None
                    else:
                        title = f"Palm Sunday"
                        key = key + "-MASS"
                    gospel = gospelReading
                    LE[key] = Readings(
                        first=first,
                        responsal=responsal,
                        second=second,
                        gospel=gospel,
                        date=date,
                    )

                    title = title[0].upper() + title[1:]
                    LE[key].title = title
            else:
                key = date[0] + "-7-" + date[-1]
                LE[key] = Readings(
                    first=first,
                    responsal=responsal,
                    second=second,
                    gospel=gospel,
                    date=date,
                )

                title = f"{getOrdinalNumber(key[0])} Sunday of Lent"
                title = title[0].upper() + title[1:]
                LE[key].title = title

    # Lent Weekdays
    lentWeekdayTables = getTables(lentWeekday)
    lentWeekdayRows = getRows(lentWeekdayTables[0])
    ashWednesday = 3
    for row in lentWeekdayRows:
        if not row[2] == "Day":
            date = row[2]
            weekday = getDayOfWeek(date)

            key = date[0] + "-" + weekday
            title = f"{getOrdinalNumber(key[0])} {getDayOfWeekString(int(weekday)-1)} of Lent"

            if "Ash" in date:
                key = "0-" + str(ashWednesday)
                if ashWednesday == 3:
                    title = "Ash Wednesday"
                else:
                    title = f"{getDayOfWeekString(ashWednesday-1)} after Ash Wednesday"
                ashWednesday += 1
            elif "Holy Week" in date:
                title = f"{getDayOfWeekString(int(weekday)-1)} of Holy Week"
                if "Chrism Mass" in date:
                    title = "Morning of Holy Thursday, Chrism Mass"
                    key = "CHRISM"
                else:
                    key = "6-" + weekday
            elif "optional" in date:
                title = f"{getOrdinalNumber(key[0])} Week of Lent - Optional Mass"
                key = key[:2] + "OPT"

            title = title[0].upper() + title[1:]
            LE[key] = Readings(
                title, first=row[3], second=row[4], gospel=row[6], date=date
            )

    return LE


def getEaster():
    easterSunday = "https://catholic-resources.org/Lectionary/1998USL-Easter.htm"
    easterWeekday = (
        "https://catholic-resources.org/Lectionary/2002USL-Weekdays-Easter.htm"
    )

    # Easter Sundays
    EA = {}
    easterSundayTables = getTables(easterSunday)
    easterSundayRows = getRows(easterSundayTables[0])
    for row in easterSundayRows:
        if len(row) == 8 and row[2] != "Sunday or Feast":
            date = row[2]
            date = date.split("(")[0].strip()

            if "Holy Thursday" in date:
                title = "Holy Thursday, Evening Mass of the Lord's Supper"
                key = "0-4"
            elif "Good Friday" in date:
                title = "Good Friday"
                key = "0-5"
            elif "Easter Sunday" in date:
                if "Vigil" in date:
                    title = "Easter Sunday, Vigil"
                    key = "0-7-VIGIL"
                else:
                    title = "Easter Sunday"
                    title = "Easter Sunday"
                    key = "0-7"
            elif "Ascension of the Lord" in date:
                title = "Ascension of the Lord"
                key = "ASCENSION-" + date[-1]
            elif "Pentecost" in date:
                if "Vigil" in date:
                    title = "Pentecost, Vigil"
                    key = "PENTECOST-VIGIL"
                else:
                    title = "Pentecost"
                    key = "PENTECOST-" + date[-1]
            else:
                key = str(int(date[0]) - 1) + "-7-" + date[-1]
                if key[0] == 7:
                    key = "8-7-" + date[-1]
                title = f"{getOrdinalNumber(int(key[0])+1)} Sunday of Easter"

            title = title[0].upper() + title[1:]

            EA[key] = Readings(
                title,
                first=row[3],
                responsal=row[4],
                second=row[5],
                gospel=row[7],
                date=date,
            )

    # Easter Weekday
    easterWeekdayTables = getTables(easterWeekday)
    easterWeekdayRows = getRows(easterWeekdayTables[0])
    for row in easterWeekdayRows:
        if row[2] != "Day":
            date = row[2]
            weekday = getDayOfWeek(date)
            if "Octave" in date:
                date = "1"

            key = date[0] + "-" + weekday

            title = f"{getOrdinalNumber(key[0])} {getDayOfWeekString(int(weekday)-1)} of Easter"
            title = title[0].upper() + title[1:]

            EA[key] = Readings(
                title, first=row[3], responsal=row[4], gospel=row[6], date=date
            )

    return EA


def getMajorSolemnities():
    majorSolemnities = (
        "https://catholic-resources.org/Lectionary/1998USL-Solemnities.htm"
    )
    # Major Solemnities
    MAJSOLEM = {}
    majorSolemnityTables = getTables(majorSolemnities)
    pentecostSolemnities = getRows(majorSolemnityTables[0])
    pentecostSolemnities.pop(0)
    lordSolemnities = getRows(majorSolemnityTables[1])
    lordSolemnities.pop(0)
    for i, row in enumerate(pentecostSolemnities):
        key = ""
        match i % 3:
            case 0:
                cycle = "A"
            case 1:
                cycle = "B"
            case 2:
                cycle = "C"
        match i / 3:
            case 0:
                solemnity = "TrinSun"
                title = "Solemnity of the Most Holy Trinity"
            case 1:
                solemnity = "BodyBlood"
                title = "Solemnity of the Most Holy Body and Blood of Christ"
            case 2:
                solemnity = "SacHeart"
                title = "Solemnity of the Most Sacred Heart of Jesus"

        key = f"{solemnity}-{cycle}"

        MAJSOLEM[key] = Readings(
            title,
            first=row[3],
            responsal=row[4],
            second=row[5],
            gospel=row[7],
        )

    majorSolemnityKeys = {
        "Presentation of the Lord": ["Feb2", "The Presentation of the Lord"],
        "St. Joseph": [
            "Mar19",
            "Solemnity of St. Joseph, Spouse of the Blessed Virgin Mary",
        ],
        "Annunciation of the Lord": ["Mar25", "The Annunciation of the Lord"],
        "St. John the Baptist: Vigil": [
            "Jun24-VIGIL",
            "The Nativity of St. John the Baptist: Vigil",
        ],
        "St. John the Baptist: Day": ["Jun24", "The Nativity of St. John the Baptist"],
        "Peter and Paul, Apostles: Vigil": [
            "Jun29-VIGIL",
            "Solemnity of St. Peter and St. Paul, Apostles: Vigil",
        ],
        "Peter and Paul, Apostles: Day": [
            "Jun29",
            "Solemnity of St. Peter and St. Paul, Apostles",
        ],
        "Transfiguration": ["Aug6", "The Transfiguration of the Lord"],
        "Mary: Vigil": [
            "Aug15-VIGIL",
            "The Assumption of the Blessed Virgin Mary: Vigil",
        ],
        "Mary: Day": ["Aug15", "The Assumption of the Blessed Virgin Mary"],
        "Exaltation": ["Sep14", "The Exaltation of the Cross"],
        "All Saints": ["Nov1", "All Saints"],
        "Faithful Departed": ["Nov2", "The Commemortaion of All the Faithful Departed"],
        "Lateran Basilica": ["Nov9", "The Dedication of the Lateran Basilica"],
        "Immaculate Conception": [
            "Dec8",
            "The Immaculate Conception of the Blessed Virgin Mary",
        ],
    }

    for row in lordSolemnities:
        date = row[1]
        title = ""

        for key in majorSolemnityKeys:
            if key in date:
                title = majorSolemnityKeys[key][1]
                date = majorSolemnityKeys[key][0]

        key = date
        MAJSOLEM[key] = Readings(
            title,
            first=row[3],
            responsal=row[4],
            second=row[5],
            gospel=row[6],
            date=date,
        )

    return MAJSOLEM


def getProperSaints():
    saintProper = "https://catholic-resources.org/Lectionary/2002USL-Sanctoral.htm"
    # Saint Proper
    SAINTPROPER = {}
    saintTables = getTables(saintProper)
    saintRows = getRows(saintTables[0])
    saintMonths = {
        "Jan. ": "Jan",
        "Feb. ": "Feb",
        "March ": "Mar",
        "April ": "Apr",
        "May ": "May",
        "June ": "Jun",
        "July ": "Jul",
        "Aug. ": "Aug",
        "Sept. ": "Sep",
        "Oct. ": "Oct",
        "Nov. ": "Nov",
        "Dec. ": "Dec",
    }
    # saintRanks = {
    #     ".": "Optional Memorial",
    #     "USA Opt.": "USA Optional Memorial",
    #     "USA Mem.": "USA Memorial",
    #     "USA Feast": "USA Feast",
    #     "Feast": "Feast",
    #     "Mem.": "Memorial",
    #     "Calif. Proper": "California Proper",
    #     "USA trans. from July 14": "USA Optional Memorial",
    #     "Feast (as of 2016)": "Feast",
    #     "Univ. Opt. / USA Mem.": "USA Memorial",
    #     "19: Univ. 20: USA": "USA Memorial",
    # }

    def parseRank(rank):
        returnString = ""
        if rank == ".":
            return "Optional Memorial"
        elif "USA Mem." in rank or "20: USA" in rank:
            return "USA Memorial"
        elif "USA trans." in rank:
            return "USA Optional Memorial"
        elif "Calif." in rank:
            return "California Proper"

        if "USA" in rank:
            returnString = "USA "
        if "Feast" in rank:
            return f"{returnString}Feast"
        elif "Mem." in rank:
            return f"{returnString}Memorial"
        elif "Opt." in rank:
            return f"{returnString}Optional Memorial"

    for row in saintRows:
        if not row[1] == "Date" and row[3] != "Solemnity":
            date = row[1]
            date = date.split("+")[0].strip()
            date = fixNewLine(date)
            title = fixNewLine(row[2])

            key = date
            if "Thanksgiving" in title:
                key = "THANKSGIVING"
            if "St. Gregory" in title:
                key = "Sept. 3"
            if "St. Paul of the Cross" in title:
                key = "Oct. 20"
            if "St. Francis Xavier" in title:
                key = "Dec. 3"
            if "St. Vincnet" in title:
                key = "Jan23-2"
            if "St. Camillus" in title:
                key = "Jul18"

            for month in saintMonths:
                if month in saintMonths:
                    key = key.replace(month, saintMonths[month])

            if key not in MAJSOLEM:
                rank = parseRank(row[3])
                SAINTPROPER[key] = Readings(
                    title,
                    first=row[5],
                    responsal=row[6],
                    second=row[7],
                    gospel=row[9],
                    rank=rank,
                    date=date,
                )

    return SAINTPROPER


if __name__ == "__main__":

    OT = getOrdinaryTime()
    LE = getLent()
    EA = getEaster()
    AD = getAdvent()
    CH = getChristmas()
    MAJSOLEM = getMajorSolemnities()  # Major Solemnities that can supplant an OT Sunday
    SAINTPROPER = getProperSaints()  # Memorials and feasts, cannot supplant any Sunday

    # print("ADVENT:")
    # printDict(AD)
    # print("\n")
    # print("CHRISTMAS:")
    # printDict(CH)
    # print("\n")
    # print("ORDINARY TIME:")
    # printDict(OT)
    # print("\n")
    # print("LENT:")
    # printDict(LE)
    # print("\n")
    # print("EASTER:")
    # printDict(EA)
    # print("\n")
    # print("MAJOR SOLEMNITIES:")
    # printDict(MAJSOLEM)
    # print("\n")
    # print("PROPER OF SAINTS:")
    # printDict(SAINTPROPER)
    # print("\n")

    def parseDict(dict):
        return {key: dict[key].toDict() for key, reading in dict.items()}

    parsedLectionary = {
        "ADVENT": parseDict(AD),
        "CHRISTMAS": parseDict(CH),
        "ORDINARY": parseDict(OT),
        "LENT": parseDict(LE),
        "EASTER": parseDict(EA),
        "SOLEMNITY": parseDict(MAJSOLEM),
        "SAINTPROPER": parseDict(SAINTPROPER),
    }

    with open("lectionaryTemplate.json", "w", encoding="utf-8") as f:
        json.dump(parsedLectionary, f, indent=2)
