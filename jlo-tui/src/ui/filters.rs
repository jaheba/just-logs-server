use crate::api::{Application, LogFilters, LogLevel};
use chrono::{Duration, Utc};
use crossterm::event::{KeyCode, KeyEvent};
use ratatui::{
    layout::{Constraint, Direction, Layout, Rect},
    style::{Color, Modifier, Style},
    text::{Line, Span},
    widgets::{Block, Borders, List, ListItem, ListState, Paragraph},
    Frame,
};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum FilterField {
    App,
    Levels,
    Search,
    TimeRange,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TimeRangePreset {
    Last1Hour,
    Last24Hours,
    Last7Days,
    All,
}

impl TimeRangePreset {
    pub fn as_str(&self) -> &str {
        match self {
            TimeRangePreset::Last1Hour => "Last 1 hour",
            TimeRangePreset::Last24Hours => "Last 24 hours",
            TimeRangePreset::Last7Days => "Last 7 days",
            TimeRangePreset::All => "All time",
        }
    }

    pub fn all() -> Vec<TimeRangePreset> {
        vec![
            TimeRangePreset::Last1Hour,
            TimeRangePreset::Last24Hours,
            TimeRangePreset::Last7Days,
            TimeRangePreset::All,
        ]
    }
}

pub struct FilterState {
    pub active_field: FilterField,
    pub selected_app_id: Option<i64>,
    pub selected_levels: Vec<String>,
    pub search_text: String,
    pub time_range: TimeRangePreset,
    pub apps: Vec<Application>,
    pub app_list_state: ListState,
    pub level_list_state: ListState,
    pub time_list_state: ListState,
}

impl FilterState {
    pub fn new(apps: Vec<Application>) -> Self {
        let mut app_list_state = ListState::default();
        app_list_state.select(Some(0));

        let mut level_list_state = ListState::default();
        level_list_state.select(Some(0));

        let mut time_list_state = ListState::default();
        time_list_state.select(Some(1)); // Default to Last 24 hours

        Self {
            active_field: FilterField::App,
            selected_app_id: None,
            selected_levels: Vec::new(),
            search_text: String::new(),
            time_range: TimeRangePreset::Last24Hours,
            apps,
            app_list_state,
            level_list_state,
            time_list_state,
        }
    }

    pub fn handle_key(&mut self, key: KeyEvent) -> bool {
        match self.active_field {
            FilterField::Search => match key.code {
                KeyCode::Char(c) => {
                    self.search_text.push(c);
                    false
                }
                KeyCode::Backspace => {
                    self.search_text.pop();
                    false
                }
                KeyCode::Enter => true,
                KeyCode::Tab => {
                    self.active_field = FilterField::App;
                    false
                }
                _ => false,
            },
            FilterField::App => match key.code {
                KeyCode::Up | KeyCode::Char('k') => {
                    self.previous_app();
                    false
                }
                KeyCode::Down | KeyCode::Char('j') => {
                    self.next_app();
                    false
                }
                KeyCode::Enter | KeyCode::Char(' ') => {
                    self.toggle_app_selection();
                    false
                }
                KeyCode::Tab => {
                    self.active_field = FilterField::Levels;
                    false
                }
                _ => false,
            },
            FilterField::Levels => match key.code {
                KeyCode::Up | KeyCode::Char('k') => {
                    self.previous_level();
                    false
                }
                KeyCode::Down | KeyCode::Char('j') => {
                    self.next_level();
                    false
                }
                KeyCode::Enter | KeyCode::Char(' ') => {
                    self.toggle_level_selection();
                    false
                }
                KeyCode::Tab => {
                    self.active_field = FilterField::TimeRange;
                    false
                }
                _ => false,
            },
            FilterField::TimeRange => match key.code {
                KeyCode::Up | KeyCode::Char('k') => {
                    self.previous_time_range();
                    false
                }
                KeyCode::Down | KeyCode::Char('j') => {
                    self.next_time_range();
                    false
                }
                KeyCode::Enter | KeyCode::Char(' ') => {
                    self.select_time_range();
                    false
                }
                KeyCode::Tab => {
                    self.active_field = FilterField::Search;
                    false
                }
                _ => false,
            },
        }
    }

    fn next_app(&mut self) {
        let i = self.app_list_state.selected().unwrap_or(0);
        let next = if i >= self.apps.len() { 0 } else { i + 1 };
        self.app_list_state.select(Some(next));
    }

    fn previous_app(&mut self) {
        let i = self.app_list_state.selected().unwrap_or(0);
        let prev = if i == 0 { self.apps.len() } else { i - 1 };
        self.app_list_state.select(Some(prev));
    }

    fn toggle_app_selection(&mut self) {
        if let Some(i) = self.app_list_state.selected() {
            if i == 0 {
                self.selected_app_id = None;
            } else if let Some(app) = self.apps.get(i - 1) {
                self.selected_app_id = Some(app.id);
            }
        }
    }

    fn next_level(&mut self) {
        let i = self.level_list_state.selected().unwrap_or(0);
        let next = if i >= LogLevel::all().len() - 1 {
            0
        } else {
            i + 1
        };
        self.level_list_state.select(Some(next));
    }

    fn previous_level(&mut self) {
        let i = self.level_list_state.selected().unwrap_or(0);
        let prev = if i == 0 {
            LogLevel::all().len() - 1
        } else {
            i - 1
        };
        self.level_list_state.select(Some(prev));
    }

    fn toggle_level_selection(&mut self) {
        if let Some(i) = self.level_list_state.selected() {
            if let Some(level) = LogLevel::all().get(i) {
                let level_str = level.as_str().to_string();
                if self.selected_levels.contains(&level_str) {
                    self.selected_levels.retain(|l| l != &level_str);
                } else {
                    self.selected_levels.push(level_str);
                }
            }
        }
    }

    fn next_time_range(&mut self) {
        let i = self.time_list_state.selected().unwrap_or(0);
        let next = if i >= TimeRangePreset::all().len() - 1 {
            0
        } else {
            i + 1
        };
        self.time_list_state.select(Some(next));
    }

    fn previous_time_range(&mut self) {
        let i = self.time_list_state.selected().unwrap_or(0);
        let prev = if i == 0 {
            TimeRangePreset::all().len() - 1
        } else {
            i - 1
        };
        self.time_list_state.select(Some(prev));
    }

    fn select_time_range(&mut self) {
        if let Some(i) = self.time_list_state.selected() {
            if let Some(preset) = TimeRangePreset::all().get(i) {
                self.time_range = *preset;
            }
        }
    }

    pub fn to_log_filters(&self) -> LogFilters {
        let (start_time, end_time) = match self.time_range {
            TimeRangePreset::Last1Hour => (Some(Utc::now() - Duration::hours(1)), Some(Utc::now())),
            TimeRangePreset::Last24Hours => {
                (Some(Utc::now() - Duration::days(1)), Some(Utc::now()))
            }
            TimeRangePreset::Last7Days => (Some(Utc::now() - Duration::days(7)), Some(Utc::now())),
            TimeRangePreset::All => (None, None),
        };

        LogFilters {
            app_id: self.selected_app_id,
            levels: self.selected_levels.clone(),
            search: if self.search_text.is_empty() {
                None
            } else {
                Some(self.search_text.clone())
            },
            start_time,
            end_time,
            limit: 100,
            offset: 0,
        }
    }
}

pub fn render_filters(f: &mut Frame, area: Rect, state: &mut FilterState) {
    let block = Block::default()
        .title("Filters (Tab to switch, Enter to apply, ESC to close)")
        .borders(Borders::ALL)
        .border_style(Style::default().fg(Color::Yellow));

    let inner_area = block.inner(area);
    f.render_widget(block, area);

    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Length(8),
            Constraint::Length(8),
            Constraint::Length(7),
            Constraint::Length(3),
        ])
        .split(inner_area);

    // App selector
    render_app_selector(f, chunks[0], state);

    // Level selector
    render_level_selector(f, chunks[1], state);

    // Time range selector
    render_time_range_selector(f, chunks[2], state);

    // Search field
    render_search_field(f, chunks[3], state);
}

