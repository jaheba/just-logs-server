use crossterm::event::{KeyCode, KeyEvent};
use ratatui::{
    layout::{Alignment, Constraint, Direction, Layout, Rect},
    style::{Color, Modifier, Style},
    text::{Line, Span},
    widgets::{Block, Borders, Paragraph},
    Frame,
};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum LoginField {
    Username,
    Password,
}

pub struct LoginState {
    pub username: String,
    pub password: String,
    pub active_field: LoginField,
    pub error_message: Option<String>,
    pub is_submitting: bool,
}

impl Default for LoginState {
    fn default() -> Self {
        Self {
            username: String::new(),
            password: String::new(),
            active_field: LoginField::Username,
            error_message: None,
            is_submitting: false,
        }
    }
}

impl LoginState {
    pub fn handle_key(&mut self, key: KeyEvent) -> bool {
        match key.code {
            KeyCode::Char(c) => {
                match self.active_field {
                    LoginField::Username => self.username.push(c),
                    LoginField::Password => self.password.push(c),
                }
                false
            }
            KeyCode::Backspace => {
                match self.active_field {
                    LoginField::Username => {
                        self.username.pop();
                    }
                    LoginField::Password => {
                        self.password.pop();
                    }
                }
                false
            }
            KeyCode::Tab => {
                self.active_field = match self.active_field {
                    LoginField::Username => LoginField::Password,
                    LoginField::Password => LoginField::Username,
                };
                false
            }
            KeyCode::Enter => {
                // Submit login
                true
            }
            _ => false,
        }
    }

    pub fn set_error(&mut self, message: String) {
        self.error_message = Some(message);
        self.is_submitting = false;
    }

    pub fn clear_error(&mut self) {
        self.error_message = None;
    }
}

pub fn render_login(f: &mut Frame, area: Rect, state: &LoginState) {
    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Percentage(30),
            Constraint::Length(11),
            Constraint::Percentage(30),
        ])
        .split(area);

    let login_chunks = Layout::default()
        .direction(Direction::Horizontal)
        .constraints([
            Constraint::Percentage(25),
            Constraint::Percentage(50),
            Constraint::Percentage(25),
        ])
        .split(chunks[1]);

    let form_area = login_chunks[1];

    let form_chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Length(1),
            Constraint::Length(3),
            Constraint::Length(3),
            Constraint::Length(1),
            Constraint::Length(3),
        ])
        .split(form_area);

    // Title
    let title = Paragraph::new("just-logs TUI - Login")
        .style(
            Style::default()
                .fg(Color::Cyan)
                .add_modifier(Modifier::BOLD),
        )
        .alignment(Alignment::Center);
    f.render_widget(title, form_chunks[0]);

    // Username field
    let username_style = if state.active_field == LoginField::Username {
        Style::default().fg(Color::Yellow)
    } else {
        Style::default().fg(Color::White)
    };

    let username_block = Block::default()
        .borders(Borders::ALL)
        .title("Username")
        .border_style(username_style);

    let username_text = Paragraph::new(state.username.as_str()).block(username_block);
    f.render_widget(username_text, form_chunks[1]);

    // Password field
    let password_style = if state.active_field == LoginField::Password {
        Style::default().fg(Color::Yellow)
    } else {
        Style::default().fg(Color::White)
    };

    let password_block = Block::default()
        .borders(Borders::ALL)
        .title("Password")
        .border_style(password_style);

    let masked_password = "*".repeat(state.password.len());
    let password_text = Paragraph::new(masked_password.as_str()).block(password_block);
    f.render_widget(password_text, form_chunks[2]);

    // Instructions or error
    let message = if let Some(ref error) = state.error_message {
        Line::from(vec![Span::styled(
            error.as_str(),
            Style::default().fg(Color::Red),
        )])
    } else if state.is_submitting {
        Line::from(vec![Span::styled(
            "Logging in...",
            Style::default().fg(Color::Yellow),
        )])
    } else {
        Line::from(vec![
            Span::styled("Tab", Style::default().fg(Color::Cyan)),
            Span::raw(" to switch fields | "),
            Span::styled("Enter", Style::default().fg(Color::Cyan)),
            Span::raw(" to login | "),
            Span::styled("Ctrl+C", Style::default().fg(Color::Cyan)),
            Span::raw(" to quit"),
        ])
    };

    let instructions = Paragraph::new(message).alignment(Alignment::Center);
    f.render_widget(instructions, form_chunks[4]);
}
