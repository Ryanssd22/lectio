use chrono::{Datelike, Duration, NaiveDate, Weekday};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::env;
use std::fs;
use std::path::Path;

use crate::config::get_storage_path;

// #[derive(Debug, Clone, Serialize, Deserialize)]
// pub struct Reading {
//     title: String,
//     first: String,
//     responsal: String,
//     second: String,
//     gospel: String,
//     rank: String,
// }
#[derive(Deserialize, Debug, Clone, Serialize)]
pub struct RangeEnd {
    chapter: u32,
    verse: u32,
}

#[derive(Deserialize, Debug, Clone, Serialize)]
pub struct Verse {
    chapter: u32,
    verse: u32,
    translation: Option<String>,
    range_end: Option<RangeEnd>,
}

#[derive(Deserialize, Debug, Clone, Serialize)]
pub struct Verses {
    book: String,
    verses: Vec<Verse>,
}

#[derive(Deserialize, Debug, Clone, Serialize)]
pub struct Reading {
    rawReading: String,
    reading: Vec<Verses>,
}

#[derive(Deserialize, Debug, Clone, Serialize)]
pub struct Readings {
    title: String,
    first: Option<Reading>,
    responsal: Option<Reading>,
    second: Option<Reading>,
    gospel: Option<Reading>,
    rank: Option<String>,
}

#[derive(Debug, Clone)]
struct Calendar {
    weekday_cycle: u8,
    sunday_cycle: u8,
    holy_family: NaiveDate,
    epiphany: NaiveDate,
    christmas_end: NaiveDate,
    ash_wednesday: NaiveDate,
    easter: NaiveDate,
    pentecost: NaiveDate,
    advent_start: NaiveDate,
    weeks_before_lent: u8,
    pentecost_start_ot: u8,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum LiturgicalSeason {
    Christmas,
    Ordinary,
    Lent,
    Easter,
    Advent,
}

impl LiturgicalSeason {
    fn as_str(&self) -> &'static str {
        match self {
            Self::Christmas => "CHRISTMAS",
            Self::Ordinary => "ORDINARY", 
            Self::Lent => "LENT",
            Self::Easter => "EASTER",
            Self::Advent => "ADVENT",
        }
    }
}

type LectionaryTemplate = HashMap<String, HashMap<String, Readings>>;

pub struct LiturgyGenerator {
    lectionary: LectionaryTemplate,
    calendar: Calendar,
    year: i32,
}

impl LiturgyGenerator {
    pub fn new(year: i32) -> Result<Self, Box<dyn std::error::Error>> {
        let template_path = get_storage_path().join("lectionaryTemplate.json");
        let lectionary_data = fs::read_to_string(template_path)?;
        let lectionary: LectionaryTemplate = serde_json::from_str(&lectionary_data)?;
        
        // This would normally come from readCalendar.rs equivalent
        let calendar = Self::get_calendar(year);
        
        Ok(Self {
            lectionary,
            calendar,
            year,
        })
    }

    fn get_calendar(year: i32) -> Calendar {
        // Placeholder implementation - this would be replaced with actual calendar calculation
        // from the readCalendar module equivalent
        Calendar {
            weekday_cycle: 1,
            sunday_cycle: ((year - 2021) % 3 + 1) as u8,
            holy_family: NaiveDate::from_ymd_opt(year, 12, 30).unwrap(),
            epiphany: NaiveDate::from_ymd_opt(year, 1, 6).unwrap(),
            christmas_end: NaiveDate::from_ymd_opt(year, 1, 13).unwrap(),
            ash_wednesday: NaiveDate::from_ymd_opt(year, 2, 14).unwrap(),
            easter: NaiveDate::from_ymd_opt(year, 3, 31).unwrap(),
            pentecost: NaiveDate::from_ymd_opt(year, 5, 19).unwrap(),
            advent_start: NaiveDate::from_ymd_opt(year, 11, 28).unwrap(),
            weeks_before_lent: 6,
            pentecost_start_ot: 9,
        }
    }

