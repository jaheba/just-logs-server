mod api;
mod app;
mod config;
mod ui;
mod utils;

use anyhow::Result;
use app::{App, AppState};
use clap::Parser;
use config::Config;
use crossterm::{
    event::{self, DisableMouseCapture, EnableMouseCapture, Event},
    execute,
    terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen},
};
use ratatui::{
    backend::CrosstermBackend,
    layout::{Constraint, Direction, Layout, Rect},
    style::{Color, Modifier, Style},
    text::{Line, Span},
    widgets::{Block, Borders, List, ListItem, Paragraph},
    Terminal,
};
use std::io;
use std::path::PathBuf;
use std::time::Duration;

#[derive(Parser, Debug)]
#[command(name = "jlo-tui")]
#[command(about = "Terminal UI for just-logs server", long_about = None)]
struct Args {
    /// Server URL (overrides config file)
    #[arg(short, long)]
    server: Option<String>,

    /// Username (overrides config file)
    #[arg(short, long)]
    username: Option<String>,

    /// Password (NOT RECOMMENDED: visible in process list. Use JLO_PASSWORD env var instead)
    #[arg(short, long, env = "JLO_PASSWORD")]
    password: Option<String>,

    /// Path to config file
    #[arg(short, long)]
    config: Option<PathBuf>,
}

#[tokio::main]
async fn main() -> Result<()> {
    let args = Args::parse();

    // Load config
    let mut config = Config::load(args.config)?;

    // Override with CLI args
    if let Some(server) = args.server {
        config.server_url = server;
    }
    
    // Determine username (CLI arg takes precedence over config)
    let username = args.username.or_else(|| config.username.clone());
    if username.is_some() {
        config.username = username.clone();
    }

    // Setup terminal
    enable_raw_mode()?;
    let mut stdout = io::stdout();
    execute!(stdout, EnterAlternateScreen, EnableMouseCapture)?;
    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend)?;

    // Create app with optional password
    let mut app = App::new(config, username, args.password)?;

    // Run app
    let res = run_app(&mut terminal, &mut app).await;

    // Restore terminal
    disable_raw_mode()?;
    execute!(
        terminal.backend_mut(),
        LeaveAlternateScreen,
        DisableMouseCapture
    )?;
    terminal.show_cursor()?;

    if let Err(err) = res {
        eprintln!("Error: {:?}", err);
    }

    Ok(())
}

async fn run_app<B: ratatui::backend::Backend>(
    terminal: &mut Terminal<B>,
    app: &mut App,
) -> Result<()> {
    // Try auto-login if credentials are pre-filled
    app.try_auto_login().await?;
    
    loop {
        terminal.draw(|f| {
            let size = f.area();
            render_app(f, app, size);
        })?;

        // Handle events with timeout
        if event::poll(Duration::from_millis(100))? {
            if let Event::Key(key) = event::read()? {
                app.handle_key(key).await?;
            }
        }

        // Poll stream if in tail mode
        if app.tail_mode {
            app.poll_stream().await;
        }

        if app.should_quit {
            break;
        }
    }

    Ok(())
}

fn render_app(f: &mut ratatui::Frame, app: &mut App, area: Rect) {
    match app.state {
        AppState::Login => {
            ui::login::render_login(f, area, &app.login_state);
        }
        AppState::Main => {
            render_main_view(f, app, area);
        }
        AppState::FilterPanel => {
            render_main_view(f, app, area);
            if let Some(ref mut filter_state) = app.filter_state {
                let popup_area = centered_rect(80, 80, area);
                ui::filters::render_filters(f, popup_area, filter_state);
            }
        }
        AppState::LogDetail => {
            render_main_view(f, app, area);
            if let Some(log) = app.logs_view.selected_log() {
                let popup_area = centered_rect(80, 80, area);
                ui::render_log_detail(f, popup_area, log);
            }
        }
        AppState::Help => {
            ui::render_help(f, area);
        }
        AppState::ExportMenu => {
            render_main_view(f, app, area);
            let popup_area = centered_rect(40, 30, area);
            render_export_menu(f, popup_area, app.export_format_selection);
        }
    }
}

