use ratatui::{
    layout::{Alignment, Constraint, Direction, Layout, Rect},
    style::{Color, Modifier, Style},
    text::{Line, Span},
    widgets::{Block, Borders, Paragraph},
    Frame,
};

pub fn render_help(f: &mut Frame, area: Rect) {
    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Percentage(10),
            Constraint::Percentage(80),
            Constraint::Percentage(10),
        ])
        .split(area);

    let help_chunks = Layout::default()
        .direction(Direction::Horizontal)
        .constraints([
            Constraint::Percentage(15),
            Constraint::Percentage(70),
            Constraint::Percentage(15),
        ])
        .split(chunks[1]);

    let help_area = help_chunks[1];

    let block = Block::default()
        .title("Help - Keybindings")
        .borders(Borders::ALL)
        .border_style(Style::default().fg(Color::Cyan));

    let help_text = vec![
        Line::from(Span::styled(
            "Navigation",
            Style::default()
                .fg(Color::Yellow)
                .add_modifier(Modifier::BOLD),
        )),
        Line::from(""),
        Line::from(vec![
            Span::styled("↑/k", Style::default().fg(Color::Green)),
            Span::raw("          Move up"),
        ]),
        Line::from(vec![
            Span::styled("↓/j", Style::default().fg(Color::Green)),
            Span::raw("          Move down"),
        ]),
        Line::from(vec![
            Span::styled("g", Style::default().fg(Color::Green)),
            Span::raw("            Go to top"),
        ]),
        Line::from(vec![
            Span::styled("G", Style::default().fg(Color::Green)),
            Span::raw("            Go to bottom"),
        ]),
        Line::from(vec![
            Span::styled("Ctrl+u", Style::default().fg(Color::Green)),
            Span::raw("        Page up"),
        ]),
        Line::from(vec![
            Span::styled("Ctrl+d", Style::default().fg(Color::Green)),
            Span::raw("        Page down"),
        ]),
        Line::from(""),
        Line::from(Span::styled(
            "Actions",
            Style::default()
                .fg(Color::Yellow)
                .add_modifier(Modifier::BOLD),
        )),
        Line::from(""),
        Line::from(vec![
            Span::styled("Enter", Style::default().fg(Color::Green)),
            Span::raw("         Show log details"),
        ]),
        Line::from(vec![
            Span::styled("f", Style::default().fg(Color::Green)),
            Span::raw("            Toggle filter panel"),
        ]),
        Line::from(vec![
            Span::styled("t", Style::default().fg(Color::Green)),
            Span::raw("            Toggle tail mode (live streaming)"),
        ]),
        Line::from(vec![
            Span::styled("e", Style::default().fg(Color::Green)),
            Span::raw("            Export logs"),
        ]),
        Line::from(vec![
            Span::styled("r", Style::default().fg(Color::Green)),
            Span::raw("            Refresh/reload logs"),
        ]),
        Line::from(vec![
            Span::styled("?", Style::default().fg(Color::Green)),
            Span::raw("            Show this help screen"),
        ]),
        Line::from(vec![
            Span::styled("q", Style::default().fg(Color::Green)),
            Span::raw("            Quit application"),
        ]),
        Line::from(vec![
            Span::styled("Esc", Style::default().fg(Color::Green)),
            Span::raw("          Close popup/cancel"),
        ]),
        Line::from(""),
        Line::from(Span::styled(
            "Filters",
            Style::default()
                .fg(Color::Yellow)
                .add_modifier(Modifier::BOLD),
        )),
        Line::from(""),
        Line::from(vec![
            Span::styled("Tab", Style::default().fg(Color::Green)),
            Span::raw("          Switch between filter fields"),
        ]),
        Line::from(vec![
            Span::styled("Space", Style::default().fg(Color::Green)),
            Span::raw("        Toggle selection (levels, app)"),
        ]),
        Line::from(vec![
            Span::styled("Enter", Style::default().fg(Color::Green)),
            Span::raw("        Apply filters"),
        ]),
        Line::from(vec![
            Span::styled("Esc", Style::default().fg(Color::Green)),
            Span::raw("          Close filter panel"),
        ]),
    ];

    let paragraph = Paragraph::new(help_text)
        .block(block)
        .alignment(Alignment::Left);

    f.render_widget(paragraph, help_area);

    let close_hint = Paragraph::new("Press ESC or ? to close")
        .alignment(Alignment::Center)
        .style(Style::default().fg(Color::Gray));

    f.render_widget(close_hint, chunks[2]);
}
