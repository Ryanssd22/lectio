use reqwest;
use scraper::{Html, Selector};
use regex::Regex;
use std::collections::HashMap;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::time::Duration;
use once_cell::sync::Lazy;
use colored::Colorize;
use anyhow::Result;
use tokio;
use futures::future::join_all;

// Book chapters constants
static BOOK_CHAPTERS: Lazy<HashMap<&'static str, i32>> = Lazy::new(|| {
    let mut m = HashMap::new();
    m.insert("Genesis", 50);
    m.insert("Exodus", 40);
    m.insert("Leviticus", 27);
    m.insert("Numbers", 36);
    m.insert("Deuteronomy", 34);
    m.insert("Joshua", 24);
    m.insert("Judges", 21);
    m.insert("Ruth", 4);
    m.insert("1 Samuel", 31);
    m.insert("2 Samuel", 24);
    m.insert("1 Kings", 22);
    m.insert("2 Kings", 25);
    m.insert("1 Chronicles", 29);
    m.insert("2 Chronicles", 36);
    m.insert("Ezra", 10);
    m.insert("Nehemiah", 13);
    m.insert("Esther", 10);
    m.insert("Job", 42);
    m.insert("Psalms", 150);
    m.insert("Proverbs", 31);
    m.insert("Ecclesiastes", 12);
    m.insert("Song of Solomon", 8);
    m.insert("Isaiah", 66);
    m.insert("Jeremiah", 52);
    m.insert("Lamentations", 5);
    m.insert("Ezekiel", 48);
    m.insert("Daniel", 12);
    m.insert("Hosea", 14);
    m.insert("Joel", 3);
    m.insert("Amos", 9);
    m.insert("Obadiah", 1);
    m.insert("Jonah", 4);
    m.insert("Micah", 7);
    m.insert("Nahum", 3);
    m.insert("Habakkuk", 3);
    m.insert("Zephaniah", 3);
    m.insert("Haggai", 2);
    m.insert("Zechariah", 14);
    m.insert("Malachi", 4);
    m.insert("Matthew", 28);
    m.insert("Mark", 16);
    m.insert("Luke", 24);
    m.insert("John", 21);
    m.insert("Acts", 28);
    m.insert("Romans", 16);
    m.insert("1 Corinthians", 16);
    m.insert("2 Corinthians", 13);
    m.insert("Galatians", 6);
    m.insert("Ephesians", 6);
    m.insert("Philippians", 4);
    m.insert("Colossians", 4);
    m.insert("1 Thessalonians", 5);
    m.insert("2 Thessalonians", 3);
    m.insert("1 Timothy", 6);
    m.insert("2 Timothy", 4);
    m.insert("Titus", 3);
    m.insert("Philemon", 1);
    m.insert("Hebrews", 13);
    m.insert("James", 5);
    m.insert("1 Peter", 5);
    m.insert("2 Peter", 3);
    m.insert("1 John", 5);
    m.insert("2 John", 1);
    m.insert("3 John", 1);
    m.insert("Jude", 1);
    m.insert("Revelation", 22);
    m
});