    fn sunday_cycle_to_char(cycle: u8) -> char {
        match cycle {
            1 => 'A',
            2 => 'B', 
            3 => 'C',
            _ => 'A',
        }
    }

    fn get_prev_saturday(mut date: NaiveDate, delta: u32) -> NaiveDate {
        for _ in 0..delta {
            date = date.pred_opt().unwrap();
            while date.weekday() != Weekday::Sat {
                date = date.pred_opt().unwrap();
            }
        }
        date
    }

    fn get_next_thursday(mut date: NaiveDate, delta: u32) -> NaiveDate {
        for _ in 0..delta {
            date = date.succ_opt().unwrap();
            while date.weekday() != Weekday::Thu {
                date = date.succ_opt().unwrap();
            }
        }
        date
    }

    fn get_next_sunday(mut date: NaiveDate) -> NaiveDate {
        date = date.succ_opt().unwrap();
        while date.weekday() != Weekday::Sun {
            date = date.succ_opt().unwrap();
        }
        date
    }

    fn date_to_lectionary_date(date: NaiveDate) -> String {
        let month = match date.month() {
            1 => "Jan",
            2 => "Feb", 
            3 => "Mar",
            4 => "Apr",
            5 => "May",
            6 => "Jun",
            7 => "Jul",
            8 => "Aug",
            9 => "Sep",
            10 => "Oct",
            11 => "Nov",
            12 => "Dec",
            _ => unreachable!(),
        };
        format!("{}{}", month, date.day())
    }

    fn get_ordinal_number(n: u32) -> String {
        let suffix = match n % 10 {
            1 if n % 100 != 11 => "st",
            2 if n % 100 != 12 => "nd", 
            3 if n % 100 != 13 => "rd",
            _ => "th",
        };
        format!("{}{}", n, suffix)
    }

