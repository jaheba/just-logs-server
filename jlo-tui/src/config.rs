use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use std::path::PathBuf;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    pub server_url: String,
    #[serde(default)]
    pub username: Option<String>,
    #[serde(default)]
    pub ui: UiConfig,
    #[serde(default)]
    pub colors: ColorConfig,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UiConfig {
    #[serde(default = "default_refresh_interval")]
    pub refresh_interval_ms: u64,
    #[serde(default = "default_page_size")]
    pub page_size: usize,
    #[serde(default = "default_max_logs")]
    pub max_logs_in_memory: usize,
    #[serde(default = "default_date_format")]
    pub date_format: String,
    #[serde(default = "default_true")]
    pub enable_colors: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ColorConfig {
    #[serde(default = "default_error_color")]
    pub error: String,
    #[serde(default = "default_warn_color")]
    pub warn: String,
    #[serde(default = "default_info_color")]
    pub info: String,
    #[serde(default = "default_debug_color")]
    pub debug: String,
    #[serde(default = "default_fatal_color")]
    pub fatal: String,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            server_url: "http://localhost:8000".to_string(),
            username: None,
            ui: UiConfig::default(),
            colors: ColorConfig::default(),
        }
    }
}

impl Default for UiConfig {
    fn default() -> Self {
        Self {
            refresh_interval_ms: default_refresh_interval(),
            page_size: default_page_size(),
            max_logs_in_memory: default_max_logs(),
            date_format: default_date_format(),
            enable_colors: default_true(),
        }
    }
}

impl Default for ColorConfig {
    fn default() -> Self {
        Self {
            error: default_error_color(),
            warn: default_warn_color(),
            info: default_info_color(),
            debug: default_debug_color(),
            fatal: default_fatal_color(),
        }
    }
}

fn default_refresh_interval() -> u64 {
    5000
}
fn default_page_size() -> usize {
    100
}
fn default_max_logs() -> usize {
    10000
}
fn default_date_format() -> String {
    "%Y-%m-%d %H:%M:%S".to_string()
}
fn default_true() -> bool {
    true
}
fn default_error_color() -> String {
    "red".to_string()
}
fn default_warn_color() -> String {
    "yellow".to_string()
}
fn default_info_color() -> String {
    "green".to_string()
}
fn default_debug_color() -> String {
    "blue".to_string()
}
fn default_fatal_color() -> String {
    "magenta".to_string()
}

impl Config {
    pub fn load(config_path: Option<PathBuf>) -> Result<Self> {
        let config_file = if let Some(path) = config_path {
            path
        } else {
            Self::default_config_path()?
        };

        if !config_file.exists() {
            // Return default config if file doesn't exist
            return Ok(Config::default());
        }

        let contents =
            std::fs::read_to_string(&config_file).context("Failed to read config file")?;

        let config: Config = toml::from_str(&contents).context("Failed to parse config file")?;

        Ok(config)
    }

    pub fn save(&self, config_path: Option<PathBuf>) -> Result<()> {
        let config_file = if let Some(path) = config_path {
            path
        } else {
            Self::default_config_path()?
        };

        // Create parent directory if it doesn't exist
        if let Some(parent) = config_file.parent() {
            std::fs::create_dir_all(parent).context("Failed to create config directory")?;
        }

        let contents = toml::to_string_pretty(self).context("Failed to serialize config")?;

        std::fs::write(&config_file, contents).context("Failed to write config file")?;

        Ok(())
    }

    pub fn default_config_path() -> Result<PathBuf> {
        let config_dir = dirs::config_dir()
            .context("Failed to get config directory")?
            .join("jlo-tui");

        Ok(config_dir.join("config.toml"))
    }
}
