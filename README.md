# jlo - Just Logs

A simple, lightweight logging server for collecting and viewing application logs.

> **📦 Built with [uv](https://docs.astral.sh/uv/)** - Fast, reliable Python package management

## Features

- **HTTP-based Log Ingestion**: Send logs via simple HTTP POST requests
- **Structured & Unstructured Logs**: Support for both plain text and JSON structured data
- **Application Grouping**: Organize logs by application/service
- **API Key Authentication**: Secure log ingestion with API keys
- **Real-time Streaming**: Live log updates using Server-Sent Events (SSE)
- **Advanced Filtering**: Search and filter by app, level, time range, and text
- **Log Levels**: DEBUG, INFO, WARN, ERROR, FATAL
- **Export Functionality**: Export logs as JSON or CSV
- **Web UI**: Beautiful Vue.js interface for viewing and managing logs
- **SQLite Backend**: Simple, file-based database with raw SQL (no ORM)

## Quick Start

### Prerequisites

- **uv** - Fast Python package manager ([install instructions](https://docs.astral.sh/uv/getting-started/installation/))
- **Node.js 16+** (for frontend development)
- **just** (optional but recommended) - Command runner ([install instructions](https://github.com/casey/just))

### Installation & Running

**🚀 Recommended way - Using just:**
```bash
# Install dependencies
just install

# Initialize database
just db-init

# Start development (both servers with auto-reload)
just dev

# Check status
just dev-status

# View logs
just dev-logs

# Stop servers
just dev-stop
```

See [DEV_GUIDE.md](DEV_GUIDE.md) for detailed development workflow and [JUSTFILE.md](JUSTFILE.md) for all available commands.

**Alternative - Use the startup script:**
```bash
./start.sh
```

This will:
- Install backend dependencies with `uv`
- Optionally build the frontend
- Start the server at http://localhost:8000

**Manual installation:**

1. **Clone the repository**
```bash
git clone <repository-url>
cd just-logging
```

2. **Install backend dependencies with uv**
```bash
cd backend
uv sync
```

3. **Install frontend dependencies** (optional, for development)
```bash
cd ../frontend
npm install
```

### Running in Production Mode

1. **Build the frontend**
```bash
cd frontend
npm run build
```

2. **Start the backend server**
```bash
cd ../backend
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

3. **Access the application**
   - Web UI: http://localhost:8000
   - API: http://localhost:8000/api
   - Default credentials: `admin` / `admin`

### Running in Development Mode

1. **Start the backend**
```bash
cd backend
uv run uvicorn main:app --reload --port 8000
```

2. **Start the frontend dev server** (in another terminal)
```bash
cd frontend
npm run dev
```

3. **Access the application**
   - Frontend dev server: http://localhost:5173
   - Backend API: http://localhost:8000/api

## Usage

### Web UI

1. Login with default credentials: `admin` / `admin`
2. Create an application in the "Apps" section
3. Generate an API key in the "API Keys" section
4. Use the API key to send logs (see examples below)
5. View logs in real-time on the dashboard

### Sending Logs via HTTP

#### Single Log Entry

```bash
curl -X POST http://localhost:8000/api/logs \
  -H "X-API-Key: your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "level": "INFO",
    "message": "User logged in successfully",
    "structured_data": {
      "user_id": 12345,
      "ip_address": "192.168.1.1"
    }
  }'
```

#### Batch Logs

```bash
curl -X POST http://localhost:8000/api/logs/batch \
  -H "X-API-Key: your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "logs": [
      {
        "level": "INFO",
        "message": "Application started"
      },
      {
        "level": "ERROR",
        "message": "Failed to connect to database",
        "structured_data": {
          "error": "Connection timeout",
          "retry_count": 3
        }
      }
    ]
  }'
```

### Python Client Example

Create a file `jlo_client.py`:

```python
import requests
from datetime import datetime
from typing import Optional, Dict, Any

class JloClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            'X-API-Key': api_key,
            'Content-Type': 'application/json'
        }
    
    def log(self, level: str, message: str, structured_data: Optional[Dict[str, Any]] = None):
        """Send a single log entry"""
        payload = {
            'level': level,
            'message': message,
            'timestamp': datetime.utcnow().isoformat()
        }
        if structured_data:
            payload['structured_data'] = structured_data
        
        response = requests.post(
            f'{self.base_url}/api/logs',
            json=payload,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def debug(self, message: str, **kwargs):
        return self.log('DEBUG', message, kwargs if kwargs else None)
    
    def info(self, message: str, **kwargs):
        return self.log('INFO', message, kwargs if kwargs else None)
    
    def warn(self, message: str, **kwargs):
        return self.log('WARN', message, kwargs if kwargs else None)
    
    def error(self, message: str, **kwargs):
        return self.log('ERROR', message, kwargs if kwargs else None)
    
    def fatal(self, message: str, **kwargs):
        return self.log('FATAL', message, kwargs if kwargs else None)

# Usage example
if __name__ == '__main__':
    logger = JloClient('http://localhost:8000', 'your-api-key-here')
    
    # Simple log
    logger.info('Application started')
    
    # Log with structured data
    logger.error('Database connection failed', 
                 error='Connection timeout',
                 retry_count=3,
                 database='postgres')
    
    # Log with custom data
    logger.warn('High memory usage detected',
                memory_percent=85.5,
                threshold=80.0,
                hostname='server-01')
```

## API Documentation

### Authentication

**For Log Ingestion:**
- Use `X-API-Key` header with your API key

**For Web UI:**
- Login via `/api/auth/login` to receive a session cookie
- Session cookie is automatically included in subsequent requests

### Endpoints

#### Log Ingestion (requires API key)

**POST `/api/logs`** - Send a single log entry
- Body: `{ "level": "INFO", "message": "...", "structured_data": {...}, "timestamp": "..." }`
- Response: `{ "id": 123, "message": "Log created successfully" }`

**POST `/api/logs/batch`** - Send multiple log entries
- Body: `{ "logs": [{ "level": "INFO", "message": "..." }, ...] }`
- Response: `{ "count": 5, "message": "Created 5 logs" }`

#### Log Retrieval (requires web session)

**GET `/api/logs`** - Get logs with filtering
- Query params: `app_id`, `level`, `search`, `start_time`, `end_time`, `limit`, `offset`
- Response: Array of log objects

**GET `/api/logs/count`** - Count logs matching filters
- Query params: `app_id`, `level`, `search`, `start_time`, `end_time`
- Response: `{ "total": 1234 }`

**GET `/api/logs/stream`** - Real-time log streaming (SSE)
- Response: Server-Sent Events stream

**GET `/api/logs/export`** - Export logs
- Query params: `format` (json/csv), plus filters
- Response: JSON or CSV file

#### Application Management (requires web session)

**GET `/api/apps`** - List all applications
**POST `/api/apps`** - Create new application
- Body: `{ "name": "my-service" }`

#### API Key Management (requires web session)

**GET `/api/api-keys`** - List all API keys
**POST `/api/api-keys`** - Generate new API key
- Body: `{ "app_id": 1 }`
**DELETE `/api/api-keys/{id}`** - Revoke an API key

#### Authentication

**POST `/api/auth/login`** - Login to web UI
- Body: `{ "username": "admin", "password": "admin" }`
**POST `/api/auth/logout`** - Logout
**GET `/api/auth/me`** - Get current user

#### Health Check

**GET `/api/health`** - Service health status

## Database Schema

### apps
- `id` - Integer, primary key
- `name` - Text, unique
- `created_at` - Timestamp

### api_keys
- `id` - Integer, primary key
- `key` - Text, unique (indexed)
- `app_id` - Foreign key to apps
- `is_active` - Boolean
- `created_at` - Timestamp

### logs
- `id` - Integer, primary key
- `app_id` - Foreign key to apps
- `level` - Text (DEBUG, INFO, WARN, ERROR, FATAL)
- `message` - Text
- `structured_data` - JSON text
- `timestamp` - Timestamp (indexed)
- `created_at` - Timestamp

### web_users
- `id` - Integer, primary key
- `username` - Text, unique
- `password_hash` - Text
- `created_at` - Timestamp

## Configuration

### Backend Configuration

Edit `backend/auth.py` to customize:
- `SECRET_KEY` - JWT secret (use environment variable in production)
- `ACCESS_TOKEN_EXPIRE_MINUTES` - Session duration

### Frontend Configuration

Edit `frontend/vite.config.js` to customize:
- Development proxy settings
- Build output directory

## Deployment Considerations

### Security
1. **Change default admin password** immediately after first login
2. **Use HTTPS** in production
3. **Set SECRET_KEY** via environment variable
4. **Implement rate limiting** for log ingestion endpoints
5. **Regular API key rotation**

### Performance
1. **Database indexes** are already in place for common queries
2. Consider **SQLite WAL mode** for concurrent writes:
   ```python
   conn.execute("PRAGMA journal_mode=WAL")
   ```
3. For high-volume logging, consider:
   - Batch log ingestion
   - Background log processing
   - Periodic log archival

### Scaling
For high-scale deployments, consider:
- Migrating to PostgreSQL/MySQL
- Adding message queue (RabbitMQ/Redis) for log buffering
- Horizontal scaling with load balancer
- Separate read/write database replicas

## License

MIT License - feel free to use and modify as needed.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues.