    fn get_day_of_week_string(day: u32) -> &'static str {
        match day {
            0 => "Monday",
            1 => "Tuesday",
            2 => "Wednesday", 
            3 => "Thursday",
            4 => "Friday",
            5 => "Saturday",
            6 => "Sunday",
            _ => "Monday",
        }
    }

    fn determine_seasons(&self) -> HashMap<NaiveDate, LiturgicalSeason> {
        let mut seasons = HashMap::new();
        let start_date = NaiveDate::from_ymd_opt(self.year, 1, 1).unwrap();
        let end_date = NaiveDate::from_ymd_opt(self.year + 1, 1, 1).unwrap();
        
        let mut current_date = start_date;
        while current_date < end_date {
            let season = if current_date <= self.calendar.christmas_end {
                LiturgicalSeason::Christmas
            } else if current_date < self.calendar.ash_wednesday {
                LiturgicalSeason::Ordinary
            } else if current_date < self.calendar.easter - Duration::days(2) {
                LiturgicalSeason::Lent
            } else if current_date <= self.calendar.pentecost {
                LiturgicalSeason::Easter
            } else if current_date < self.calendar.advent_start {
                LiturgicalSeason::Ordinary
            } else if current_date < NaiveDate::from_ymd_opt(self.year, 12, 25).unwrap() {
                LiturgicalSeason::Advent
            } else {
                LiturgicalSeason::Christmas
            };
            
            seasons.insert(current_date, season);
            current_date = current_date.succ_opt().unwrap();
        }
        
        seasons
    }

    fn process_christmas_readings(
        &self,
        date: NaiveDate,
        liturgy: &mut HashMap<NaiveDate, Vec<Readings>>,
    ) {
        let sunday_cycle_char = Self::sunday_cycle_to_char(self.calendar.sunday_cycle);
        let christmas_lectionary = &self.lectionary["CHRISTMAS"];
        let date_search = Self::date_to_lectionary_date(date);

        liturgy.entry(date).or_insert_with(Vec::new);

        if date == NaiveDate::from_ymd_opt(self.year, 12, 25).unwrap() {
            // Christmas Day - multiple masses
            let masses = ["CHRISTMAS-VIGIL", "CHRISTMAS-NIGHT", "CHRISTMAS-DAWN", "CHRISTMAS-DAY"];
            for mass in &masses {
                if let Some(reading) = christmas_lectionary.get(*mass) {
                    liturgy.get_mut(&date).unwrap().push(reading.clone());
                }
            }
        } else if date == self.calendar.holy_family {
            // Holy Family
            let next_sunday_cycle = self.calendar.sunday_cycle % 3 + 1;
            let key_search = format!("HOLYFAMILY-{}", Self::sunday_cycle_to_char(next_sunday_cycle));
            
            if next_sunday_cycle == 1 {
                if let Some(reading) = christmas_lectionary.get(&key_search) {
                    liturgy.get_mut(&date).unwrap().push(reading.clone());
                }
            } else {
                if let Some(reading) = christmas_lectionary.get("HOLYFAMILY-A") {
                    liturgy.get_mut(&date).unwrap().push(reading.clone());
                }
                if let Some(reading) = christmas_lectionary.get(&key_search) {
                    liturgy.get_mut(&date).unwrap().push(reading.clone());
                }
            }
        } else if christmas_lectionary.contains_key(&date_search) &&
                  (date < self.calendar.epiphany || 
                   date > NaiveDate::from_ymd_opt(self.year, 12, 25).unwrap()) {
            // Christmas season days
            if let Some(reading) = christmas_lectionary.get(&date_search) {
                liturgy.get_mut(&date).unwrap().push(reading.clone());
            }
        } else if date == self.calendar.christmas_end {
            // Baptism of Our Lord
            let key_search = format!("BAPTISM-{}", sunday_cycle_char);
            if self.calendar.sunday_cycle == 1 {
                if let Some(reading) = christmas_lectionary.get("BAPTISM-A") {
                    liturgy.get_mut(&date).unwrap().push(reading.clone());
                }
            } else {
                if let Some(reading) = christmas_lectionary.get("BAPTISM-A") {
                    liturgy.get_mut(&date).unwrap().push(reading.clone());
                }
                if let Some(reading) = christmas_lectionary.get(&key_search) {
                    liturgy.get_mut(&date).unwrap().push(reading.clone());
                }
            }
        } else if date == self.calendar.epiphany {
            // Epiphany
            if let Some(reading) = christmas_lectionary.get("EPIPHANY") {
                liturgy.get_mut(&date).unwrap().push(reading.clone());
            }
        } else {
            // Days after Epiphany
            let days_from_epiphany = (date - self.calendar.epiphany).num_days();
            let key = format!("EPIPHANY-{}", days_from_epiphany);
            if let Some(reading) = christmas_lectionary.get(&key) {
                liturgy.get_mut(&date).unwrap().push(reading.clone());
            }
        }
    }

    fn process_advent_readings(
        &self,
        date: NaiveDate,
        liturgy: &mut HashMap<NaiveDate, Vec<Readings>>,
    ) {
        let sunday_cycle_char = Self::sunday_cycle_to_char(self.calendar.sunday_cycle);
        let advent_lectionary = &self.lectionary["ADVENT"];
        let day_of_week = date.weekday().num_days_from_monday() + 1;
        let weeks_since_start = ((date - self.calendar.advent_start).num_days() / 7 + 1) as u32;

        liturgy.entry(date).or_insert_with(Vec::new);

        if date.day() >= 17 && date.day() <= 24 {
            // Specific December dates
            let key_search = format!("Dec{}", date.day());
            if let Some(mut reading) = advent_lectionary.get(&key_search).cloned() {
                let title = format!(
                    "{} {} of Advent",
                    Self::get_ordinal_number(weeks_since_start),
                    Self::get_day_of_week_string((day_of_week - 1) as u32)
                );
                reading.title = title;
                liturgy.get_mut(&date).unwrap().push(reading);
            }
        } else if date.weekday() == Weekday::Sun {
            // Sundays
            let key_search = format!("{}-7-{}", weeks_since_start, sunday_cycle_char);
            if let Some(reading) = advent_lectionary.get(&key_search) {
                liturgy.get_mut(&date).unwrap().push(reading.clone());
            }
        } else {
            // Weekdays
            let key_search = format!("{}-{}", weeks_since_start, day_of_week);
            if let Some(reading) = advent_lectionary.get(&key_search) {
                liturgy.get_mut(&date).unwrap().push(reading.clone());
            }
        }
    }

    fn process_ordinary_readings(
        &self,
        date: NaiveDate,
        liturgy: &mut HashMap<NaiveDate, Vec<Readings>>,
    ) {
        let sunday_cycle_char = Self::sunday_cycle_to_char(self.calendar.sunday_cycle);
        let ordinary_lectionary = &self.lectionary["ORDINARY"];
        let day_of_week = date.weekday().num_days_from_monday() + 1;

        let weeks_since_start = if date < self.calendar.ash_wednesday {
            ((date - self.calendar.christmas_end).num_days() / 7 + 1) as u32
        } else {
            ((date - self.calendar.pentecost).num_days() / 7 + self.calendar.pentecost_start_ot as i64) as u32
        };

        let week_str = if weeks_since_start < 10 {
            format!("0{}", weeks_since_start)
        } else {
            weeks_since_start.to_string()
        };

        liturgy.entry(date).or_insert_with(Vec::new);

        if date.weekday() == Weekday::Sun {
            let key_search = format!("{}-7-{}", week_str, sunday_cycle_char);
            if let Some(mut reading) = ordinary_lectionary.get(&key_search).cloned() {
                reading.title = format!("{} Sunday of Ordinary Time", Self::get_ordinal_number(weeks_since_start));
                liturgy.get_mut(&date).unwrap().push(reading);
            }
        } else {
            let key_search = format!("{}-{}-{}", week_str, day_of_week, self.calendar.weekday_cycle);
            if let Some(reading) = ordinary_lectionary.get(&key_search) {
                liturgy.get_mut(&date).unwrap().push(reading.clone());
            }
        }
    }

    fn process_lent_readings(
        &self,
        date: NaiveDate,
        liturgy: &mut HashMap<NaiveDate, Vec<Readings>>,
    ) {
        let sunday_cycle_char = Self::sunday_cycle_to_char(self.calendar.sunday_cycle);
        let lent_lectionary = &self.lectionary["LENT"];
        let easter_lectionary = &self.lectionary["EASTER"];
        let day_of_week = date.weekday().num_days_from_monday() + 1;
        let weeks_since_ash = ((date - self.calendar.ash_wednesday + Duration::days(2)).num_days() / 7) as u32;

        liturgy.entry(date).or_insert_with(Vec::new);

        if date + Duration::days(3) == self.calendar.easter {
            // Holy Thursday
            if let Some(reading) = lent_lectionary.get("CHRISM") {
                liturgy.get_mut(&date).unwrap().push(reading.clone());
            }
            if let Some(reading) = easter_lectionary.get("0-4") {
                liturgy.get_mut(&date).unwrap().push(reading.clone());
            }
        } else if date.weekday() == Weekday::Sun {
            if weeks_since_ash + 1 == 6 {
                // Palm Sunday
                let key_search = format!("6-7-{}", sunday_cycle_char);
                if let Some(reading) = lent_lectionary.get(&format!("{}-MASS", key_search)) {
                    liturgy.get_mut(&date).unwrap().push(reading.clone());
                }
                if let Some(reading) = lent_lectionary.get(&format!("{}-PROC", key_search)) {
                    liturgy.get_mut(&date).unwrap().push(reading.clone());
                }
            } else {
                let key_search = format!("{}-7-{}", weeks_since_ash + 1, sunday_cycle_char);
                if let Some(reading) = lent_lectionary.get(&key_search) {
                    liturgy.get_mut(&date).unwrap().push(reading.clone());
                }
            }
        } else {
            let key_search = format!("{}-{}", weeks_since_ash, day_of_week);
            if let Some(reading) = lent_lectionary.get(&key_search) {
                liturgy.get_mut(&date).unwrap().push(reading.clone());
            }
        }
    }

    fn process_easter_readings(
        &self,
        date: NaiveDate,
        liturgy: &mut HashMap<NaiveDate, Vec<Readings>>,
    ) {
        let sunday_cycle_char = Self::sunday_cycle_to_char(self.calendar.sunday_cycle);
        let easter_lectionary = &self.lectionary["EASTER"];
        let day_of_week = date.weekday().num_days_from_monday() + 1;
        let weeks_since_easter = ((date - self.calendar.easter).num_days() / 7 + 1) as u32;

        liturgy.entry(date).or_insert_with(Vec::new);

        if date == self.calendar.easter - Duration::days(1) {
            // Holy Saturday
            liturgy.get_mut(&date).unwrap().push(Readings {
                title: "No Mass".to_string(),
                first: None,
                responsal: None, 
                second: None, 
                gospel: None, 
                rank: None, 
            });
        } else if date == self.calendar.easter - Duration::days(2) {
            // Good Friday
            if let Some(reading) = easter_lectionary.get("0-5") {
                liturgy.get_mut(&date).unwrap().push(reading.clone());
            }
        } else if date == self.calendar.easter {
            // Easter Sunday
            if let Some(reading) = easter_lectionary.get("0-7-VIGIL") {
                liturgy.get_mut(&date).unwrap().push(reading.clone());
            }
            if let Some(reading) = easter_lectionary.get("0-7") {
                liturgy.get_mut(&date).unwrap().push(reading.clone());
            }
        } else if date == self.calendar.pentecost {
            // Pentecost
            if let Some(reading) = easter_lectionary.get("PENTECOST-VIGIL") {
                liturgy.get_mut(&date).unwrap().push(reading.clone());
            }
            if let Some(reading) = easter_lectionary.get("PENTECOST-A") {
                liturgy.get_mut(&date).unwrap().push(reading.clone());
            }
            if self.calendar.sunday_cycle != 1 {
                let key = format!("PENTECOST-{}", sunday_cycle_char);
                if let Some(reading) = easter_lectionary.get(&key) {
                    liturgy.get_mut(&date).unwrap().push(reading.clone());
                }
            }
        } else if date.weekday() == Weekday::Sun {
            // Easter Sundays
            let key_search = format!("{}-7-{}", weeks_since_easter - 1, sunday_cycle_char);
            if let Some(reading) = easter_lectionary.get(&key_search) {
                liturgy.get_mut(&date).unwrap().push(reading.clone());
            }
            if weeks_since_easter == 6 {
                // Ascension
                let ascension_key = format!("ASCENSION-{}", sunday_cycle_char);
                if let Some(reading) = easter_lectionary.get(&ascension_key) {
                    liturgy.get_mut(&date).unwrap().insert(0, reading.clone());
                }
            }
        } else {
            // Easter Weekdays
            let key_search = format!("{}-{}", weeks_since_easter, day_of_week);
            if let Some(reading) = easter_lectionary.get(&key_search) {
                liturgy.get_mut(&date).unwrap().push(reading.clone());
            }
        }
    }

    fn process_solemnities(&self, liturgy: &mut HashMap<NaiveDate, Vec<Readings>>) {
        let sunday_cycle_char = Self::sunday_cycle_to_char(self.calendar.sunday_cycle);
        let solemnity_lectionary = &self.lectionary["SOLEMNITY"];
        
        let trinity_sunday = Self::get_next_sunday(self.calendar.pentecost);
        let body_blood = Self::get_next_sunday(trinity_sunday);
        let sacred_heart = body_blood + Duration::days(5);
        let start_holy_week = self.calendar.easter - Duration::days(6);

        // Major moveable solemnities
        if let Some(reading) = solemnity_lectionary.get(&format!("TrinSun-{}", sunday_cycle_char)) {
            liturgy.entry(trinity_sunday).or_insert_with(Vec::new).insert(0, reading.clone());
        }
        if let Some(reading) = solemnity_lectionary.get(&format!("BodyBlood-{}", sunday_cycle_char)) {
            liturgy.entry(body_blood).or_insert_with(Vec::new).insert(0, reading.clone());
        }
        if let Some(reading) = solemnity_lectionary.get(&format!("SacHeart-{}", sunday_cycle_char)) {
            liturgy.entry(sacred_heart).or_insert_with(Vec::new).insert(0, reading.clone());
        }

        // Fixed solemnities with special handling
        let dates_to_check = [
            (3, 19, "Mar19"), // St. Joseph
            (3, 25, "Mar25"), // Annunciation
            (6, 24, "Jun24"), // St. John the Baptist
            (12, 8, "Dec8"),  // Immaculate Conception
        ];

        for (month, day, key) in &dates_to_check {
            if let Some(solemnity_date) = NaiveDate::from_ymd_opt(self.year, *month, *day) {
                let mut actual_date = solemnity_date;
                
                match key {
                    &"Mar19" => {
                        // St. Joseph - move if conflicts with Holy Week
                        if start_holy_week < solemnity_date && solemnity_date < self.calendar.easter {
                            actual_date = Self::get_prev_saturday(solemnity_date, 1);
                        } else if solemnity_date.weekday() == Weekday::Sun && 
                                 matches!(liturgy.get(&solemnity_date).map(|v| v.is_empty()).unwrap_or(true), false) {
                            actual_date = solemnity_date + Duration::days(1);
                        }
                    },
                    &"Mar25" => {
                        // Annunciation - complex moving rules
                        if solemnity_date.weekday() == Weekday::Sun {
                            actual_date = NaiveDate::from_ymd_opt(self.year, 3, 26).unwrap();
                        }
                        if start_holy_week <= actual_date && actual_date < Self::get_next_sunday(self.calendar.easter) {
                            actual_date = self.calendar.easter + Duration::days(8);
                        }
                    },
                    &"Jun24" => {
                        // St. John the Baptist - move if conflicts with Sacred Heart
                        if solemnity_date == sacred_heart {
                            actual_date = NaiveDate::from_ymd_opt(self.year, 6, 23).unwrap();
                        }
                        // This one has both vigil and day masses
                        if let Some(vigil_reading) = solemnity_lectionary.get("Jun24-VIGIL") {
                            liturgy.entry(actual_date).or_insert_with(Vec::new).insert(0, vigil_reading.clone());
                        }
                    },
                    &"Dec8" => {
                        // Immaculate Conception - move if Sunday in Advent
                        if solemnity_date.weekday() == Weekday::Sun {
                            actual_date = NaiveDate::from_ymd_opt(self.year, 12, 9).unwrap();
                        }
                    },
                    _ => {}
                }

                if let Some(reading) = solemnity_lectionary.get(*key) {
                    liturgy.entry(actual_date).or_insert_with(Vec::new).insert(0, reading.clone());
                }
            }
        }

        // Other fixed solemnities
        for (date_str, reading) in solemnity_lectionary {
            if let Ok(parsed_date) = Self::parse_lectionary_date_to_date(date_str, self.year) {
                // Skip already handled dates
                if ["Mar19", "Mar25", "Jun24", "Dec8"].contains(&date_str.as_str()) ||
                   date_str.contains("TrinSun") || date_str.contains("BodyBlood") || date_str.contains("SacHeart") {
                    continue;
                }

                if date_str.ends_with("-VIGIL") {
                    if let Some(base_reading) = solemnity_lectionary.get(&date_str.replace("-VIGIL", "")) {
                        let readings = liturgy.entry(parsed_date).or_insert_with(Vec::new);
                        readings.insert(0, base_reading.clone());
                        readings.insert(0, reading.clone());
                    }
                } else if !solemnity_lectionary.contains_key(&format!("{}-VIGIL", date_str)) {
                    liturgy.entry(parsed_date).or_insert_with(Vec::new).insert(0, reading.clone());
                }
            }
        }
    }

    fn process_saints(&self, liturgy: &mut HashMap<NaiveDate, Vec<Readings>>) {
        let saint_lectionary = &self.lectionary["SAINTPROPER"];
        
        // Add Thanksgiving
        let thanksgiving = Self::get_next_thursday(
            NaiveDate::from_ymd_opt(self.year, 10, 31).unwrap(), 
            4
        );
        if let Some(reading) = saint_lectionary.get("THANKSGIVING") {
            liturgy.entry(thanksgiving).or_insert_with(Vec::new).push(reading.clone());
        }

        // Process all saint days
        for (date_str, reading) in saint_lectionary {
            if date_str == "THANKSGIVING" {
                continue; // Already handled
            }

            if let Ok(saint_date) = Self::parse_lectionary_date_to_date(date_str, self.year) {
                let day_of_week = saint_date.weekday();
                
                if day_of_week == Weekday::Sun || reading.rank.clone().unwrap_or(String::new()).contains("Opt") {
                    liturgy.entry(saint_date).or_insert_with(Vec::new).push(reading.clone());
                } else {
                    liturgy.entry(saint_date).or_insert_with(Vec::new).insert(0, reading.clone());
                }
            }
        }
    }

    fn parse_lectionary_date_to_date(date_str: &str, year: i32) -> Result<NaiveDate, Box<dyn std::error::Error>> {
        if date_str.len() < 4 {
            return Err("Invalid date string".into());
        }

        let month_str = &date_str[..3];
        let day_str = &date_str[3..].chars().take_while(|c| c.is_ascii_digit()).collect::<String>();
        
        let month = match month_str {
            "Jan" => 1, "Feb" => 2, "Mar" => 3, "Apr" => 4,
            "May" => 5, "Jun" => 6, "Jul" => 7, "Aug" => 8,
            "Sep" => 9, "Oct" => 10, "Nov" => 11, "Dec" => 12,
            _ => return Err("Invalid month".into()),
        };

        let day: u32 = day_str.parse()?;
        NaiveDate::from_ymd_opt(year, month, day)
            .ok_or_else(|| "Invalid date".into())
    }

    pub fn generate(&self) -> Result<(HashMap<String, Vec<Readings>>, HashMap<String, LiturgicalSeason>), Box<dyn std::error::Error>> {
        let seasons = self.determine_seasons();
        let mut liturgy: HashMap<NaiveDate, Vec<Readings>> = HashMap::new();

        // Process each day according to its season
        for (&date, &season) in &seasons {
            match season {
                LiturgicalSeason::Christmas => self.process_christmas_readings(date, &mut liturgy),
                LiturgicalSeason::Advent => self.process_advent_readings(date, &mut liturgy),
                LiturgicalSeason::Ordinary => self.process_ordinary_readings(date, &mut liturgy),
                LiturgicalSeason::Lent => self.process_lent_readings(date, &mut liturgy),
                LiturgicalSeason::Easter => self.process_easter_readings(date, &mut liturgy),
            }
        }

        // Process solemnities and saints
        self.process_solemnities(&mut liturgy);
        self.process_saints(&mut liturgy);

        // Convert to string keys for JSON serialization
        let parsed_liturgy: HashMap<String, Vec<Readings>> = liturgy
            .into_iter()
            .map(|(date, readings)| (date.format("%Y-%m-%d").to_string(), readings))
            .collect();

        let parsed_seasons: HashMap<String, LiturgicalSeason> = seasons
            .into_iter()
            .map(|(date, season)| (date.format("%Y-%m-%d").to_string(), season))
            .collect();

        Ok((parsed_liturgy, parsed_seasons))
    }

    pub fn save_to_files(&self) -> Result<(), Box<dyn std::error::Error>> {
        let (liturgy, seasons) = self.generate()?;
        
        // Create output directory
        let liturgy_folder = get_storage_path().join("liturgies");
        std::fs::create_dir_all(&liturgy_folder)?;
        
        // Save liturgy
        let liturgy_json = serde_json::to_string_pretty(&liturgy)?;
        std::fs::write(&liturgy_folder.join(format!("liturgy{}.json", self.year)), &liturgy_json)?;
        println!("{}", liturgy_json);
        
        // Save seasons
        let seasons_json = serde_json::to_string_pretty(&seasons)?;
        std::fs::write(format!("./liturgies/liturgy{}season.json", self.year), &seasons_json)?;
        
        Ok(())
    }
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = env::args().collect();
    let year = if args.len() < 2 {
        chrono::Utc::now().year()
    } else {
        args[1].parse::<i32>()?
    };

    let generator = LiturgyGenerator::new(year)?;
    generator.save_to_files()?;
    
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_sunday_cycle_conversion() {
        assert_eq!(LiturgyGenerator::sunday_cycle_to_char(1), 'A');
        assert_eq!(LiturgyGenerator::sunday_cycle_to_char(2), 'B');
        assert_eq!(LiturgyGenerator::sunday_cycle_to_char(3), 'C');
    }

    #[test]
    fn test_date_to_lectionary_date() {
        let date = NaiveDate::from_ymd_opt(2024, 3, 15).unwrap();
        assert_eq!(LiturgyGenerator::date_to_lectionary_date(date), "Mar15");
    }

    #[test]
    fn test_ordinal_numbers() {
        assert_eq!(LiturgyGenerator::get_ordinal_number(1), "1st");
        assert_eq!(LiturgyGenerator::get_ordinal_number(2), "2nd");
        assert_eq!(LiturgyGenerator::get_ordinal_number(3), "3rd");
        assert_eq!(LiturgyGenerator::get_ordinal_number(4), "4th");
        assert_eq!(LiturgyGenerator::get_ordinal_number(11), "11th");
        assert_eq!(LiturgyGenerator::get_ordinal_number(21), "21st");
    }

    #[test]
    fn test_parse_lectionary_date() {
        let result = LiturgyGenerator::parse_lectionary_date_to_date("Mar15", 2024);
        assert!(result.is_ok());
        assert_eq!(result.unwrap(), NaiveDate::from_ymd_opt(2024, 3, 15).unwrap());
    }
}