// Book abbreviations constants
pub static BOOKS: Lazy<HashMap<&'static str, &'static str>> = Lazy::new(|| {
    let mut m = HashMap::new();
    m.insert("Genesis", "Gen");
    m.insert("Exodus", "Exod");
    m.insert("Leviticus", "Lev");
    m.insert("Numbers", "Num");
    m.insert("Deuteronomy", "Deut");
    m.insert("Joshua", "Josh");
    m.insert("Judges", "Judg");
    m.insert("Ruth", "Ruth");
    m.insert("1 Samuel", "1Sam");
    m.insert("2 Samuel", "2Sam");
    m.insert("1 Kings", "1Kgs");
    m.insert("2 Kings", "2Kgs");
    m.insert("1 Chronicles", "1Chr");
    m.insert("2 Chronicles", "2Chr");
    m.insert("Ezra", "Ezra");
    m.insert("Nehemiah", "Neh");
    m.insert("Esther", "Esth");
    m.insert("Job", "Job");
    m.insert("Psalms", "Ps");
    m.insert("Proverbs", "Prov");
    m.insert("Ecclesiastes", "Eccl");
    m.insert("Song of Solomon", "Song");
    m.insert("Isaiah", "Isa");
    m.insert("Jeremiah", "Jer");
    m.insert("Lamentations", "Lam");
    m.insert("Ezekiel", "Ezek");
    m.insert("Daniel", "Dan");
    m.insert("Hosea", "Hos");
    m.insert("Joel", "Joel");
    m.insert("Amos", "Amos");
    m.insert("Obadiah", "Obad");
    m.insert("Jonah", "Jonah");
    m.insert("Micah", "Mic");
    m.insert("Nahum", "Nah");
    m.insert("Habakkuk", "Hab");
    m.insert("Zephaniah", "Zeph");
    m.insert("Haggai", "Hag");
    m.insert("Zechariah", "Zech");
    m.insert("Malachi", "Mal");
    m.insert("Matthew", "Matt");
    m.insert("Mark", "Mark");
    m.insert("Luke", "Luke");
    m.insert("John", "John");
    m.insert("Acts", "Acts");
    m.insert("Romans", "Mom");
    m.insert("1 Corinthians", "1Cor");
    m.insert("2 Corinthians", "2Cor");
    m.insert("Galatians", "Gal");
    m.insert("Ephesians", "Eph");
    m.insert("Philippians", "Phil");
    m.insert("Colossians", "Col");
    m.insert("1 Thessalonians", "1Thess");
    m.insert("2 Thessalonians", "2Thess");
    m.insert("1 Timothy", "1Tim");
    m.insert("2 Timothy", "2Tim");
    m.insert("Titus", "Titus");
    m.insert("Philemon", "Phlm");
    m.insert("Hebrews", "Heb");
    m.insert("James", "Jas");
    m.insert("1 Peter", "1Pet");
    m.insert("2 Peter", "2Pet");
    m.insert("1 John", "1John");
    m.insert("2 John", "2John");
    m.insert("3 John", "3John");
    m.insert("Jude", "Jude");
    m.insert("Revelation", "Rev");
    m
});

pub struct BibleDownloader {
    bible_progress: HashMap<String, i32>,
    raw_bible: HashMap<String, String>,
    stop_event: Arc<AtomicBool>,
}

impl BibleDownloader {
    pub fn new() -> Self {
        Self {
            bible_progress: HashMap::new(),
            raw_bible: HashMap::new(),
            stop_event: Arc::new(AtomicBool::new(false)),
        }
    }

