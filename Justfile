# JLO (Just Logs) - Project Build Automation
# Requires: just (https://github.com/casey/just)
# Install: brew install just

# Default recipe - show available commands
default:
    @just --list

# ============================================
# Development Commands
# ============================================

# Start development servers (both backend and frontend with auto-reload)
dev:
    @./dev-server.sh start

# Stop development servers
dev-stop:
    @./dev-server.sh stop

# Restart development servers
dev-restart:
    @./dev-server.sh restart

# Show development server status
dev-status:
    @./dev-server.sh status

# Tail development logs
dev-logs:
    @./dev-server.sh logs

# Start backend development server only
dev-backend:
    @echo "🚀 Starting backend development server..."
    cd backend && uv run uvicorn main:app --reload --port 8000

# Start frontend development server only
dev-frontend:
    @echo "🚀 Starting frontend development server..."
    cd frontend && npm run dev

# Start development with tmux (split panes) - alternative to 'just dev'
dev-tmux:
    #!/usr/bin/env bash
    tmux new-session -d -s jlo 'cd backend && uv run uvicorn main:app --reload --port 8000'
    tmux split-window -h -t jlo 'cd frontend && npm run dev'
    tmux attach -t jlo

# ============================================
# Build Commands
# ============================================

# Build frontend for production
build-frontend:
    @echo "📦 Building frontend..."
    cd frontend && npm install && npm run build
    @echo "✅ Frontend built successfully! Output in frontend/dist/"

# Watch frontend files and auto-rebuild production bundle on changes
build-watch:
    @./watch-build.sh

# Install backend dependencies
build-backend:
    @echo "📦 Installing backend dependencies..."
    cd backend && uv sync
    @echo "✅ Backend dependencies installed!"

# Build everything (frontend + backend deps)
build: build-backend build-frontend
    @echo "✅ Full build complete!"

# Clean build artifacts
clean:
    @echo "🧹 Cleaning build artifacts..."
    rm -rf frontend/dist
    rm -rf frontend/node_modules/.vite
    rm -rf backend/.venv
    rm -rf backend/__pycache__
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    @echo "✅ Clean complete!"

# ============================================
# Install Commands
# ============================================

# Install all dependencies (backend + frontend)
install: install-backend install-frontend
    @echo "✅ All dependencies installed!"

# Install backend dependencies
install-backend:
    @echo "📦 Installing backend dependencies..."
    cd backend && uv sync
    @echo "✅ Backend dependencies installed!"

# Install frontend dependencies
install-frontend:
    @echo "📦 Installing frontend dependencies..."
    cd frontend && npm install
    @echo "✅ Frontend dependencies installed!"

# ============================================
# Production Commands
# ============================================

# Run production server (backend serves frontend)
serve: build-frontend
    @echo "🚀 Starting production server..."
    cd backend && uv run uvicorn main:app --host 0.0.0.0 --port 8000

# Preview production build locally
preview: build-frontend
    @echo "👀 Previewing production build..."
    cd frontend && npm run preview

# ============================================
# Database Commands
# ============================================

# Initialize database and create admin user
db-init:
    @echo "🗄️  Initializing database..."
    cd backend && uv run python -c "from database import init_db; from auth import create_admin_user; init_db(); create_admin_user('admin', 'admin')"
    @echo "✅ Database initialized! Default login: admin/admin"

# Reset database (WARNING: deletes all data)
db-reset:
    @echo "⚠️  WARNING: This will delete all data!"
    @read -p "Are you sure? [y/N] " -n 1 -r; echo; [[ $$REPLY =~ ^[Yy]$$ ]] || exit 1
    rm -f backend/logs.db
    just db-init
    @echo "✅ Database reset complete!"

# Backup database
db-backup:
    @echo "💾 Backing up database..."
    mkdir -p backups
    cp backend/logs.db backups/logs-$(date +%Y%m%d-%H%M%S).db
    @echo "✅ Database backed up to backups/"

# ============================================
# Testing & Quality Commands
# ============================================

# Run backend tests (if you add them)
test-backend:
    @echo "🧪 Running backend tests..."
    cd backend && uv run pytest