fn render_main_view(f: &mut ratatui::Frame, app: &mut App, area: Rect) {
    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Length(1),
            Constraint::Min(0),
            Constraint::Length(2),
        ])
        .split(area);

    // Status bar
    let status_line = app.get_status_line();
    let status_bar = Paragraph::new(status_line).style(
        Style::default()
            .fg(Color::White)
            .bg(Color::Blue)
            .add_modifier(Modifier::BOLD),
    );
    f.render_widget(status_bar, chunks[0]);

    // Main logs table
    ui::render_logs_table(f, chunks[1], &mut app.logs_view, &app.config.colors);

    // Keybindings hint
    let keybindings = if app.tail_mode {
        Line::from(vec![
            Span::styled("t", Style::default().fg(Color::Yellow)),
            Span::raw(":Stop Tail | "),
            Span::styled("f", Style::default().fg(Color::Yellow)),
            Span::raw(":Filters | "),
            Span::styled("?", Style::default().fg(Color::Yellow)),
            Span::raw(":Help | "),
            Span::styled("q", Style::default().fg(Color::Yellow)),
            Span::raw(":Quit"),
        ])
    } else {
        Line::from(vec![
            Span::styled("↑↓/jk", Style::default().fg(Color::Yellow)),
            Span::raw(":Navigate | "),
            Span::styled("Enter", Style::default().fg(Color::Yellow)),
            Span::raw(":Details | "),
            Span::styled("f", Style::default().fg(Color::Yellow)),
            Span::raw(":Filters | "),
            Span::styled("t", Style::default().fg(Color::Yellow)),
            Span::raw(":Tail | "),
            Span::styled("e", Style::default().fg(Color::Yellow)),
            Span::raw(":Export | "),
            Span::styled("r", Style::default().fg(Color::Yellow)),
            Span::raw(":Refresh | "),
            Span::styled("?", Style::default().fg(Color::Yellow)),
            Span::raw(":Help | "),
            Span::styled("q", Style::default().fg(Color::Yellow)),
            Span::raw(":Quit"),
        ])
    };

    let keybindings_widget = Paragraph::new(keybindings)
        .block(Block::default().borders(Borders::ALL))
        .style(Style::default().fg(Color::White));
    f.render_widget(keybindings_widget, chunks[2]);

    // Status message overlay
    if let Some(ref msg) = app.status_message {
        let msg_area = Rect {
            x: area.x + 2,
            y: area.y + 2,
            width: area.width.saturating_sub(4).min(msg.len() as u16 + 4),
            height: 3,
        };
        let msg_block = Block::default()
            .borders(Borders::ALL)
            .border_style(Style::default().fg(Color::Yellow));
        let msg_paragraph = Paragraph::new(msg.as_str()).block(msg_block);
        f.render_widget(msg_paragraph, msg_area);
    }
}

fn render_export_menu(f: &mut ratatui::Frame, area: Rect, selected: usize) {
    let block = Block::default()
        .title("Export Logs")
        .borders(Borders::ALL)
        .border_style(Style::default().fg(Color::Cyan));

    let items = vec![
        ListItem::new("JSON"),
        ListItem::new("CSV"),
    ];

    let list = List::new(items)
        .block(block)
        .highlight_style(
            Style::default()
                .bg(Color::DarkGray)
                .add_modifier(Modifier::BOLD),
        )
        .highlight_symbol("> ");

    let mut state = ratatui::widgets::ListState::default();
    state.select(Some(selected));

    f.render_stateful_widget(list, area, &mut state);

    // Instructions
    let instructions_area = Rect {
        x: area.x,
        y: area.y + area.height.saturating_sub(1),
        width: area.width,
        height: 1,
    };

    let instructions = Paragraph::new("↑↓:Select | Enter:Export | ESC:Cancel")
        .style(Style::default().fg(Color::Gray));
    f.render_widget(instructions, instructions_area);
}

fn centered_rect(percent_x: u16, percent_y: u16, r: Rect) -> Rect {
    let popup_layout = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Percentage((100 - percent_y) / 2),
            Constraint::Percentage(percent_y),
            Constraint::Percentage((100 - percent_y) / 2),
        ])
        .split(r);

    Layout::default()
        .direction(Direction::Horizontal)
        .constraints([
            Constraint::Percentage((100 - percent_x) / 2),
            Constraint::Percentage(percent_x),
            Constraint::Percentage((100 - percent_x) / 2),
        ])
        .split(popup_layout[1])[1]
}