    pub async fn download_book(
        &mut self,
        book: &str,
        translation: &str,
    ) -> Result<String> {
        let chapter_amount = *BOOK_CHAPTERS.get(book).unwrap_or(&0);
        let book_abrv = BOOKS.get(book).unwrap_or(&"").to_string();
        let biblegateway_url = "https://www.biblegateway.com/passage/?search=";
        
        let mut chapter = 1;
        let mut verse_count = 1;
        let mut output = String::new();
        
        let client = reqwest::Client::builder()
            .timeout(Duration::from_secs(5))
            .build()?;

        // Regex patterns for cleaning text
        let bracket_regex = Regex::new(r"\[.*?\]")?;
        let paren_regex = Regex::new(r"\(.*?\)")?;
        let comma_regex = Regex::new(r" ,")?;
        let period_regex = Regex::new(r" \.")?;
        let question_regex = Regex::new(r" \?")?;
        let space_regex = Regex::new(r"\s+")?;
        let verse_regex = Regex::new(r"\b(\d+)-(\d+)\b")?;

        while chapter < 200 {
            if self.stop_event.load(Ordering::Relaxed) {
                return Ok(output);
            }

            let full_url = format!(
                "{}{}+{}&version={}",
                biblegateway_url, book, chapter, translation
            );

            match client.get(&full_url).send().await {
                Ok(response) => {
                    let page_text = response.text().await?;

                    // Test if book actually exists
                    if page_text.contains("No results found.") && chapter == 1 {
                        break;
                    }

                    self.bible_progress.insert(book.to_string(), (chapter - 1).min(chapter_amount - 1));

                    // Test if data is found
                    let single_chapter_books = ["Obadiah", "Philemon", "Jude", "2 John", "3 John"];
                    if page_text.contains("No results found.") || 
                       (single_chapter_books.contains(&book) && chapter == 2) {
                        self.bible_progress.insert(book.to_string(), chapter - 1);
                        output.push('\n');
                        break;
                    }

                    if self.stop_event.load(Ordering::Relaxed) {
                        return Ok(output);
                    }

                    // Parse HTML
                    let document = Html::parse_document(&page_text);
                    let paragraph_selector = Selector::parse("p").unwrap();
                    let mut old_verse_index = String::new();

                    for paragraph in document.select(&paragraph_selector) {
                        // Find verses with class matching book abbreviation
                        let verse_selector = Selector::parse(&format!("[class*='{}']", book_abrv)).unwrap();
                        
                        for verse_element in paragraph.select(&verse_selector) {
                            let verse_html = verse_element.html();
                            let verse_doc = Html::parse_fragment(&verse_html);

                            // Remove verse numbers (sup elements with class versenum)
                            let sup_selector = Selector::parse("sup.versenum").unwrap();
                            let mut clean_html = verse_html.clone();
                            for sup in verse_doc.select(&sup_selector) {
                                clean_html = clean_html.replace(&sup.html(), "");
                            }

                            // Handle bold headers
                            let bold_selector = Selector::parse("b.inline-h3").unwrap();
                            let bold_doc = Html::parse_fragment(&clean_html);
                            for bold in bold_doc.select(&bold_selector) {
                                let bold_text = bold.text().collect::<String>();
                                clean_html = clean_html.replace(&bold.html(), &format!("*{}*", bold_text));
                            }

                            // Get clean text
                            let clean_doc = Html::parse_fragment(&clean_html);
                            let mut parsed_verse = clean_doc.root_element().text().collect::<Vec<_>>().join(" ");

                            // Clean up the text
                            parsed_verse = bracket_regex.replace_all(&parsed_verse, "").to_string();
                            parsed_verse = paren_regex.replace_all(&parsed_verse, "").to_string();
                            parsed_verse = comma_regex.replace_all(&parsed_verse, ",").to_string();
                            parsed_verse = period_regex.replace_all(&parsed_verse, ".").to_string();
                            parsed_verse = question_regex.replace_all(&parsed_verse, "?").to_string();
                            parsed_verse = space_regex.replace_all(&parsed_verse, " ").trim().to_string();

                            // Extract chapter and verse numbers from class
                            if let Some(class_attr) = verse_element.value().attr("class") {
                                for class_name in class_attr.split_whitespace() {
                                    if class_name.starts_with(&book_abrv) {
                                        if let Some(captures) = verse_regex.captures(class_name) {
                                            let chapter_num = &captures[1];
                                            let verse_num = &captures[2];
                                            let verse_index = format!("{}:{}", chapter_num, verse_num);

                                            if verse_index == old_verse_index {
                                                output.push_str(&format!(" {}", self.clean(&parsed_verse)));
                                            } else {
                                                output.push_str(&format!("\n{} {}", verse_index, self.clean(&parsed_verse)));
                                            }

                                            verse_count += 1;
                                            old_verse_index = verse_index;
                                            break;
                                        }
                                    }
                                }
                            }
                        }
                    }

                    println!("{:>13} {} - {}", "Downloading".yellow(), chapter, book);
                    chapter += 1;
                }
                Err(e) => {
                    eprintln!("Request failed: {}", e);
                    self.bible_progress.insert(book.to_string(), -1);
                    break;
                }
            }
        }

        println!("{:>13} {}", "Downloaded".green(), book);
        self.raw_bible.insert(book.to_string(), output.clone());
        Ok(output)
    }

    fn clean(&self, text: &str) -> String {
        // Removes trailing whitespace and any uncommon characters
        // Convert curly quotes to straight quotes
        text.replace("“", "\"")
            .replace("”", "\"")
            .trim()
            .to_string()
    }

    pub fn stop(&self) {
        self.stop_event.store(true, Ordering::Relaxed);
    }

    pub fn get_book(&self, book_name: &str) -> Option<&String> {
        self.raw_bible.get(book_name)
    }
    
    pub fn get_all_books(&self) -> &HashMap<String, String> {
        &self.raw_bible
    }

    pub async fn download_books_concurrent(
        &mut self,
        books: Vec<&str>,
        translation: &str,
    ) -> Result<HashMap<String, String>> {
        let mut futures = Vec::new();
        
        // Create futures for each book download
        for book in books {
            let book_owned = book.to_string();
            let translation_owned = translation.to_string();
            let stop_event = Arc::clone(&self.stop_event);
            
            let future = tokio::spawn(async move {
                let mut downloader = BibleDownloader::new();
                downloader.stop_event = stop_event;
                downloader.download_book(&book_owned, &translation_owned).await
                    .map(|content| (book_owned, content))
            });
            
            futures.push(future);
        }
        
        // Wait for all downloads to complete
        let results = join_all(futures).await;
        let mut downloaded_books = HashMap::new();
        
        for result in results {
            match result {
                Ok(Ok((book_name, content))) => {
                    downloaded_books.insert(book_name.clone(), content.clone());
                    self.raw_bible.insert(book_name, content);
                }
                Ok(Err(e)) => eprintln!("Failed to download book: {}", e),
                Err(e) => eprintln!("Task failed: {}", e),
            }
        }
        
        Ok(downloaded_books)
    }
}
