pub mod config;
pub mod generate_liturgy;
use generate_liturgy::{LiturgyGenerator, LiturgicalSeason, search_bible, Readings};
use wasm_bindgen::prelude::*;
use std::collections::HashMap;
use serde::{Deserialize, Serialize};
use chrono::{NaiveDate};

// Built in bible translations
static NABRE: &str = include_str!(concat!(env!("CARGO_MANIFEST_DIR"), "/data/bibles/NABRE.txt"));
static RSVCE: &str = include_str!(concat!(env!("CARGO_MANIFEST_DIR"), "/data/bibles/RSVCE.txt"));
static DRA: &str = include_str!(concat!(env!("CARGO_MANIFEST_DIR"), "/data/bibles/DRA.txt"));
static HWP: &str = include_str!(concat!(env!("CARGO_MANIFEST_DIR"), "/data/bibles/HWP.txt"));

#[derive(Deserialize, Serialize, Debug, Clone)]
struct LiturgyAndSeason {
    liturgy: Vec<Readings>,
    season: HashMap<String, LiturgicalSeason>,
}

#[wasm_bindgen]
pub fn wasm_generate_liturgy(date: &str, bible: &str) -> String {
    let bible = match bible {
        "NABRE" => NABRE,
        "RSVCE" => RSVCE,
        "DRA" => DRA,
        "HWP" => HWP,
        _ => "",
    };
    let year: i32 = date.split("-").next().unwrap().parse().unwrap();
    let generator = match LiturgyGenerator::new(year) {
        Ok(content) => content,
        Err(e) => {println!("Liturgy Init error: {e}"); return "".to_string();},
    };
    let (liturgy, season) = match generator.generate() {
        Ok(content) => content,
        Err(e) => {println!("Generator error: {e}"); return "".to_string();}
    };

    let mut search_liturgy = liturgy[date].clone();
    search_bible(bible, &mut search_liturgy);

    let liturgy_and_season = LiturgyAndSeason {
        liturgy: search_liturgy,
        season: season,
    };

    let serialized_liturgy = match serde_json::to_string_pretty(&liturgy_and_season) {
        Ok(liturgy) => liturgy,
        Err(e) => return "".to_string(),
    };
    println!("{}", serialized_liturgy);
    return serialized_liturgy;
}

#[cfg(test)]
mod wasm_tests {
    use super::*;

    #[test]
    fn test_generate_liturgy() {
        wasm_generate_liturgy("2025-06-29", "NABRE");
    }

}
