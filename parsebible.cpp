#include <iostream>
#include <string>
#include <fstream>
#include <sstream>
#include <cctype>
#include <algorithm>
using namespace std;

int main(int argc, char* argv[]) {
  if (argc != 2) {
    cout << "Usage: " << argv[0] << " [FILE]";
    return 1;
  }

  ifstream bible(argv[1]);
  if (!bible.is_open()) {
    cout << argv[1] << " failed to open!" << endl;
    return 1;
  }

  string line, currentBook = "", version, verabbr;

  getline(bible, verabbr);
  getline(bible,version);
  cout << "Bible version: " << version << endl;
  ofstream bibleOutput(verabbr + ".txt");
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
    transform(newBook.begin(), newBook.end(), newBook.begin(), ::toupper);
    if (currentBook != newBook) {
      if (!currentBook.empty()) {
        //cout << '^' << '\n';
        bibleOutput << '^' << '\n'; 
      }
      //cout << newBook << '\n';
      bibleOutput << newBook << '\n';
    }

    //Reads chapter:verse
    int chapter, verseNumber;
    char colon;
    verse >> chapter >> colon >> verseNumber;
    //cout << chapter << ":" << verseNumber << " ";
    bibleOutput << chapter << ":" << verseNumber << " ";

    //Reads verse
    string fullVerse;
    getline(verse, fullVerse);
    //cout << fullVerse << '\n';
    bibleOutput << fullVerse << '\n';

    currentBook = newBook;
  }

  bibleOutput.close();
  bible.close();
  return 0;
}
