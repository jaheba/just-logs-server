use crate::api::{ApiClient, Application, ExportFormat, Log, LogFilters};
use crate::api::sse::LogStream;
use crate::config::Config;
use crate::ui::{FilterState, LoginState, LogsViewState};
use anyhow::Result;
use crossterm::event::{KeyCode, KeyEvent, KeyModifiers};
use std::path::PathBuf;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum AppState {
    Login,
    Main,
    FilterPanel,
    LogDetail,
    Help,
    ExportMenu,
}

pub struct App {
    pub state: AppState,
    pub config: Config,
    pub api_client: ApiClient,
    pub login_state: LoginState,
    pub logs_view: LogsViewState,
    pub filter_state: Option<FilterState>,
    pub apps: Vec<Application>,
    pub tail_mode: bool,
    pub log_stream: Option<LogStream>,
    pub status_message: Option<String>,
    pub should_quit: bool,
    pub export_format_selection: usize,
}

impl App {
    pub fn new(config: Config, username: Option<String>, password: Option<String>) -> Result<Self> {
        let api_client = ApiClient::new(config.server_url.clone())?;
        let logs_view = LogsViewState::new(config.ui.date_format.clone());
        
        let mut login_state = LoginState::default();
        
        // Pre-fill username from config or parameter
        if let Some(user) = username.or(config.username.clone()) {
            login_state.username = user;
        }
        
        // Pre-fill password if provided (will auto-login)
        if let Some(pass) = password {
            login_state.password = pass;
            // Will trigger auto-login on first event loop
        }

        Ok(Self {
            state: AppState::Login,
            config,
            api_client,
            login_state,
            logs_view,
            filter_state: None,
            apps: Vec::new(),
            tail_mode: false,
            log_stream: None,
            status_message: None,
            should_quit: false,
            export_format_selection: 0,
        })
    }
    
    pub async fn try_auto_login(&mut self) -> Result<()> {
        // If username and password are both filled and we're on login screen, try to login
        if self.state == AppState::Login 
            && !self.login_state.username.is_empty() 
            && !self.login_state.password.is_empty() 
            && !self.login_state.is_submitting 
        {
            self.login_state.is_submitting = true;
            match self
                .api_client
                .login(&self.login_state.username, &self.login_state.password)
                .await
            {
                Ok(_) => {
                    match self.api_client.get_apps().await {
                        Ok(apps) => {
                            self.apps = apps;
                            self.state = AppState::Main;
                            self.status_message = Some("Logged in successfully".to_string());
                        }
                        Err(e) => {
                            self.login_state.set_error(format!("Failed to load apps: {}", e));
                        }
                    }
                }
                Err(e) => {
                    self.login_state.set_error(format!("Login failed: {}", e));
                }
            }
        }
        Ok(())
    }

    pub async fn handle_key(&mut self, key: KeyEvent) -> Result<()> {
        match self.state {
            AppState::Login => self.handle_login_key(key).await?,
            AppState::Main => self.handle_main_key(key).await?,
            AppState::FilterPanel => self.handle_filter_key(key).await?,
            AppState::LogDetail => self.handle_detail_key(key),
            AppState::Help => self.handle_help_key(key),
            AppState::ExportMenu => self.handle_export_key(key).await?,
        }
        Ok(())
    }

    async fn handle_login_key(&mut self, key: KeyEvent) -> Result<()> {
        if key.code == KeyCode::Char('c') && key.modifiers.contains(KeyModifiers::CONTROL) {
            self.should_quit = true;
            return Ok(());
        }

        let should_submit = self.login_state.handle_key(key);
        if should_submit {
            self.login_state.is_submitting = true;
            self.login_state.clear_error();

            match self
                .api_client
                .login(&self.login_state.username, &self.login_state.password)
                .await
            {
                Ok(_) => {
                    // Fetch apps after successful login
                    match self.api_client.get_apps().await {
                        Ok(apps) => {
                            self.apps = apps;
                            self.state = AppState::Main;
                            self.status_message = Some("Logged in successfully".to_string());
                        }
                        Err(e) => {
                            self.login_state.set_error(format!("Failed to load apps: {}", e));
                        }
                    }
                }
                Err(e) => {
                    self.login_state.set_error(format!("Login failed: {}", e));
                }
            }
        }

        Ok(())
    }

    async fn handle_main_key(&mut self, key: KeyEvent) -> Result<()> {
        match key.code {
            KeyCode::Char('q') => {
                self.should_quit = true;
            }
            KeyCode::Char('?') => {
                self.state = AppState::Help;
            }
            KeyCode::Char('f') => {
                self.state = AppState::FilterPanel;
                self.filter_state = Some(FilterState::new(self.apps.clone()));
            }
            KeyCode::Char('r') => {
                self.refresh_logs().await?;
            }
            KeyCode::Char('t') => {
                self.toggle_tail_mode().await?;
            }
            KeyCode::Char('e') => {
                self.state = AppState::ExportMenu;
                self.export_format_selection = 0;
            }
            KeyCode::Up | KeyCode::Char('k') => {
                self.logs_view.previous();
            }
            KeyCode::Down | KeyCode::Char('j') => {
                self.logs_view.next();
            }
            KeyCode::Char('g') => {
                self.logs_view.select_first();
            }
            KeyCode::Char('G') => {
                self.logs_view.select_last();
            }
            KeyCode::Char('u') if key.modifiers.contains(KeyModifiers::CONTROL) => {
                self.logs_view.page_up();
            }
            KeyCode::Char('d') if key.modifiers.contains(KeyModifiers::CONTROL) => {
                self.logs_view.page_down();
            }
            KeyCode::Enter => {
                if self.logs_view.selected_log().is_some() {
                    self.state = AppState::LogDetail;
                }
            }
            _ => {}
        }
        Ok(())
    }

