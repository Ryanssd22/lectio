use std::path::PathBuf;

pub fn get_storage_path() -> PathBuf {
    if cfg!(debug_assertions) {
        PathBuf::from("./data")
    } else {
        dirs::data_dir()
            .unwrap_or_else(|| PathBuf::from("."))
            .join(env!("CARGO_PKG_NAME"))
    }
}
