#!/usr/bin/env python3
import re
import sys
import multiprocessing
import threading
import time

import requests
from bs4 import BeautifulSoup

from bibledata import BOOKS, BOOKCHAPTERS

rawBible = {}  # Where all the raw strings will be stored
bibleProgress = {"active": True}
progressBarSize = 0
downloadFinished = False


def downloadBook(book, translation):
    """Downloads a book from biblegateway given a book and translation. Returns a string"""
    chapterAmount = BOOKCHAPTERS[book]
    BOOKABRV = BOOKS[book]
    biblegatewayURL = "https://www.biblegateway.com/passage/?search="
    chapter = 1
    totalChapters = BOOKCHAPTERS[book]
    verseCount = 1
    output = ""
    while chapter < 200:
        try:
            bibleProgress[book] = min(chapter - 1, chapterAmount - 1)
            FULL_URL = (
                biblegatewayURL + book + "+" + str(chapter) + "&version=" + translation
            )
            page = requests.get(FULL_URL, timeout=5)

            # Test if data is found
            if "No results found." in page.text or (
                book in ["Obadiah", "Philemon", "Jude", "2 John", "3 John"]
                and chapter == 2
            ):
                # outputFile.write("\n")
                bibleProgress[book] = chapter - 1
                BOOKCHAPTERS[book] = bibleProgress[book]
                output += "\n"
                break

            # Parsing webpage
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
                        # outputFile.write(f" {clean(parsedVerse)}")
                        output += f" {clean(parsedVerse)}"
                    else:
                        # outputFile.write(f"\n{verseIndex} {clean(parsedVerse)}")
                        output += f"\n{verseIndex} {clean(parsedVerse)}"

                    verseCount += 1
                    oldVerseIndex = verseIndex

            chapter = int(chapter)
            chapter += 1
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            bibleProgress[book] = -1
            break

    rawBible[book] = output
    return output


def updateProgressBar():
    """A progress bar"""
    LENGTH = 50
    namePadding = 15

    global downloadFinished
    downloadFinished = True
    global progressBarSize
    sys.stdout.write(f"\033[{progressBarSize-1}F")
    progressBarSize = 1
    progress = ""
    for book in bibleProgress:
        if book != "active":
            finishedChapters = bibleProgress[book]
            totalChapters = max(BOOKCHAPTERS[book], finishedChapters)
            progressPercent = finishedChapters / totalChapters
            filledLength = int(LENGTH * progressPercent)
            percentComplete = int(100 * progressPercent)
            progress += (
                book
                + " " * (namePadding - len(book))
                + "|"
                + "█" * filledLength
                + "░" * (LENGTH - filledLength)
                + "|"
                + f" {percentComplete}%"
                + f" ({finishedChapters} / {totalChapters})"
                + "\n"
            )
            if progressPercent < 1:
                downloadFinished = False
            progressBarSize += 1
    sys.stdout.write(f"{progress}")
    sys.stdout.flush()

    # percent = int(100 * (iteration / float(total)))
    # filledLength = int(length * iteration // total)
    # bar = "#" * filledLength + "-" * (length - filledLength)
    # sys.stdout.write(f"\r|{bar}| {percent}%")
    # sys.stdout.flush()


def clean(text):
    """Removes trailing whitespace and any uncommon characters"""
    cleanStr = re.sub(r"[^\w\s.,!?;:'\"()\[\]{}\-—]", "", text)
    return re.sub(r"\s+", " ", cleanStr).strip()


if len(sys.argv) > 1:
    TRANSLATION = sys.argv[1]
else:
    TRANSLATION = "NABRE"
BASEURL = "https://www.biblegateway.com/passage/?search="

# Reads all books from bibleGateway and outputs to /biblegateway
multistart = time.time()
threads = []
for book in BOOKS:
    # rawBible[book] = downloadBook(book, TRANSLATION)
    thread = threading.Thread(
        target=downloadBook, args=(book, TRANSLATION), daemon=True
    )
    threads.append(thread)
    rawBible[book] = -1
    thread.start()

while not downloadFinished:
    updateProgressBar()
    downloadFinished = True
    for check in rawBible:
        if rawBible[check] == -1:
            downloadFinished = False
    time.sleep(0.1)

print("\nOutputting into file...")

with open(TRANSLATION + ".txt", "w", encoding="utf-8") as outputFile:
    for book in BOOKS:
        line = book.upper() + rawBible[book]
        outputFile.write(line)

multiduration = round(time.time() - multistart, 2)
print(f"Finished downloading. {multiduration}s")

# start = time.time()
#
# for book in BOOKS:
#     # rawBible[book] = downloadBook(book, TRANSLATION)
#     bookOutput = downloadBook(book, TRANSLATION)
#     print(bookOutput)
#
# duration = round(time.time() - start, 2)
# print(f"Multithreading: {multiduration}s")
# print(f"No multithreading: {duration}s")


# while chapter < 200:
#     try:
#         FULL_URL = (
#             BASEURL + book + "+" + str(chapter) + "&version=" + TRANSLATION
#         )
#
#         page = requests.get(FULL_URL, timeout=5)
#
#         # Test if data is found
#         if "No results found." in page.text or (
#             book in ["Obadiah", "Philemon", "Jude", "2 John", "3 John"]
#             and chapter == 2
#         ):
#             printProgressBar(1, 1)
#             outputFile.write("\n")
#             print(f" Done! {verseCount} Verses written")
#
#             break
#
#         soup = BeautifulSoup(page.text, "html.parser")
#         paragraphs = soup.find_all("p")
#         oldVerseIndex = ""
#         for paragraph in paragraphs:
#             verses = paragraph.find_all(class_=re.compile(BOOKABRV))
#             for verse in verses:
#                 parsedVerse = "".join(
#                     verse.find_all(string=True, recursive=False)
#                 ).strip()
#                 classList = verse.get("class")
#                 className = next(
#                     (cls for cls in classList if re.match(BOOKABRV, cls)), None
#                 )
#                 match = re.search(r"\b(\d+)-(\d+)\b", className)
#                 chapter, verse = match.groups()
#
#                 verseIndex = f"{chapter}:{verse}"
#                 if verseIndex == oldVerseIndex:
#                     outputFile.write(f" {clean(parsedVerse)}")
#                 else:
#                     outputFile.write(f"\n{verseIndex} {clean(parsedVerse)}")
#
#                 verseCount += 1
#                 oldVerseIndex = verseIndex
#
#         chapter = int(chapter)
#         chapter += 1
#         printProgressBar(chapter, max(chapter, chapterAmount + 1))
#     except requests.exceptions.RequestException as e:
#         print(f"Request failed: {e}")
#         break
