use std::fs;
use std::io;
use std::io::Write;
use std::env;
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::collections::HashMap;
use serde::{Deserialize};
use clap::{Parser, Subcommand, CommandFactory};
use chrono::prelude::*;
use chrono::NaiveDate;
use regex::Regex;
use colored::Colorize;
use inquire::{Select, ui::{RenderConfig, Styled, Color, StyleSheet}};

mod biblescrape;
use biblescrape::BibleDownloader;

mod config;
use crate::config::get_storage_path;

mod generateLiturgy;
use generateLiturgy::{LiturgyGenerator, LiturgicalSeason};

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

#[derive(Parser, Debug)]
#[command(version, about, long_about = None)]
struct Cli {
    #[arg(short, long, help = "Date of the liturgy to search")]
    date: Option<String>,

    #[arg(short, long, help = "Translation of the bible to use")]
    translation: Option<String>,

    #[arg(short, long, help = "Print all readings")]
    print_all: bool,

    #[arg(short, long, help = "Outputs all JSON (Can specify a date (-d) and translation (-t))")]
    json: bool,

    #[command(subcommand)]
    command: Option<Commands>,
}

#[derive(Subcommand, Debug)]
enum Commands {
    Install {
        #[arg()]
        translation: String,
    },
}

fn main() {
    let cli = Cli::parse();
    match &cli.command {
        Some(Commands::Install {translation}) => {
            let rt = match tokio::runtime::Runtime::new() {
                Ok(content) => content,
                Err(e) => {
                    eprintln!("Async error: {e}");
                    return;
                }
            };
            rt.block_on(run_bible_scrape(&translation.to_uppercase()));
        }
        None => {run_lectio();}
    };
}

async fn run_bible_scrape(translation: &str) -> Result<(), Box<dyn std::error::Error>>{
    let mut downloader = BibleDownloader::new();

    let mut books = Vec::new();
    for (book, _) in &*biblescrape::BOOKS {
        books.push(*book);
    }
    let results = downloader.download_books_concurrent(books, translation).await?;

    let mut bible_string = String::new();
    for (book, text) in results {
        if text != "" {
            bible_string.push_str(&book.to_uppercase());
            bible_string.push_str(&text);
        }
    }

    let bibles_path = get_storage_path().join("bibles/");
    fs::create_dir_all(&bibles_path);
    let file_path = bibles_path.join(format!("{}.txt", translation));
    fs::write(&file_path, bible_string);

    println!("Saved in {:#?}", bibles_path);
    Ok(())
}

fn has_python() -> bool {
    Command::new("python")
        .arg("--version")
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .status()
        .map(|status| status.success())
        .unwrap_or(false)
}

fn run_lectio() {
    let cli = Cli::parse();
    let cli_command = Cli::command();
    let executable_name = cli_command.get_name();
    let print_all = cli.print_all;
    let json = cli.json;

    let date = cli.date.unwrap_or(today_date());
    let date = match valid_date(&date) {
        Ok(content) => content,
        Err(e) => {
            eprintln!("{date} date error: {e}");
            return;
        }
    };

    let translation = cli.translation.unwrap_or("NABRE".to_string());

    let year: i32 = date.split("-").next().unwrap().parse().unwrap();

    // let liturgy = match read_liturgy(year) {
    //     Ok(content) => content,
    //     Err(e) => {
    //         // eprintln!("Error reading liturgy: {e}");
    //         match generate_liturgy(year) {
    //             Ok(content) => {content},
    //             Err(e) => {
    //                 eprintln!("{e}");
    //                 return;
    //             }
    //         }
    //     }
    // };


    let (liturgy, season) = match generate_liturgy(year) {
        Ok(content) => {content},
        Err(e) => {
            eprintln!("Liturgy couldn't be generated: {e}");
            return;
        }
    };

    let season = season.get(date).unwrap();

    // let season = match search_season(date) {
    //     Ok(content) => content,
    //     Err(_) => "N/A".to_string(),
    // };

    let bible = match read_bible(&translation) {
        Ok(content) => content,
        Err(e) => {
            eprintln!("{} {}: {e}", "Error reading".red(), format!("{}.txt", translation).yellow());
            eprintln!("To install {translation}, run:");
            eprintln!("{}", format!("\t{} install {translation}", executable_name).bold());
            return;
        }
    };

    // println!("Your liturgy: {}", liturgy);

    if json {
        let mut liturgy_json: HashMap<String, Vec<Readings>> = serde_json::from_str(&liturgy).expect("N/A");
        for (date, liturgy) in &mut liturgy_json {
            // println!("{:#?}", liturgy);
            // print!(".");
            search_bible(&bible, liturgy);
        }
        println!("{:#?}", liturgy_json);
    } else {
        let mut searched_liturgy = match parse_liturgy(&liturgy, &date) {
            Ok(content) => content,
            Err(e) => {
                eprintln!("Error parsing liturgy: {e}");
                return;
            }
        };
        search_bible(&bible, &mut searched_liturgy);

        if print_all || searched_liturgy.len() == 1 {
            for readings in searched_liturgy {
                print_readings(readings, &date, season);
            }
        } else {
            if searched_liturgy.len() > 1 {
                let mut reading_options = Vec::new();
                for readings in &searched_liturgy {
                    reading_options.push(readings.title.clone());
                }
                let mut select_config = RenderConfig::default();
                select_config.help_message = StyleSheet::default().with_fg(Color::DarkGreen);
                select_config.selected_option = Some(StyleSheet::default().with_fg(Color::DarkGreen));
                select_config.answer = StyleSheet::default().with_fg(Color::DarkGreen);

                let readings_ans = match Select::new("Which reading?", reading_options.clone())
                    .with_help_message("Use ↑↓ arrows to navigate")
                    .with_render_config(select_config)
                    .prompt() {
                    Ok(content) => content,
                    Err(_) => {
                        println!("{}", "Selection canceled".red());
                        return;
                    }
                };
                let selected_index = reading_options.iter().position(|title| title == &readings_ans).unwrap();
                print_readings(searched_liturgy[selected_index].clone(), &date, season);
            }
        }
    }
}