    async fn handle_filter_key(&mut self, key: KeyEvent) -> Result<()> {
        if key.code == KeyCode::Esc {
            self.state = AppState::Main;
            self.filter_state = None;
            return Ok(());
        }

        if let Some(ref mut filter_state) = self.filter_state {
            let should_apply = filter_state.handle_key(key);
            if should_apply || key.code == KeyCode::Enter {
                let filters = filter_state.to_log_filters();
                self.apply_filters(filters).await?;
                self.state = AppState::Main;
                self.filter_state = None;
            }
        }

        Ok(())
    }

    fn handle_detail_key(&mut self, key: KeyEvent) {
        if key.code == KeyCode::Esc || key.code == KeyCode::Char('q') {
            self.state = AppState::Main;
        }
    }

    fn handle_help_key(&mut self, key: KeyEvent) {
        if key.code == KeyCode::Esc || key.code == KeyCode::Char('?') {
            self.state = AppState::Main;
        }
    }

    async fn handle_export_key(&mut self, key: KeyEvent) -> Result<()> {
        match key.code {
            KeyCode::Esc | KeyCode::Char('q') => {
                self.state = AppState::Main;
            }
            KeyCode::Up | KeyCode::Char('k') => {
                self.export_format_selection = (self.export_format_selection + 1) % 2;
            }
            KeyCode::Down | KeyCode::Char('j') => {
                self.export_format_selection = (self.export_format_selection + 1) % 2;
            }
            KeyCode::Enter => {
                self.export_logs().await?;
                self.state = AppState::Main;
            }
            _ => {}
        }
        Ok(())
    }

    async fn refresh_logs(&mut self) -> Result<()> {
        self.status_message = Some("Refreshing logs...".to_string());
        let filters = LogFilters::default();
        match self.api_client.get_logs(&filters).await {
            Ok(logs) => {
                self.logs_view.set_logs(logs);
                self.status_message = Some("Logs refreshed".to_string());
            }
            Err(e) => {
                self.status_message = Some(format!("Failed to refresh logs: {}", e));
            }
        }
        Ok(())
    }

    async fn apply_filters(&mut self, filters: LogFilters) -> Result<()> {
        self.status_message = Some("Applying filters...".to_string());
        match self.api_client.get_logs(&filters).await {
            Ok(logs) => {
                self.logs_view.set_logs(logs);
                self.status_message = Some(format!("Found {} logs", self.logs_view.logs.len()));
            }
            Err(e) => {
                self.status_message = Some(format!("Failed to apply filters: {}", e));
            }
        }
        Ok(())
    }

    async fn toggle_tail_mode(&mut self) -> Result<()> {
        if self.tail_mode {
            // Disable tail mode
            self.tail_mode = false;
            self.log_stream = None;
            self.status_message = Some("Tail mode disabled".to_string());
        } else {
            // Enable tail mode
            let stream_url = self.api_client.get_stream_url();
            match LogStream::new(stream_url).await {
                Ok(stream) => {
                    self.log_stream = Some(stream);
                    self.tail_mode = true;
                    self.status_message = Some("Tail mode enabled (LIVE)".to_string());
                }
                Err(e) => {
                    self.status_message = Some(format!("Failed to enable tail mode: {}", e));
                }
            }
        }
        Ok(())
    }

    pub async fn poll_stream(&mut self) {
        if let Some(ref mut stream) = self.log_stream {
            if let Some(log) = stream.next().await {
                self.logs_view.logs.insert(0, log);
                // Keep only max logs in memory
                if self.logs_view.logs.len() > self.config.ui.max_logs_in_memory {
                    self.logs_view.logs.truncate(self.config.ui.max_logs_in_memory);
                }
            }
        }
    }

    async fn export_logs(&mut self) -> Result<()> {
        let format = if self.export_format_selection == 0 {
            ExportFormat::Json
        } else {
            ExportFormat::Csv
        };

        self.status_message = Some(format!("Exporting logs as {}...", format.as_str()));

        let filters = LogFilters::default();
        match self.api_client.export_logs(format, &filters).await {
            Ok(data) => {
                let filename = format!(
                    "logs_export_{}.{}",
                    chrono::Utc::now().format("%Y%m%d_%H%M%S"),
                    format.as_str()
                );
                let path = PathBuf::from(&filename);
                match std::fs::write(&path, data) {
                    Ok(_) => {
                        self.status_message =
                            Some(format!("Logs exported to {}", path.display()));
                    }
                    Err(e) => {
                        self.status_message = Some(format!("Failed to write file: {}", e));
                    }
                }
            }
            Err(e) => {
                self.status_message = Some(format!("Failed to export logs: {}", e));
            }
        }

        Ok(())
    }

    pub fn get_status_line(&self) -> String {
        let server_info = format!("Server: {}", self.config.server_url);
        let tail_indicator = if self.tail_mode {
            " [LIVE]"
        } else {
            ""
        };
        let log_count = format!("Logs: {}", self.logs_view.logs.len());

        format!("{} | {}{}", server_info, log_count, tail_indicator)
    }
}
