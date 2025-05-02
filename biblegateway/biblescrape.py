#!/usr/bin/env python3
import os
import re
import sys

from bibledata import BOOKS, BOOKCHAPTERS

import requests
from bs4 import BeautifulSoup


def printProgressBar(iteration, total, length=50):
    """A progress bar"""
    percent = int(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = "#" * filledLength + "-" * (length - filledLength)
    sys.stdout.write(f"\r|{bar}| {percent}%")
    sys.stdout.flush()


def clean(text):
    """Removes trailing whitespace and any uncommon characters"""
    cleanStr = re.sub(r"[^\w\s.,!?;:'\"()\[\]{}\-—]", "", text)
    return re.sub(r"\s+", " ", cleanStr).strip()


BASEURL = "https://www.biblegateway.com/passage/?search="
TRANSLATION = "DRA"

# Reads all books from bibleGateway and outputs to /biblegateway
with open(TRANSLATION + ".txt", "w", encoding="utf-8") as outputFile:
    for book in BOOKS:
        print("BOOK:", book)
        outputFile.write(f"{book.upper()}")
        BOOKABRV = BOOKS[book]
        chapterAmount = BOOKCHAPTERS[book]

        chapter = 1
        verseCount = 1
        while chapter < 200:
            try:
                FULL_URL = (
                    BASEURL + book + "+" + str(chapter) + "&version=" + TRANSLATION
                )

                page = requests.get(FULL_URL, timeout=5)

                # Test if data is found
                if "No results found." in page.text or (
                    book in ["Obadiah", "Philemon", "Jude", "2 John", "3 John"]
                    and chapter == 2
                ):
                    printProgressBar(1, 1)
                    outputFile.write("\n")
                    print(f" Done! {verseCount} Verses written")

                    break

                soup = BeautifulSoup(page.text, "html.parser")
                paragraphs = soup.find_all("p")
                oldVerseIndex = ""
                for paragraph in paragraphs:
                    verses = paragraph.find_all(class_=re.compile(BOOKABRV))
                    for verse in verses:
                        parsedVerse = "".join(
                            verse.find_all(string=True, recursive=False)
                        ).strip()
                        classList = verse.get("class")
                        className = next(
                            (cls for cls in classList if re.match(BOOKABRV, cls)), None
                        )
                        match = re.search(r"\b(\d+)-(\d+)\b", className)
                        chapter, verse = match.groups()

                        verseIndex = f"{chapter}:{verse}"
                        if verseIndex == oldVerseIndex:
                            outputFile.write(f" {clean(parsedVerse)}")
                        else:
                            outputFile.write(f"\n{verseIndex} {clean(parsedVerse)}")

                        verseCount += 1
                        oldVerseIndex = verseIndex

                chapter = int(chapter)
                chapter += 1
                printProgressBar(chapter, max(chapter, chapterAmount + 1))
            except requests.exceptions.RequestException as e:
                print(f"Request failed: {e}")
                break