fn search_season(date: &str) -> Result<String, String> {
    let year: String = date.chars().take(4).collect();
    // let liturgy_season_path = format!("./liturgies/liturgy{}season.json", year); 
    let liturgy_season_path = get_storage_path().join("liturgies").join(format!("liturgy{}season.json", year));
    let liturgy_season_str= match fs::read_to_string(&liturgy_season_path) {
        Ok(content) => content,
        Err(e) => return Err(format!("Failed to read file: {}", e)),
    };
    let liturgy_season_json: HashMap<String, String> = match serde_json::from_str(&liturgy_season_str) {
        Ok(content) => content,
        Err(e) => return Err(format!("Failed to parse json: {}", e)),
    };
    let season = liturgy_season_json.get(date);
    if season.is_none() {
        return Err(format!("Date not found in {}", &liturgy_season_path.display()));
    }
    return Ok(season.unwrap().to_string());
}

fn generate_liturgy(year: i32) -> Result<(String, HashMap<String, LiturgicalSeason>), Box<dyn std::error::Error>> {
    let generator = LiturgyGenerator::new(year)?;
    let (liturgy, season) = generator.generate()?;

    let liturgy_string = serde_json::to_string(&liturgy).unwrap();

    Ok((liturgy_string, season))
}

fn print_readings(readings: Readings, date: &str, season: &LiturgicalSeason) {
    println!("{} ({})\n", parse_season_string(&readings.title, season), date);

    print_reading(readings.first, "First Reading", season);
    print_reading(readings.responsal, "Responsal", season);
    print_reading(readings.second, "Second Reading", season);
    print_reading(readings.gospel, "Gospel", season);
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

fn print_reading(reading_option: Option<Reading>, title: &str, season: &LiturgicalSeason) {
    if let Some(reading) = reading_option {
        let formatted_title = &format!("{} {}", title.bold(), format!("({})", reading.rawReading).italic()).underline();
        println!("{}", formatted_title);
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

fn parse_season_string(string: &str, season: &LiturgicalSeason) -> String {
    let formatted_string = match season {
        LiturgicalSeason::Ordinary => string.green(),
        LiturgicalSeason::Christmas => string.white(),
        LiturgicalSeason::Lent => string.purple(),
        LiturgicalSeason::Easter => string.yellow(),
        LiturgicalSeason::Advent => string.purple(), 
        _ => string.red(),
    };
    formatted_string.bold().to_string()
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
    // let bible_path = format!("./python/bibles/{translation}.txt");
    let bible_path = get_storage_path().join(format!("bibles/{translation}.txt"));
    fs::read_to_string(bible_path)
}

// Reads a date in a liturgy and parses it into a struct
fn read_liturgy(year:i32) -> Result<String, std::io::Error> {
    // let liturgy_path = format!("./liturgies/liturgy{}.json",year);
    let liturgy_path = get_storage_path().join("liturgies").join(format!("liturgy{}.json", year));
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
    let book_start = match bible_lines.clone().into_iter().position(|line| line == book) {
        Some(content) => content,
        None => {return Vec::new();},
    };
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
                // println!("{line}");
                let line_split: Vec<&str> = line.split(':').collect();
                let current_chapter = line_split[0].parse::<u32>().unwrap_or(0); 
                if current_chapter == 0 {break;}
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
    // println!("{:#?}", result);
    
    return result;
}

fn get_os() -> String {
    if cfg!(target_os = "windows") {
        "windows".to_string()
    } else if cfg!(target_os = "macos") {
        "macos".to_string()
    } else if cfg!(target_os = "linux") {
        "linux".to_string()
    } else {
        "unknown".to_string()
    }
}


