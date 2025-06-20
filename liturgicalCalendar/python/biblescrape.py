#!/usr/bin/env python3
import os
import re
import sys
import threading
import signal
import time

import requests
from bibledata import BOOKCHAPTERS, BOOKS
from bs4 import BeautifulSoup
from bs4.element import NavigableString
from colorama import Fore, init

rawBible = {}  # Where all the raw strings will be stored
bibleProgress = {"active": True}
progressBarSize = 0
downloadFinished = False
init()  # From colorama


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

        if stopEvent.is_set():
            return

        try:
            FULL_URL = (
                biblegatewayURL + book + "+" + str(chapter) + "&version=" + translation
            )
            page = requests.get(FULL_URL, timeout=5)

            # Test if book actually exists
            if "No results found." in page.text and chapter == 1:
                # del bibleProgress[book]
                break

            bibleProgress[book] = min(chapter - 1, chapterAmount - 1)
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

            if stopEvent.is_set():
                return

            # Parsing webpage
            soup = BeautifulSoup(page.text, "html.parser")
            paragraphs = soup.find_all("p")
            oldVerseIndex = ""
            for paragraph in paragraphs:
                verses = paragraph.find_all(class_=re.compile(BOOKABRV))
                for verse in verses:
                    for sup in verse.find_all("sup", class_="versenum"):
                        sup.decompose()
                    for bold in verse.find_all("b", class_="inline-h3"):
                        # bold.insert_before("*")
                        # bold.insert_after("*")
                        bold_text = bold.get_text()
                        bold.replace_with(soup.new_string(f"*{bold_text}*"))
                    # bold.decompose()
                    parsedVerse = verse.get_text(separator=" ", strip=True)
                    # Remove all bracket blocks
                    parsedVerse = re.sub(r"\[.*?\]", "", parsedVerse)
                    # Remove all parentheses
                    parsedVerse = re.sub(r"\(.*?\)", "", parsedVerse)
                    # Fix some commas
                    parsedVerse = re.sub(r" ,", ",", parsedVerse)
                    # Fix some periods
                    parsedVerse = re.sub(r" \.", ".", parsedVerse)
                    # Fix some question marks
                    parsedVerse = re.sub(r" \?", "?", parsedVerse)
                    # Clean up multiple spaces
                    parsedVerse = re.sub(r"\s+", " ", parsedVerse).strip()

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

            # sys.stdout.write(f"\033[1F")
            print(
                Fore.YELLOW
                + f"{'Downloading':>13} "
                + Fore.WHITE
                + f"{chapter} - {book}"
            )

            chapter = int(chapter)
            chapter += 1
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            bibleProgress[book] = -1
            break

    print(Fore.GREEN + f"{'Downloaded':>13} " + Fore.WHITE + f"{book}")

    rawBible[book] = output
    return output


def resource_path():
    """Get path to resource, works for dev and PyInstaller"""
    if getattr(sys, "frozen", False):  # running in a PyInstaller bundle
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(__file__)
    return base_path


def updateProgressBar():
    """A progress bar"""
    LENGTH = 50
    namePadding = 15

    global downloadFinished
    downloadFinished = True
    global progressBarSize
    # sys.stdout.write(f"\033[{progressBarSize-1}F")
    progressBarSize = 1
    progress = ""
    for book in bibleProgress:
        if book != "active":
            finishedChapters = bibleProgress[book]
            totalChapters = max(BOOKCHAPTERS[book], finishedChapters)
            progressPercent = finishedChapters / totalChapters
            # filledLength = int(LENGTH * progressPercent)
            # percentComplete = int(100 * progressPercent)
            # progress += (
            #     book
            #     + " " * (namePadding - len(book))
            #     + "|"
            #     + "█" * filledLength
            #     + "░" * (LENGTH - filledLength)
            #     + "|"
            #     + f" {percentComplete}%"
            #     + f" ({finishedChapters} / {totalChapters})   "
            #     + "\n"
            # )
            if progressPercent < 1:
                downloadFinished = False
            progressBarSize += 1
    # sys.stdout.write(f"{progress}")
    # sys.stdout.flush()

    # percent = int(100 * (iteration / float(total)))
    # filledLength = int(length * iteration // total)
    # bar = "#" * filledLength + "-" * (length - filledLength)
    # sys.stdout.write(f"\r|{bar}| {percent}%")
    # sys.stdout.flush()


def clean(text):
    """Removes trailing whitespace and any uncommon characters"""
    # Convert curly quotes to straight quotes
    text = text.replace("“", '"')
    text = text.replace("”", '"')

    # Then clean with your existing pattern
    cleanStr = re.sub(r'[^\w\s.,!?;:\'"()[\]{}—*-]', "", text)
    return re.sub(r"\s+", " ", cleanStr).strip()


def signalHandler(signum, frame):
    print("\nStopping downloads")
    stopEvent.set()
    for thread in threads:
        thread.join(timeout=2.0)
    sys.exit(0)


if len(sys.argv) > 1:
    TRANSLATION = sys.argv[1]
else:
    TRANSLATION = "NABRE"
BASEURL = "https://www.biblegateway.com/passage/?search="
scriptPath = resource_path()
print(f"Downloading {TRANSLATION}© from BibleGateway:", flush=True)

# Reads all books from bibleGateway and outputs to /biblegateway/bibles
multistart = time.time()
threads = []
stopEvent = threading.Event()
# signal.signal(signal.SIGINT, signalHandler)
for book in BOOKS:
    if stopEvent.is_set():
        break
    # rawBible[book] = downloadBook(book, TRANSLATION)
    thread = threading.Thread(
        target=downloadBook, args=(book, TRANSLATION), daemon=True
    )
    threads.append(thread)
    rawBible[book] = -1
    thread.start()

# thread = threading.Thread(
#     target=downloadBook, args=("Genesis", TRANSLATION), daemon=True
# )
# threads.append(thread)
# rawBible["Genesis"] = -1
# thread.start()

# try:
#     while (not downloadFinished) and (not stopEvent.is_set()):
#         time.sleep(0.1)
#         updateProgressBar()
#
# except KeyboardInterrupt:
#     print("\nKeyboard interrupt")
#     stopEvent.set()
#     sys.exit(0)

try:
    for thread in threads:
        while thread.is_alive():
            thread.join(timeout=1.0)
            if stopEvent.is_set():
                break
except KeyboardInterrupt:
    print("\nStopping Downloads...")
    stopEvent.set()
    for thread in threads:
        thread.join(timeout=2.0)
    sys.exit(1)


if not stopEvent.is_set():
    if not os.path.exists(scriptPath + "/bibles"):
        os.makedirs(scriptPath + "/bibles")

    biblePath = scriptPath + "bibles\\" + TRANSLATION + ".txt"
    print(f"\nOutputting into {biblePath}")

    with open(biblePath, "w", encoding="utf-8") as outputFile:
        for book in BOOKS:
            if book in bibleProgress:
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