fn render_app_selector(f: &mut Frame, area: Rect, state: &mut FilterState) {
    let is_active = state.active_field == FilterField::App;
    let style = if is_active {
        Style::default().fg(Color::Cyan)
    } else {
        Style::default().fg(Color::White)
    };

    let mut items = vec![ListItem::new(Line::from(vec![
        Span::raw("["),
        if state.selected_app_id.is_none() {
            Span::styled("X", Style::default().fg(Color::Green))
        } else {
            Span::raw(" ")
        },
        Span::raw("] All Apps"),
    ]))];

    for app in &state.apps {
        let is_selected = Some(app.id) == state.selected_app_id;
        items.push(ListItem::new(Line::from(vec![
            Span::raw("["),
            if is_selected {
                Span::styled("X", Style::default().fg(Color::Green))
            } else {
                Span::raw(" ")
            },
            Span::raw("] "),
            Span::raw(&app.name),
        ])));
    }

    let list = List::new(items)
        .block(
            Block::default()
                .borders(Borders::ALL)
                .title("Application")
                .border_style(style),
        )
        .highlight_style(Style::default().bg(Color::DarkGray));

    f.render_stateful_widget(list, area, &mut state.app_list_state);
}

fn render_level_selector(f: &mut Frame, area: Rect, state: &mut FilterState) {
    let is_active = state.active_field == FilterField::Levels;
    let style = if is_active {
        Style::default().fg(Color::Cyan)
    } else {
        Style::default().fg(Color::White)
    };

    let items: Vec<ListItem> = LogLevel::all()
        .iter()
        .map(|level| {
            let level_str = level.as_str().to_string();
            let is_selected = state.selected_levels.contains(&level_str);
            ListItem::new(Line::from(vec![
                Span::raw("["),
                if is_selected {
                    Span::styled("X", Style::default().fg(Color::Green))
                } else {
                    Span::raw(" ")
                },
                Span::raw("] "),
                Span::raw(level_str),
            ]))
        })
        .collect();

    let list = List::new(items)
        .block(
            Block::default()
                .borders(Borders::ALL)
                .title("Levels (Space to toggle)")
                .border_style(style),
        )
        .highlight_style(Style::default().bg(Color::DarkGray));

    f.render_stateful_widget(list, area, &mut state.level_list_state);
}

