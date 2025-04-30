#include <iostream>
#include <string>
#include <fstream>
#include <sstream>
#include <cctype>
using namespace std;

int main(int argc, char* argv[]) {
  if (argc != 5) {
    cout << "Usage: " << argv[0] << " [FILE] [BOOK] [CHAPTER] [VERSE]" << endl;
    return 1;
  }

  ifstream bible(argv[1]);
  if (!bible.is_open()) {
    cout << argv[1] << " failed to open!" << endl;
    return 1;
  }

  string inputBook = argv[2];
  int inputChapter = stoi(argv[3]);
  int inputVerse = stoi(argv[4]);
  string line, currentBook, version, verabbr;

  getline(bible,verabbr);
  getline(bible,version);
  cout << "Bible version: " << version << endl;
  while (getline(bible, line)) {
    //Reads book
    string newBook;
    stringstream verse(line);
    verse >> newBook;
    if (isdigit(newBook[0])) {
      string secondTitle;
      verse >> secondTitle;
      newBook += secondTitle;
    }
    //if (currentBook != newBook) cout << "Book: " << newBook << '\n';
    currentBook = newBook;

    if (currentBook == inputBook) {
      //Reads chapter:verse
      int chapter, verseNumber;
      char colon;
      verse >> chapter >> colon >> verseNumber;
      //cout << chapter << ":" << verseNumber << '\t';

      if (chapter == inputChapter && verseNumber == inputVerse) {
        //Reads verse
        string fullVerse;
        getline(verse, fullVerse);
        cout << fullVerse << endl;
      }
    }
  }
  return 0;
}
