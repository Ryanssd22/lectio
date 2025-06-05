use std::fs::File;
use std::io::{self, BufRead};
// use std::path::Path;

fn main() {
    read_bible("NABRE")
}

fn read_bible(translation:&str) {
    let bible_path = format!("./biblegateway/bibles/{translation}.txt");

    if let Ok(file) = File::open(bible_path) {
        let reader = io::BufReader::new(file);
        for line in reader.lines() {
            match line {
                Ok(content) => println!("{content}"),
                Err(e) => println!("Error reading line: {e}")
            }
        }
    } else {
        println!("Failed to open file");
    }
}