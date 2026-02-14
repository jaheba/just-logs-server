use crate::api::Log;
use crate::config::ColorConfig;
use crate::utils::{format_timestamp, truncate_string};
use ratatui::{
    layout::{Constraint, Rect},
    style::{Color, Modifier, Style},
    text::Text,
    widgets::{Block, Borders, Cell, Row, Table, TableState},
    Frame,
};

pub struct LogsViewState {
    pub table_state: TableState,
    pub logs: Vec<Log>,
    pub date_format: String,
}

impl LogsViewState {
    pub fn new(date_format: String) -> Self {
        let mut table_state = TableState::default();
        table_state.select(Some(0));
        Self {
            table_state,
            logs: Vec::new(),
            date_format,
        }
    }

    pub fn next(&mut self) {
        if self.logs.is_empty() {
            return;
        }
        let i = match self.table_state.selected() {
            Some(i) => {
                if i >= self.logs.len() - 1 {
                    0
                } else {
                    i + 1
                }
            }
            None => 0,
        };
        self.table_state.select(Some(i));
    }

    pub fn previous(&mut self) {
        if self.logs.is_empty() {
            return;
        }
        let i = match self.table_state.selected() {
            Some(i) => {
                if i == 0 {
                    self.logs.len() - 1
                } else {
                    i - 1
                }
            }
            None => 0,
        };
        self.table_state.select(Some(i));
    }

    pub fn select_first(&mut self) {
        if !self.logs.is_empty() {
            self.table_state.select(Some(0));
        }
    }

    pub fn select_last(&mut self) {
        if !self.logs.is_empty() {
            self.table_state.select(Some(self.logs.len() - 1));
        }
    }

    pub fn page_down(&mut self) {
        if self.logs.is_empty() {
            return;
        }
        let i = self.table_state.selected().unwrap_or(0);
        let new_i = (i + 10).min(self.logs.len() - 1);
        self.table_state.select(Some(new_i));
    }

    pub fn page_up(&mut self) {
        if self.logs.is_empty() {
            return;
        }
        let i = self.table_state.selected().unwrap_or(0);
        let new_i = i.saturating_sub(10);
        self.table_state.select(Some(new_i));
    }

    pub fn selected_log(&self) -> Option<&Log> {
        self.table_state.selected().and_then(|i| self.logs.get(i))
    }

    pub fn set_logs(&mut self, logs: Vec<Log>) {
        self.logs = logs;
        if !self.logs.is_empty() && self.table_state.selected().is_none() {
            self.table_state.select(Some(0));
        }
    }
}

pub fn render_logs_table(
    f: &mut Frame,
    area: Rect,
    state: &mut LogsViewState,
    colors: &ColorConfig,
) {
    let rows: Vec<Row> = state
        .logs
        .iter()
        .map(|log| {
            let timestamp = format_timestamp(&log.timestamp, &state.date_format);
            let level_color = get_level_color(&log.level, colors);

            Row::new(vec![
                Cell::from(timestamp),
                Cell::from(log.level.clone()).style(Style::default().fg(level_color)),
                Cell::from(log.app_name.clone()),
                Cell::from(truncate_string(&log.message, 100)),
            ])
        })
        .collect();

    let header = Row::new(vec!["Timestamp", "Level", "App", "Message"])
        .style(
            Style::default()
                .fg(Color::Yellow)
                .add_modifier(Modifier::BOLD),
        )
        .bottom_margin(1);

    let table = Table::new(
        rows,
        [
            Constraint::Length(19),
            Constraint::Length(7),
            Constraint::Length(15),
            Constraint::Min(40),
        ],
    )
    .header(header)
    .block(
        Block::default()
            .borders(Borders::ALL)
            .title("Logs")
            .border_style(Style::default().fg(Color::White)),
    )
    .highlight_style(
        Style::default()
            .bg(Color::DarkGray)
            .add_modifier(Modifier::BOLD),
    );

    f.render_stateful_widget(table, area, &mut state.table_state);
}

fn get_level_color(level: &str, colors: &ColorConfig) -> Color {
    match level.to_uppercase().as_str() {
        "ERROR" => parse_color(&colors.error),
        "WARN" => parse_color(&colors.warn),
        "INFO" => parse_color(&colors.info),
        "DEBUG" => parse_color(&colors.debug),
        "FATAL" => parse_color(&colors.fatal),
        _ => Color::White,
    }
}

fn parse_color(color_str: &str) -> Color {
    match color_str.to_lowercase().as_str() {
        "red" => Color::Red,
        "yellow" => Color::Yellow,
        "green" => Color::Green,
        "blue" => Color::Blue,
        "magenta" => Color::Magenta,
        "cyan" => Color::Cyan,
        "white" => Color::White,
        "gray" | "grey" => Color::Gray,
        _ => Color::White,
    }
}

pub fn render_log_detail(f: &mut Frame, area: Rect, log: &Log) {
    let detail_text = format_log_detail(log);

    let block = Block::default()
        .title("Log Details (Press ESC or q to close)")
        .borders(Borders::ALL)
        .border_style(Style::default().fg(Color::Cyan));

    let paragraph = ratatui::widgets::Paragraph::new(detail_text)
        .block(block)
        .wrap(ratatui::widgets::Wrap { trim: false });

    f.render_widget(paragraph, area);
}

fn format_log_detail(log: &Log) -> Text<'static> {
    let mut lines = vec![
        format!("ID: {}", log.id),
        format!("App: {} (ID: {})", log.app_name, log.app_id),
        format!("Level: {}", log.level),
        format!("Timestamp: {}", log.timestamp.to_rfc3339()),
        format!("Created At: {}", log.created_at.to_rfc3339()),
        String::new(),
        "Message:".to_string(),
        log.message.clone(),
    ];

    if let Some(ref structured_data) = log.structured_data {
        lines.push(String::new());
        lines.push("Structured Data:".to_string());
        lines.push(crate::utils::format_json_pretty(structured_data));
    }

    if let Some(ref tags) = log.tags {
        if !tags.is_empty() {
            lines.push(String::new());
            lines.push("Tags:".to_string());
            for (key, value) in tags {
                lines.push(format!("  {}: {}", key, value));
            }
        }
    }

    Text::from(lines.join("\n"))
}
