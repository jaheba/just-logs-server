# Multi-stage Docker build for JLO (Just Logs)
# Optimized for production deployment

# Stage 1: Build frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy frontend package files
COPY frontend/package*.json ./

# Install dependencies (including dev dependencies needed for build)
RUN npm ci

# Copy frontend source
COPY frontend/ ./

# Build frontend for production
RUN npm run build

# Stage 2: Build backend with uv
FROM python:3.11-slim AS backend-builder

WORKDIR /app

# Install uv for fast dependency management
RUN pip install --no-cache-dir uv

# Copy backend files
COPY backend/ ./backend/

# Install backend dependencies
WORKDIR /app/backend
RUN uv sync --no-dev

# Stage 3: Production runtime
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    sqlite3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=backend-builder /app/backend/.venv /app/backend/.venv

# Copy backend application
COPY backend/ /app/backend/

# Copy built frontend from builder
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Create volume mount point for database
RUN mkdir -p /app/backend/data

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/backend/.venv/bin:$PATH" \
    JLO_DB_PATH=/app/backend/data/jlo.db \
    JLO_HOST=0.0.0.0 \
    JLO_PORT=8000 \
    JLO_WORKERS=4

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Set working directory to backend
WORKDIR /app/backend

# Run database initialization and start server
CMD ["sh", "-c", "python -c 'from database import init_database; init_database()' && uvicorn main:app --host ${JLO_HOST} --port ${JLO_PORT} --workers ${JLO_WORKERS}"]
