# jlo-tui - Project Summary

## Overview

A fully-featured Terminal User Interface (TUI) for the just-logs server, written in Rust. Provides a powerful, keyboard-driven interface for viewing, filtering, and managing logs in the terminal.

## Project Statistics

- **Total Lines of Code**: ~3,000 lines of Rust
- **Source Files**: 13 Rust modules
- **Binary Size**: 8.0 MB (release build)
- **Dependencies**: 15 direct dependencies
- **Build Time**: ~26 seconds (release)

## Architecture

### Module Structure

```
src/
├── main.rs              (265 lines)  - CLI args, terminal setup, event loop
├── app.rs               (308 lines)  - Application state and logic
├── config.rs            (167 lines)  - Configuration management
├── utils.rs             (17 lines)   - Helper utilities
├── api/
│   ├── mod.rs           (6 lines)    - Module exports
│   ├── client.rs        (255 lines)  - HTTP client with sessions
│   ├── models.rs        (121 lines)  - Data structures
│   └── sse.rs           (52 lines)   - Server-Sent Events streaming
└── ui/
    ├── mod.rs           (9 lines)    - Module exports
    ├── login.rs         (168 lines)  - Login screen
    ├── logs.rs          (210 lines)  - Main logs table view
    ├── filters.rs       (446 lines)  - Advanced filter panel
    └── help.rs          (105 lines)  - Help/keybindings screen
```

### Key Components

#### 1. **API Layer** (`src/api/`)
- **client.rs**: RESTful HTTP client with cookie-based authentication
  - Login/logout
  - Fetch logs with filters
  - Fetch applications list
  - Export logs (JSON/CSV)
  - Session management with reqwest cookie store
  
- **models.rs**: Type-safe data structures
  - `Log`: Log entry with structured data and tags
  - `LogFilters`: Query parameters for filtering
  - `Application`: App metadata
  - `LoginRequest/Response`: Authentication
  - Enums: `LogLevel`, `ExportFormat`

- **sse.rs**: Real-time log streaming
  - Server-Sent Events client
  - Async message channel
  - Automatic reconnection handling

#### 2. **UI Layer** (`src/ui/`)
- **login.rs**: Login screen
  - Username/password input fields
  - Tab navigation
  - Error display
  - Visual feedback

- **logs.rs**: Main logs table view
  - Column-based table (Timestamp, Level, App, Message)
  - Color-coded log levels
  - Row selection and navigation
  - Truncation for long messages
  - Detail view popup with full log data

- **filters.rs**: Advanced filtering
  - Application selector (radio buttons)
  - Log level multi-select (checkboxes)
  - Time range presets (1h, 24h, 7d, all)
  - Text search input
  - Tab navigation between fields

- **help.rs**: Contextual help screen
  - Keybindings reference
  - Navigation guide
  - Action descriptions

#### 3. **Application Logic** (`src/app.rs`)
- State machine with 6 states:
  - `Login`: Authentication screen
  - `Main`: Logs table view
  - `FilterPanel`: Filter overlay
  - `LogDetail`: Detail popup
  - `Help`: Help screen
  - `ExportMenu`: Export format selection

- Event handling for all states
- Async API calls
- Stream polling for tail mode
- Status message management

#### 4. **Configuration** (`src/config.rs`)
- TOML-based configuration
- Default values with overrides
- CLI argument integration
- XDG-compliant config location (`~/.config/jlo-tui/`)
- Customizable:
  - Server URL
  - UI preferences (refresh interval, page size)
  - Date format
  - Log level colors

#### 5. **Main Loop** (`src/main.rs`)
- Terminal setup/teardown
- Event polling (100ms interval)
- Keyboard event handling
- Screen rendering
- Graceful shutdown

## Features Implemented

### Core Features ✅
- [x] Username/password authentication
- [x] Session cookie management
- [x] Log table view with scrolling
- [x] Vim-like navigation (j/k, g/G, Ctrl+u/d)
- [x] Color-coded log levels
- [x] Log detail popup view

### Filtering ✅
- [x] Filter by application
- [x] Filter by log levels (multi-select)
- [x] Full-text search
- [x] Time range presets
- [x] Filter panel UI

### Real-time Features ✅
- [x] Live tail mode (SSE streaming)
- [x] Auto-scroll for new logs
- [x] LIVE indicator in status bar
- [x] Manual refresh

### Export ✅
- [x] Export to JSON
- [x] Export to CSV
- [x] Timestamped filenames
- [x] Format selection menu

### UI/UX ✅
- [x] Help screen with keybindings
- [x] Status messages
- [x] Error handling and display
- [x] Responsive layout
- [x] Popup overlays

### Configuration ✅
- [x] Config file support
- [x] CLI argument overrides
- [x] Customizable colors
- [x] Customizable date format

## Technical Highlights

### Rust & Performance
- **Async/await**: Tokio runtime for non-blocking I/O
- **Type safety**: Compile-time guarantees for correctness
- **Memory efficient**: Bounded log buffer (configurable)
- **Zero-copy**: Efficient string handling

### TUI Framework (ratatui)
- **Declarative UI**: Composable widgets
- **Efficient rendering**: Only updates changed areas
- **Cross-platform**: Works on Linux, macOS, Windows
- **Terminal agnostic**: Supports various terminal emulators

