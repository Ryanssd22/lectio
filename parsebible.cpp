#include <iostream>
#include <string>
#include <fstream>
#include <sstream>
#include <cctype>
using namespace std;

int main(int argc, char* argv[]) {
  if (argc != 2) {
    cout << "Usage: " << argv[0] << " [FILE]" << endl;
    return 1;
  }

  ifstream bible(argv[1]);
  if (!bible.is_open()) {
    cout << argv[1] << " failed to open!" << endl;
    return 1;
  }

  string line;
  string currentBook;
  string version;
  string verabbr;
  getline(bible,verabbr);
  getline(bible,version);
  cout << "Bible version: " << version << endl;
  while (getline(bible, line)) {
    string newBook;
    stringstream verse(line);
    verse >> newBook;
    if (isdigit(newBook[0])) {
      string secondTitle;
      verse >> secondTitle;
      newBook += secondTitle;
    }
    cout << "Book: " << newBook << '\n';
  }
  return 0;
}
