use std::fs;
use std::io;
use std::collections::HashMap;
use serde::{Deserialize};
use clap::Parser;
use chrono::prelude::*;
use chrono::NaiveDate;
use regex::Regex;
use colored::Colorize;
use inquire::Select;
// use std::path::Path;

#[derive(Deserialize, Debug, Clone)]
struct RangeEnd {
    chapter: u32,
    verse: u32,
}

#[derive(Deserialize, Debug, Clone)]
struct Verse {
    chapter: u32,
    verse: u32,
    translation: Option<String>,
    range_end: Option<RangeEnd>,
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

#[derive(Parser)]
#[command(version, about, long_about = None)]
struct Cli {
    #[arg(short, long, help = "Date of the liturgy to search")]
    date: Option<String>,

    #[arg(short, long, help = "Translation of the bible to use")]
    translation: Option<String>,

    #[arg(short, long, help = "Print all readings")]
    print_all: bool,
}

fn main() {
    let cli = Cli::parse();
    let print_all = cli.print_all;

    let date = cli.date.unwrap_or(today_date());
    let date = match valid_date(&date) {
        Ok(content) => content,
        Err(e) => {
            eprintln!("{date} date error: {e}");
            return;
        }
    };

    let translation = cli.translation.unwrap_or("NABRE".to_string());


    let year = date.split("-").next().unwrap().parse().unwrap();
    let bible = match read_bible(&translation) {
        Ok(content) => content,
        Err(e) => {
            eprintln!("{} {}: {e}", "Error reading".red(), format!("{}.txt", translation).yellow());
            return;
        }
    };

    let liturgy = match read_liturgy(year) {
        Ok(content) => content,
        Err(e) => {
            eprintln!("Error reading liturgy: {e}");
            return;
        }
    };

    let mut searched_liturgy = match parse_liturgy(&liturgy, &date) {
        Ok(content) => content,
        Err(e) => {
            eprintln!("Error parsing liturgy: {e}");
            return;
        }
    };
    search_bible(&bible, &mut searched_liturgy);

    if print_all || searched_liturgy.len() == 1{
        for readings in searched_liturgy {
            print_readings(readings, &date);
        }
    } else {
        if searched_liturgy.len() > 1 {
            println!("Multiple readings today");
            let mut reading_options = Vec::new();
            for readings in &searched_liturgy {
                reading_options.push(readings.title.clone());
            }
            let readings_ans = Select::new("Which reading?", reading_options).prompt();
            println!("You chose {}", readings_ans.unwrap());
        }
    }

}

fn print_readings(readings: Readings, date: &str) {
    println!("{}", readings.title.bold());
    println!("{}\n", date);

    print_reading(readings.first, "First Reading");
    print_reading(readings.responsal, "Responsal");
    print_reading(readings.second, "Second Reading");
    print_reading(readings.gospel, "Gospel");
}

fn valid_date(date: &String) -> Result<&String, String> {
    let re = Regex::new(r"^\d{4}-\d{2}-\d{2}$").unwrap();

    if !re.is_match(date) {
        Err("Not in correct format: YYYY-MM-DD".to_string())
    } else if !NaiveDate::parse_from_str(date, "%Y-%m-%d").is_ok() {
        Err("Date does not exist".to_string())
    } else {
        Ok(date)
    }
}

fn today_date() -> String {
    let local = Local::now();
    return local.format("%Y-%m-%d").to_string();
}

fn print_reading(reading_option: Option<Reading>, title: &str) {
    if let Some(reading) = reading_option {
        println!("{}", format!("{} {}", title.bold(), format!("({})", reading.rawReading).italic()).underline());
        // println!("{}:\n{}", title.bold(), reading.rawReading.underline());

        for (i, verses) in reading.reading.iter().enumerate() {
            if i > 1 {
                println!("Optional Verse:");
            }
            let mut full_verse = String::new();
            for verse in &verses.verses {
                if let Some(verse_translation) = &verse.translation {
                    let formatted_verse = match format_verse(verse_translation) {
                        Ok(content) => content,
                        Err(_) => verse_translation.clone(),
                    };
                    full_verse.push_str(&format!("{} ", &formatted_verse));
                } else {
                    print!("{} {}:{} not found", verses.book, &verse.chapter, &verse.verse);
                    break;
                }
            }
            let wrapped_text = textwrap::fill(&full_verse, 70);
            println!("{}\n", wrapped_text);
        }
    }
}

// Formats a verse. Bolds asterisks
fn format_verse(input: &str) -> Result<String, Box<dyn std::error::Error>> {
    let mut result = input;

    //Handles asterisks at end of verse
    let re = Regex::new(r"$\*")?;


    //Handles bolding asterisks
    let re = Regex::new(r"\*([^*]+)\*")?;
    let result = re.replace_all(result, |caps: &regex::Captures| {
        caps[1].bold().to_string() 
    }).to_string();


    Ok(result) 
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
            // println!("READINGS: {:#?}", reading);
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
        // println!("{:?}", verses);
        search_verses(bible, verses);
    }
}

fn search_verses<'a>(bible:&'a str, verses:&mut Verses) -> Vec<&'a str> {
    let book = &verses.book;
    let bible_lines: Vec<&str> = bible.lines().collect();
    let book_start = bible_lines.clone().into_iter().position(|line| line == book).unwrap_or(0);
    let mut result: Vec<&str> = Vec::new();
    let mut new_verses_vector: Vec<Verse> = Vec::new();

    for verse in &mut verses.verses {
        let chapter = verse.chapter;
        let verse_number = verse.verse;
        let chapter_number = verse.chapter;
        let mut book_index = bible_lines.iter().skip(book_start);
        // println!("Searching: {book}, {chapter}:{verse_number}");

        if let Some(range_end) = &verse.range_end {
            // println!("RANGE END: {:#?}", range_end);
            let end_chapter = range_end.chapter;
            let end_verse = range_end.verse;

            let mut start_reading = false;
            loop {
                let line = book_index.clone().collect::<Vec<&&str>>()[1];
                let line_split: Vec<&str> = line.split(':').collect();
                let current_chapter = line_split[0].parse::<u32>().unwrap(); 
                let (unparsed_current_verse, result) = line_split[1].split_once(' ').unwrap();
                // let current_verse = space_split[0].parse::<u32>().unwrap();
                let current_verse = unparsed_current_verse.parse::<u32>().unwrap();

                if current_chapter == chapter_number && current_verse == verse_number {
                    start_reading = true;
                }
                if start_reading {
                    // println!("{:#?}", result);
                    // println!("Current Chapter: {}", current_chapter);
                    // println!("Current Verse: {}", current_verse);
                    let new_verse = Verse {
                        chapter: current_chapter,
                        verse: current_verse,
                        translation: Some(result.to_string()),
                        range_end: None,
                    };
                    new_verses_vector.push(new_verse);
                }
                // let current_chapter = book_index;
                if current_chapter >= end_chapter && current_verse >= end_verse {
                    break;
                }
                book_index.next();
            }

            // println!("NEW VERSES: {:#?}", new_verses);
        } else {
            for line in book_index {
                if line.starts_with(&(chapter.to_string())) {
                    let split_text: Vec<&str> = line.split(':').collect();
                    if let Some(verse_text) = split_text.get(1) {
                        if verse_text.starts_with(&(verse_number.to_string())) {
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

    }

    if !new_verses_vector.is_empty() {
        verses.verses = new_verses_vector;
    }
    
    return result;
}


// Finds a verse from a bible
// fn find_verse(_bible:&str) {
// }

