"""
Pytest configuration and shared fixtures
"""

import os
import sys
import tempfile
import sqlite3
from pathlib import Path
from typing import Generator
import pytest
from fastapi.testclient import TestClient

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import database
import auth
from main import app


@pytest.fixture(scope="function")
def test_db() -> Generator[str, None, None]:
    """
    Create a temporary test database for each test
    """
    # Create temporary database file
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    # Set database path for the test
    original_path = database.DATABASE_PATH
    database.DATABASE_PATH = db_path

    # Initialize database with migrations
    database.init_database()

    yield db_path

    # Cleanup
    database.DATABASE_PATH = original_path
    try:
        os.unlink(db_path)
    except:
        pass


@pytest.fixture(scope="function")
def db_connection(test_db: str) -> Generator[sqlite3.Connection, None, None]:
    """
    Provide a database connection for testing
    """
    conn = sqlite3.connect(test_db)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


@pytest.fixture(scope="function")
def client(test_db: str) -> Generator[TestClient, None, None]:
    """
    Provide a test client for API testing
    """
    yield TestClient(app)


@pytest.fixture(scope="function")
def test_app(test_db: str):
    """
    Create a test app with a fresh database
    """
    from database import create_app, create_api_key, create_web_user
    from auth import hash_password, generate_api_key

    # Create test app
    app_id = create_app("test-app")

    # Generate and create test API key
    api_key = generate_api_key()
    create_api_key(api_key, app_id)

    # Create test user
    user_id = create_web_user(
        username="testuser",
        password_hash=hash_password("testpass123"),
        email="test@example.com",
        full_name="Test User",
        role="admin",
    )

    return {
        "app_id": app_id,
        "api_key": api_key,
        "user_id": user_id,
        "username": "testuser",
        "password": "testpass123",
    }


@pytest.fixture(scope="function")
def admin_token(client: TestClient, test_app: dict) -> str:
    """
    Get an admin authentication token for testing
    """
    response = client.post(
        "/api/auth/login",
        json={"username": test_app["username"], "password": test_app["password"]},
    )
    assert response.status_code == 200

    # Extract token from cookie
    cookies = response.cookies
    return cookies.get("session_token", "")


@pytest.fixture(scope="function")
def api_headers(test_app: dict) -> dict:
    """
    Get headers with API key for log ingestion testing
    """
    return {"X-API-Key": test_app["api_key"]}


@pytest.fixture
def sample_logs():
    """
    Sample log data for testing
    """
    return [
        {
            "level": "INFO",
            "message": "Application started successfully",
            "timestamp": "2026-02-14T12:00:00Z",
        },
        {
            "level": "WARN",
            "message": "High memory usage detected",
            "timestamp": "2026-02-14T12:05:00Z",
            "structured_data": {"memory_mb": 1024, "threshold_mb": 800},
        },
        {
            "level": "ERROR",
            "message": "Database connection failed",
            "timestamp": "2026-02-14T12:10:00Z",
            "structured_data": {"error": "Connection timeout", "retry_count": 3},
        },
    ]


@pytest.fixture
def sample_parsing_rule():
    """
    Sample parsing rule for testing
    """
    return {
        "name": "Apache Access Log",
        "parser_type": "grok",
        "pattern": "%{COMBINEDAPACHELOG}",
        "enabled": True,
        "priority": 10,
    }


@pytest.fixture
def sample_retention_policy():
    """
    Sample retention policy for testing
    """
    return {
        "priority_tier": "low",
        "retention_type": "time_based",
        "retention_days": 7,
        "enabled": True,
    }