fn render_time_range_selector(f: &mut Frame, area: Rect, state: &mut FilterState) {
    let is_active = state.active_field == FilterField::TimeRange;
    let style = if is_active {
        Style::default().fg(Color::Cyan)
    } else {
        Style::default().fg(Color::White)
    };

    let time_range_presets = TimeRangePreset::all();
    let items: Vec<ListItem> = time_range_presets
        .iter()
        .map(|preset| {
            let is_selected = *preset == state.time_range;
            ListItem::new(Line::from(vec![
                Span::raw("["),
                if is_selected {
                    Span::styled("X", Style::default().fg(Color::Green))
                } else {
                    Span::raw(" ")
                },
                Span::raw("] "),
                Span::raw(preset.as_str()),
            ]))
        })
        .collect();

    let list = List::new(items)
        .block(
            Block::default()
                .borders(Borders::ALL)
                .title("Time Range")
                .border_style(style),
        )
        .highlight_style(Style::default().bg(Color::DarkGray));

    f.render_stateful_widget(list, area, &mut state.time_list_state);
}

fn render_search_field(f: &mut Frame, area: Rect, state: &FilterState) {
    let is_active = state.active_field == FilterField::Search;
    let style = if is_active {
        Style::default().fg(Color::Cyan)
    } else {
        Style::default().fg(Color::White)
    };

    let block = Block::default()
        .borders(Borders::ALL)
        .title("Search")
        .border_style(style);

    let text = Paragraph::new(state.search_text.as_str()).block(block);
    f.render_widget(text, area);
}