# Run frontend tests (if you add them)
test-frontend:
    @echo "🧪 Running frontend tests..."
    cd frontend && npm run test

# Run all tests
test: test-backend test-frontend
    @echo "✅ All tests passed!"

# Check backend code with linters
lint-backend:
    @echo "🔍 Linting backend..."
    cd backend && uv run ruff check . || true
    cd backend && uv run mypy . || true

# Check frontend code with linters
lint-frontend:
    @echo "🔍 Linting frontend..."
    cd frontend && npm run lint || true

# Lint everything
lint: lint-backend lint-frontend

# ============================================
# Example/Demo Commands
# ============================================

# Send example logs to test the system
demo-logs:
    @echo "📤 Sending example logs..."
    @echo "Make sure backend is running on port 8000"
    python quickstart.py

# Run comprehensive example logger
demo-full:
    @echo "📤 Running full logging demo..."
    @echo "Make sure backend is running on port 8000"
    python example_logger.py

# ============================================
# Maintenance Commands
# ============================================

# Update all dependencies
update:
    @echo "⬆️  Updating dependencies..."
    cd backend && uv sync --upgrade
    cd frontend && npm update
    @echo "✅ Dependencies updated!"

# Check system requirements
check:
    @echo "🔍 Checking system requirements..."
    @echo "Python version:"
    @python3 --version || echo "❌ Python not found"
    @echo "\nNode version:"
    @node --version || echo "❌ Node not found"
    @echo "\nnpm version:"
    @npm --version || echo "❌ npm not found"
    @echo "\nuv version:"
    @uv --version || echo "❌ uv not installed (install: curl -LsSf https://astral.sh/uv/install.sh | sh)"
    @echo "\nBackend dependencies:"
    @cd backend && uv pip list 2>/dev/null | head -5 || echo "Run: just install-backend"
    @echo "\nFrontend dependencies:"
    @test -d frontend/node_modules && echo "✅ Installed" || echo "❌ Not installed (run: just install-frontend)"

# Show project info
info:
    @echo "📊 JLO (Just Logs) Project Info"
    @echo "================================"
    @echo "Project: Centralized Logging Server"
    @echo "Backend: FastAPI + SQLite"
    @echo "Frontend: Vue 3 + Vite"
    @echo ""
    @echo "URLs:"
    @echo "  Development Frontend: http://localhost:5173"
    @echo "  Backend API: http://localhost:8000"
    @echo "  API Docs: http://localhost:8000/docs"
    @echo ""
    @echo "Default Credentials:"
    @echo "  Username: admin"
    @echo "  Password: admin"
    @echo ""
    @echo "Quick Start:"
    @echo "  1. just install       # Install dependencies"
    @echo "  2. just db-init       # Initialize database"
    @echo "  3. just dev-backend   # Start backend (terminal 1)"
    @echo "  4. just dev-frontend  # Start frontend (terminal 2)"
    @echo ""
    @echo "Production:"
    @echo "  just build && just serve"

# ============================================
# Docker Commands (Future)
# ============================================

# Build Docker image (if Dockerfile exists)
docker-build:
    @echo "🐳 Building Docker image..."
    docker build -t jlo:latest .

# Run Docker container
docker-run:
    @echo "🐳 Running Docker container..."
    docker run -p 8000:8000 -v $(pwd)/backend/logs.db:/app/backend/logs.db jlo:latest

# ============================================
# Release Commands
# ============================================

# Create a release build
release: clean install build
    @echo "🎉 Release build complete!"
    @echo "Files ready in frontend/dist/"
    @echo "Deploy with: just serve"

# Package for distribution
package: release
    @echo "📦 Creating distribution package..."
    mkdir -p dist
    tar -czf dist/jlo-$(date +%Y%m%d-%H%M%S).tar.gz \
        backend/ \
        frontend/dist/ \
        frontend/package.json \
        frontend/package-lock.json \
        *.py \
        *.md \
        Justfile \
        --exclude backend/__pycache__ \
        --exclude backend/.venv \
        --exclude backend/logs.db
    @echo "✅ Package created in dist/"