### HTTP Client (reqwest)
- **Cookie jar**: Automatic session management
- **Async**: Non-blocking network calls
- **TLS support**: Secure HTTPS connections
- **Connection pooling**: Reuses connections

### SSE Streaming
- **eventsource-client**: Standards-compliant SSE
- **Async channels**: Decoupled streaming and UI
- **Error recovery**: Graceful handling of disconnects

## User Experience

### Workflow
1. **Start**: `jlo-tui` → Login screen
2. **Authenticate**: Enter credentials → Main view
3. **View Logs**: Automatic table with recent logs
4. **Filter**: Press `f` → Configure filters → Apply
5. **Tail**: Press `t` → Real-time streaming enabled
6. **Details**: Select log → Press Enter → Full view
7. **Export**: Press `e` → Choose format → Save file

### Keyboard-Driven
- No mouse required
- Vim-inspired navigation
- Context-sensitive keybindings
- Quick actions (single key)

### Visual Feedback
- Color-coded log levels
- Selection highlighting
- Status bar with server info
- Live mode indicator
- Status messages for actions

## Testing

### Manual Testing Checklist
- [x] Login with valid credentials
- [x] Login with invalid credentials (error display)
- [x] Fetch and display logs
- [x] Navigate logs (up/down, page up/down)
- [x] Open filter panel
- [x] Apply filters (app, level, search, time)
- [x] View log details
- [x] Enable/disable tail mode
- [x] Export logs (JSON and CSV)
- [x] Show help screen
- [x] Quit application

### Future Testing
- [ ] Unit tests for API client
- [ ] Unit tests for filter logic
- [ ] Integration tests with mock server
- [ ] UI snapshot tests
- [ ] Performance tests with large log datasets

## Build & Deployment

### Development Build
```bash
cargo build
# Binary: target/debug/jlo-tui (with debug symbols)
```

### Release Build
```bash
cargo build --release
# Binary: target/release/jlo-tui (optimized, 8MB)
```

### Installation
```bash
cargo install --path .
# Installs to ~/.cargo/bin/jlo-tui
```

## Configuration Example

**~/.config/jlo-tui/config.toml**:
```toml
server_url = "http://localhost:8000"
username = "admin"

[ui]
refresh_interval_ms = 5000
page_size = 100
max_logs_in_memory = 10000
date_format = "%Y-%m-%d %H:%M:%S"
enable_colors = true

[colors]
error = "red"
warn = "yellow"
info = "green"
debug = "blue"
fatal = "magenta"
```

## Dependencies

### Core
- `ratatui` 0.28 - TUI framework
- `crossterm` 0.28 - Terminal control
- `tokio` 1.x - Async runtime

### HTTP & API
- `reqwest` 0.12 - HTTP client
- `eventsource-client` 0.13 - SSE streaming
- `futures-util` 0.3 - Async utilities

### Serialization
- `serde` 1.0 - Serialization framework
- `serde_json` 1.0 - JSON support

### Configuration
- `config` 0.14 - Config file management
- `toml` 0.8 - TOML parsing
- `dirs` 5.0 - Standard directories

### CLI & Error Handling
- `clap` 4.x - CLI argument parsing
- `anyhow` 1.0 - Error handling
- `thiserror` 1.0 - Error types

### Utilities
- `chrono` 0.4 - Date/time
- `unicode-width` 0.1 - Unicode handling

## Known Limitations

1. **Session expiration**: User must manually restart and re-login
2. **Large datasets**: May slow down with >10,000 logs in memory
3. **No pagination UI**: Loads configured page size only
4. **Single server**: No multi-server profile support yet
5. **No log editing**: Read-only view
6. **Terminal size**: Requires minimum 80x24 terminal

## Future Enhancements

### High Priority
- Session refresh/re-authentication
- Virtual scrolling for unlimited logs
- Pagination controls
- Log count/stats display

### Medium Priority
- Saved filter presets
- Multi-server profiles
- Custom color themes
- Regex-based highlighting

### Low Priority
- Log bookmarks
- Export with custom fields
- Notification system
- Plugin architecture

## Comparison with Web UI

| Feature | jlo-tui | Web UI |
|---------|---------|--------|
| **Environment** | Terminal | Browser |
| **Navigation** | Keyboard | Mouse + Keyboard |
| **Performance** | Fast, native | Depends on browser |
| **Resource Usage** | ~20MB RAM | ~100MB+ RAM |
| **Accessibility** | SSH-friendly | Requires GUI |
| **Advanced Filters** | ✅ | ✅ |
| **Real-time Streaming** | ✅ | ✅ |
| **Export** | ✅ | ✅ |
| **User Management** | ❌ | ✅ |
| **API Key Management** | ❌ | ✅ |
| **Retention Policies** | ❌ | ✅ |
| **Multiple Tabs** | ❌ | ✅ |
| **Rich Formatting** | Limited | Full |

## Conclusion

The jlo-tui provides a powerful, efficient, and keyboard-driven alternative to the web UI for viewing and managing logs. It's particularly well-suited for:
- SSH/remote server access
- Developers comfortable with terminal workflows
- Low-resource environments
- Quick log inspection and debugging
- Integration with terminal-based workflows

The implementation demonstrates modern Rust best practices, async programming, and terminal UI development with ratatui.
