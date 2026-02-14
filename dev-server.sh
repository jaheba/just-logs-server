#!/usr/bin/env bash
set -e

# JLO Development Server Manager
# This script ensures only one instance runs and manages both backend and frontend

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIDFILE="$PROJECT_ROOT/.dev-server.pid"
LOGDIR="$PROJECT_ROOT/logs"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create logs directory
mkdir -p "$LOGDIR"

# Function to print colored output
log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

# Function to kill processes on specific ports
kill_port() {
    local port=$1
    local pids=$(lsof -ti:$port 2>/dev/null || true)
    if [ -n "$pids" ]; then
        log_warn "Killing existing process on port $port (PIDs: $pids)"
        echo "$pids" | xargs kill -9 2>/dev/null || true
        sleep 1
    fi
}

# Function to check if server is already running
check_running() {
    if [ -f "$PIDFILE" ]; then
        local pid=$(cat "$PIDFILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0  # Running
        else
            rm -f "$PIDFILE"
            return 1  # Not running
        fi
    fi
    return 1  # Not running
}

# Function to stop servers
stop_servers() {
    log_info "Stopping development servers..."
    
    # Kill by ports
    kill_port 8000
    kill_port 5173
    
    # Remove PID file
    rm -f "$PIDFILE"
    
    log_success "All servers stopped"
}

# Function to start servers
start_servers() {
    # Check if already running
    if check_running; then
        log_error "Development servers are already running!"
        log_info "Run '$0 stop' to stop them, or '$0 restart' to restart"
        exit 1
    fi
    
    # Kill any stray processes on our ports
    kill_port 8000
    kill_port 5173
    
    log_info "Starting backend server (port 8000)..."
    cd "$PROJECT_ROOT/backend"
    uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000 \
        > "$LOGDIR/backend.log" 2>&1 &
    local backend_pid=$!
    
    # Wait for backend to start
    sleep 2
    if ! ps -p $backend_pid > /dev/null; then
        log_error "Backend failed to start! Check $LOGDIR/backend.log"
        exit 1
    fi
    log_success "Backend started (PID: $backend_pid)"
    
    log_info "Starting frontend dev server (port 5173)..."
    cd "$PROJECT_ROOT/frontend"
    npm run dev > "$LOGDIR/frontend.log" 2>&1 &
    local frontend_pid=$!
    
    # Wait for frontend to start
    sleep 2
    if ! ps -p $frontend_pid > /dev/null; then
        log_error "Frontend failed to start! Check $LOGDIR/frontend.log"
        kill $backend_pid 2>/dev/null || true
        exit 1
    fi
    log_success "Frontend started (PID: $frontend_pid)"
    
    # Save main PID (we'll use backend PID as reference)
    echo $backend_pid > "$PIDFILE"
    
    echo ""
    log_success "Development servers running!"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "  ${BLUE}Backend:${NC}  http://localhost:8000"
    echo -e "  ${BLUE}Frontend:${NC} http://localhost:5173"
    echo -e "  ${BLUE}API Docs:${NC} http://localhost:8000/docs"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    log_info "Logs:"
    echo -e "  Backend:  ${LOGDIR}/backend.log"
    echo -e "  Frontend: ${LOGDIR}/frontend.log"
    echo ""
    log_info "Use '$0 logs' to tail logs"
    log_info "Use '$0 stop' to stop servers"
}

# Function to show status
show_status() {
    if check_running; then
        local pid=$(cat "$PIDFILE")
        log_success "Development servers are running (PID: $pid)"
        
        # Check ports
        local backend_running=$(lsof -ti:8000 2>/dev/null || true)
        local frontend_running=$(lsof -ti:5173 2>/dev/null || true)
        
        if [ -n "$backend_running" ]; then
            echo -e "  ${GREEN}✓${NC} Backend running on port 8000"
        else
            echo -e "  ${RED}✗${NC} Backend not running"
        fi
        
        if [ -n "$frontend_running" ]; then
            echo -e "  ${GREEN}✓${NC} Frontend running on port 5173"
        else
            echo -e "  ${RED}✗${NC} Frontend not running"
        fi
    else
        log_warn "Development servers are not running"
    fi
}

# Function to tail logs
tail_logs() {
    if [ ! -f "$LOGDIR/backend.log" ] || [ ! -f "$LOGDIR/frontend.log" ]; then
        log_error "Log files not found. Are the servers running?"
        exit 1
    fi
    
    log_info "Tailing logs (Ctrl+C to exit)..."
    echo ""
    tail -f "$LOGDIR/backend.log" "$LOGDIR/frontend.log"
}

# Function to restart servers
restart_servers() {
    log_info "Restarting development servers..."
    stop_servers
    sleep 1
    start_servers
}

# Main command handler
case "${1:-start}" in
    start)
        start_servers
        ;;
    stop)
        stop_servers
        ;;
    restart)
        restart_servers
        ;;
    status)
        show_status
        ;;
    logs)
        tail_logs
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "Commands:"
        echo "  start   - Start development servers (default)"
        echo "  stop    - Stop development servers"
        echo "  restart - Restart development servers"
        echo "  status  - Show server status"
        echo "  logs    - Tail server logs"
        exit 1
        ;;
esac