// Additional helper functions that might be needed for the calendar module

pub mod calendar_utils {
    use chrono::{NaiveDate, Datelike};

    /// Calculate Easter date using the algorithm for Gregorian calendar
    pub fn calculate_easter(year: i32) -> NaiveDate {
        let a = year % 19;
        let b = year / 100;
        let c = year % 100;
        let d = b / 4;
        let e = b % 4;
        let f = (b + 8) / 25;
        let g = (b - f + 1) / 3;
        let h = (19 * a + b - d - g + 15) % 30;
        let i = c / 4;
        let k = c % 4;
        let l = (32 + 2 * e + 2 * i - h - k) % 7;
        let m = (a + 11 * h + 22 * l) / 451;
        let n = (h + l - 7 * m + 114) / 31;
        let p = (h + l - 7 * m + 114) % 31;
        
        NaiveDate::from_ymd_opt(year, n as u32, (p + 1) as u32).unwrap()
    }

    /// Calculate Ash Wednesday (46 days before Easter)
    pub fn calculate_ash_wednesday(easter: NaiveDate) -> NaiveDate {
        easter - chrono::Duration::days(46)
    }

    /// Calculate Pentecost (49 days after Easter)
    pub fn calculate_pentecost(easter: NaiveDate) -> NaiveDate {
        easter + chrono::Duration::days(49)
    }

    /// Calculate first Sunday of Advent (4 Sundays before Christmas)
    pub fn calculate_advent_start(year: i32) -> NaiveDate {
        let christmas = NaiveDate::from_ymd_opt(year, 12, 25).unwrap();
        let mut advent_start = christmas;
        
        // Go back to find the 4th Sunday before
        for _ in 0..4 {
            advent_start = advent_start - chrono::Duration::days(1);
            while advent_start.weekday() != chrono::Weekday::Sun {
                advent_start = advent_start - chrono::Duration::days(1);
            }
        }
        
        advent_start
    }

    /// Determine the Sunday cycle (A, B, C) based on the year
    pub fn calculate_sunday_cycle(year: i32) -> u8 {
        // Year A begins with Advent in the year before a year divisible by 3
        // Year B begins with Advent in the year before a year that leaves remainder 1 when divided by 3
        // Year C begins with Advent in the year before a year that leaves remainder 2 when divided by 3
        ((year - 1) % 3 + 1) as u8
    }
}
