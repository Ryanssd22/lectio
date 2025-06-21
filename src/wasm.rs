pub mod config;
pub mod generate_liturgy;
use generate_liturgy::{LiturgyGenerator, LiturgicalSeason, search_bible};

// Built in bible translations
static NABRE: &str = include_str!(concat!(env!("CARGO_MANIFEST_DIR"), "/data/bibles/NABRE.txt"));
static RSVCE: &str = include_str!(concat!(env!("CARGO_MANIFEST_DIR"), "/data/bibles/RSVCE.txt"));
static DRA: &str = include_str!(concat!(env!("CARGO_MANIFEST_DIR"), "/data/bibles/DRA.txt"));
static HWP: &str = include_str!(concat!(env!("CARGO_MANIFEST_DIR"), "/data/bibles/HWP.txt"));

pub fn wasm_generate_liturgy(date: &str, bible: &str) {
    let year: i32 = date.split("-").next().unwrap().parse().unwrap();
    let generator = match LiturgyGenerator::new(year) {
        Ok(content) => content,
        Err(e) => {println!("Liturgy Init error: {e}"); return;},
    };
    let (liturgy, season) = match generator.generate() {
        Ok(content) => content,
        Err(e) => {println!("Generator error: {e}"); return;}
    };

    let mut search_liturgy = liturgy[date].clone();
    search_bible(bible, &mut search_liturgy);
    println!("{:#?}", search_liturgy);
}

#[cfg(test)]
mod wasm_tests {
    use super::*;

    #[test]
    fn test_generate_liturgy() {
        wasm_generate_liturgy("2025-06-21", HWP);
    }
}
