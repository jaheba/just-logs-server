# jlo-tui - Terminal UI for just-logs

A powerful, terminal-based user interface for viewing and managing logs from the just-logs server. Built with Rust and [ratatui](https://github.com/ratatui/ratatui).

## Features

- **Authentication**: Login with username/password (session-based)
- **Real-time Log Viewing**: Browse logs in a clean, table-based interface
- **Advanced Filtering**: Filter by application, log level, search text, and time range
- **Live Tail Mode**: Stream logs in real-time using Server-Sent Events (SSE)
- **Log Details**: View full log entries with structured data and tags
- **Export**: Export logs to JSON or CSV format
- **Vim-like Navigation**: Familiar keybindings for efficient navigation
- **Configuration**: Customizable via config file or CLI arguments

## Installation

### Prerequisites

- Rust 1.70 or later
- A running just-logs server

### Build from Source

```bash
cd jlo-tui
cargo build --release
```

The binary will be available at `target/release/jlo-tui`.

### Optional: Install Globally

```bash
cargo install --path .
```

## Quick Start

1. **Run the TUI**:
   ```bash
   jlo-tui
   ```

2. **Login** with your just-logs credentials (default: `admin` / `admin`)

3. **Start exploring**:
   - Press `r` to refresh and load logs
   - Press `f` to open the filter panel
   - Press `t` to enable live tail mode
   - Press `?` for help

## Usage

### Command-Line Options

```bash
# Connect to a custom server
jlo-tui --server http://production.example.com:8000

# Specify username
jlo-tui --username myuser

# Use custom config file
jlo-tui --config /path/to/config.toml

# Show help
jlo-tui --help
```

### Authentication Options

There are three ways to provide credentials:

#### 1. Interactive (Most Secure - Default)
Simply run `jlo-tui` and enter credentials when prompted:
```bash
jlo-tui
# Enter username and password at login screen
```

#### 2. Environment Variable (Recommended for Automation)
Set the `JLO_PASSWORD` environment variable:
```bash
# Set password in environment
export JLO_PASSWORD="your-password"

# Pre-fill username in config or CLI
jlo-tui --username admin
# Will auto-login without prompting
```

Or use it inline:
```bash
JLO_PASSWORD="your-password" jlo-tui --username admin
```

#### 3. Command-Line Argument (Not Recommended)
⚠️ **WARNING**: Passwords passed as CLI arguments are visible in process lists and shell history!

```bash
jlo-tui --username admin --password your-password
```

**Priority order**: CLI arg > Environment variable > Interactive prompt

#### Best Practices

- **Development**: Use interactive mode (default)
- **Scripts/Automation**: Use environment variable
- **CI/CD**: Store password in secret manager, export to `JLO_PASSWORD`
- **Avoid**: Command-line password argument (security risk)

### Keybindings

#### Navigation
- `↑` or `k` - Move up
- `↓` or `j` - Move down
- `g` - Go to top
- `G` - Go to bottom
- `Ctrl+u` - Page up
- `Ctrl+d` - Page down

#### Actions
- `Enter` - Show detailed view of selected log
- `f` - Toggle filter panel
- `t` - Toggle tail mode (live streaming)
- `e` - Export logs (JSON or CSV)
- `r` - Refresh/reload logs
- `?` - Show help screen
- `q` - Quit application
- `Esc` - Close popup/cancel

#### Filter Panel
- `Tab` - Switch between filter fields
- `↑`/`↓` or `j`/`k` - Navigate options
- `Space` - Toggle selection (for apps and levels)
- `Enter` - Apply filters and close panel
- `Esc` - Close panel without applying

## Configuration

The TUI can be configured via a TOML file located at `~/.config/jlo-tui/config.toml`.

### Example Configuration

```toml
# Server connection
server_url = "http://localhost:8000"

# Optional: Pre-fill username (password is always prompted)
username = "admin"

[ui]
# Auto-refresh interval in milliseconds (when not in tail mode)
refresh_interval_ms = 5000

# Number of logs to fetch per request
page_size = 100

# Maximum logs to keep in memory
max_logs_in_memory = 10000

# Date/time format (strftime format)
date_format = "%Y-%m-%d %H:%M:%S"

# Enable colored log levels
enable_colors = true

[colors]
# Log level colors
error = "red"
warn = "yellow"
info = "green"
debug = "blue"
fatal = "magenta"
```

### Configuration Priority

1. Command-line arguments (highest priority)
2. Configuration file
3. Default values (lowest priority)

## Features in Detail

### Log Filtering

The filter panel allows you to narrow down logs based on:

- **Application**: Select a specific app or view all
- **Log Levels**: Multi-select DEBUG, INFO, WARN, ERROR, FATAL
- **Search**: Full-text search in log messages
- **Time Range**: Presets (Last 1h, 24h, 7d, All time)

### Live Tail Mode

Press `t` to enable real-time log streaming:
- New logs appear at the top automatically
- Status bar shows `[LIVE]` indicator
- Press `t` again to disable and stop streaming

### Log Details View

Press `Enter` on any log to see:
- Full log message (no truncation)
- Structured data (pretty-printed JSON)
- Tags (key-value pairs from API keys)
- Timestamps (ISO 8601 format)
- App and log level information

### Export Logs

Press `e` to export logs:
1. Choose format (JSON or CSV)
2. Press Enter to confirm
3. File is saved in current directory with timestamp

Export respects currently applied filters.

## Troubleshooting

### Connection Issues

If you can't connect to the server:
1. Verify the server is running: `curl http://localhost:8000/api/health`
2. Check the server URL in config or CLI args
3. Ensure no firewall is blocking the connection

### Authentication Failed

- Default credentials are `admin` / `admin`
- Check if the server has different credentials configured
- Verify your user account is active in the just-logs web UI

### Empty Log List

- Press `r` to refresh logs
- Check filters - you might have filtered out all logs
- Verify logs exist in the just-logs server

### Tail Mode Not Working

- Check that the just-logs server supports SSE streaming
- Verify the `/api/logs/stream` endpoint is accessible
- Check network connectivity

## Architecture

```
jlo-tui/
├── src/
│   ├── main.rs          # CLI args, terminal setup, main loop
│   ├── app.rs           # Application state and event handling
│   ├── config.rs        # Configuration management
│   ├── utils.rs         # Helper functions
│   ├── api/
│   │   ├── client.rs    # HTTP client with session management
│   │   ├── models.rs    # Data structures
│   │   └── sse.rs       # Server-Sent Events streaming
│   └── ui/
│       ├── login.rs     # Login screen
│       ├── logs.rs      # Main logs table view
│       ├── filters.rs   # Filter panel
│       └── help.rs      # Help screen
└── Cargo.toml
```

## Tech Stack

- **[ratatui](https://github.com/ratatui/ratatui)**: Terminal UI framework
- **[crossterm](https://github.com/crossterm-rs/crossterm)**: Terminal manipulation
- **[tokio](https://tokio.rs/)**: Async runtime
- **[reqwest](https://github.com/seanmonstar/reqwest)**: HTTP client with cookie support
- **[eventsource-client](https://github.com/jpopesculian/eventsource-client)**: Server-Sent Events
- **[clap](https://github.com/clap-rs/clap)**: CLI argument parsing
- **[serde](https://serde.rs/)**: Serialization/deserialization

## Development

### Running in Development

```bash
cargo run

# With custom server
cargo run -- --server http://localhost:8000

# Show verbose output
RUST_LOG=debug cargo run
```

### Code Style

```bash
# Format code
cargo fmt

# Lint
cargo clippy

# Run tests (when available)
cargo test
```

## Roadmap

Future enhancements:
- [ ] Multiple server profiles (dev/staging/prod)
- [ ] Saved filter presets
- [ ] Custom log highlighting with regex
- [ ] Log volume charts/graphs
- [ ] Pattern-based notifications
- [ ] Plugin system for custom formatters
- [ ] Pagination for large log sets
- [ ] Bookmarks/favorites

## Contributing

Contributions are welcome! Areas to improve:
- Add unit and integration tests
- Improve error handling and user feedback
- Add keyboard shortcuts customization
- Performance optimization for large log sets
- Accessibility improvements

## License

This project is part of the just-logs ecosystem.

## Related Projects

- **just-logs server**: Python FastAPI backend + Vue.js frontend
- **jlo-client**: Python client library for sending logs

## Support

For issues, questions, or feature requests, please open an issue in the repository.
