use std::fs;
use std::io;
use std::env;
use std::collections::HashMap;
use serde::{Deserialize, Serialize};
// use std::path::Path;

#[derive(Deserialize, Debug, Clone)]
struct Verse {
    chapter: u32,
    verse: u32,
    translation: Option<String>,
}

#[derive(Deserialize, Debug, Clone)]
struct Verses {
    book: String,
    verses: Vec<Verse>,
}

#[derive(Deserialize, Debug, Clone)]
struct Reading {
    rawReading: String,
    reading: Vec<Verses>,
}

#[derive(Deserialize, Debug, Clone)]
struct Readings {
    title: String,
    first: Option<Reading>,
    responsal: Option<Reading>,
    second: Option<Reading>,
    gospel: Option<Reading>,
    rank: Option<String>,
}

fn main() {
    // let args: Vec<String> = env::args().collect();

    // let year = args[1].split("-").next().unwrap().parse().unwrap();
    let bible = match read_bible("NABRE") {
        Ok(content) => content,
        Err(e) => {
            eprintln!("Error reading file: {e}");
            return;
        }
    };

    let liturgy = match read_liturgy(2025) {
        Ok(content) => content,
        Err(e) => {
            eprintln!("Error reading liturgy: {e}");
            return;
        }
    };

    let mut searched_liturgy = match parse_liturgy(&liturgy, "2025-06-06") {
        Ok(content) => content,
        Err(e) => {
            eprintln!("Error parsing liturgy: {e}");
            return;
        }
    };
    search_bible(&bible, &mut searched_liturgy);

    for readings in searched_liturgy {
        println!("\n{}:", readings.title);

        print_reading(readings.first, "First Reading");
        print_reading(readings.responsal, "Responsal");
        print_reading(readings.second, "Second Reading");
        print_reading(readings.gospel, "Gospel");
    }
}

fn print_reading(reading_option: Option<Reading>, title: &str) {
    if let Some(reading) = reading_option {
        println!("{}:\n{}", title, reading.rawReading);

        for verses in reading.reading {
            for verse in verses.verses {
                if let Some(verse_translation) = verse.translation {
                    print!("{} ", verse_translation);
                }
            }
        }
    }
    println!();
}

// Reads a bible.txt
fn read_bible(translation:&str) -> io::Result<String> {
    let bible_path = format!("../biblegateway/bibles/{translation}.txt");
    fs::read_to_string(bible_path)
}

// Reads a date in a liturgy and parses it into a struct
fn read_liturgy(year:u32) -> Result<String, std::io::Error> {
    let liturgy_path = format!("../liturgies/liturgy{}.json",year);
    fs::read_to_string(liturgy_path)
}

// Reads in liturgy string and parses it into rust structs
fn parse_liturgy(liturgy_str:&str, date:&str) -> Result<Vec<Readings>, Box<dyn std::error::Error>> {
    let liturgy: HashMap<String, Vec<Readings>> = serde_json::from_str(liturgy_str)?;

    liturgy.get(date)
        .cloned()
        .ok_or_else(|| format!("Date '{}' not found in liturgy", date).into())
}

// Searches bible for verses to complete Liturgy 
fn search_bible(bible:&str, liturgy:&mut Vec<Readings>) {
    for readings in liturgy {
        if let Some(reading) = &mut readings.first {
            search_reading(bible, reading);
        }
        if let Some(reading) = &mut readings.responsal {
            search_reading(bible, reading);
        }
        if let Some(reading) = &mut readings.second {
            search_reading(bible, reading);
        }
        if let Some(reading) = &mut readings.gospel {
            search_reading(bible, reading);
        }
    }
}

// Searches bible for verses to complete Reading
fn search_reading(bible:&str, reading:&mut Reading) {
    for verses in &mut reading.reading {
        let verses_text = search_verses(bible, verses);
        // println!("{:?}", verses);
    }
}

fn search_verses<'a>(bible:&'a str, verses:&mut Verses) -> Vec<&'a str> {
    let book = &verses.book;
    let bible_lines: Vec<&str> = bible.lines().collect();
    let book_start = bible_lines.clone().into_iter().position(|line| line == book).unwrap_or(0);
    let mut result: Vec<&str> = Vec::new();

    for verse in &mut verses.verses {
        let chapter = verse.chapter;
        let verse_number = verse.verse;
        let book_index = bible_lines.iter().skip(book_start);
        // println!("Searching: {book}, {chapter}:{verse_number}");

        for line in book_index {
            if line.starts_with(&(chapter.to_string())) {
                let split_text: Vec<&str> = line.split(':').collect();
                if let Some(chapter_text) = split_text.get(1) {
                    if chapter_text.starts_with(&(verse_number.to_string())) {
                        let space_split = line.split_once(' ');
                        let (_, verse_text) = space_split.unwrap_or(("", ""));
                        result.push(verse_text);

                        verse.translation = Some(verse_text.to_string());
                        break;
                    }
                }
            }
        }

    }
    
    return result;
}


// Finds a verse from a bible
// fn find_verse(_bible:&str) {
// }

