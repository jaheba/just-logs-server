"""
Tests for API endpoints
"""

import pytest
from datetime import datetime
import json


class TestHealthEndpoint:
    """Test health check endpoint"""

    def test_health_check(self, client):
        """Test health check returns 200"""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data


class TestAuthEndpoints:
    """Test authentication endpoints"""

    def test_login_success(self, client, test_app):
        """Test successful login"""
        response = client.post(
            "/api/auth/login",
            json={"username": test_app["username"], "password": test_app["password"]},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Login successful"
        assert data["username"] == test_app["username"]
        assert data["role"] == "admin"

        # Check cookie was set
        assert "session_token" in response.cookies

    def test_login_wrong_password(self, client, test_app):
        """Test login with wrong password"""
        response = client.post(
            "/api/auth/login",
            json={"username": test_app["username"], "password": "wrongpassword"},
        )

        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        """Test login with nonexistent user"""
        response = client.post(
            "/api/auth/login", json={"username": "nonexistent", "password": "password"}
        )

        assert response.status_code == 401

    def test_get_current_user(self, client, test_app, admin_token):
        """Test getting current user info"""
        response = client.get("/api/auth/me", cookies={"session_token": admin_token})

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == test_app["username"]
        assert "password_hash" not in data  # Should not return password

    def test_get_current_user_no_auth(self, client):
        """Test getting current user without authentication"""
        response = client.get("/api/auth/me")
        assert response.status_code == 401

    def test_logout(self, client, admin_token):
        """Test logout"""
        response = client.post(
            "/api/auth/logout", cookies={"session_token": admin_token}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Logout successful"


class TestLogIngestionEndpoints:
    """Test log ingestion endpoints"""

    def test_ingest_single_log(self, client, test_app, api_headers):
        """Test ingesting a single log"""
        log_data = {
            "level": "INFO",
            "message": "Test log message",
            "timestamp": "2026-02-14T12:00:00Z",
        }

        response = client.post("/api/logs", json=log_data, headers=api_headers)

        assert response.status_code == 202
        data = response.json()
        assert "accepted" in data

    def test_ingest_log_with_structured_data(self, client, test_app, api_headers):
        """Test ingesting log with structured data"""
        log_data = {
            "level": "ERROR",
            "message": "Database error",
            "timestamp": "2026-02-14T12:00:00Z",
            "structured_data": {"error_code": "DB_CONNECTION_FAILED", "retry_count": 3},
        }

        response = client.post("/api/logs", json=log_data, headers=api_headers)

        assert response.status_code == 202

    def test_ingest_bulk_logs(self, client, test_app, api_headers, sample_logs):
        """Test ingesting multiple logs at once"""
        # Convert sample logs to have proper level format
        for log in sample_logs:
            log["level"] = log["level"].upper()

        response = client.post("/api/logs", json=sample_logs, headers=api_headers)

        assert response.status_code == 202
        data = response.json()
        assert "accepted" in data

    def test_ingest_log_without_api_key(self, client):
        """Test ingesting log without API key fails"""
        log_data = {
            "level": "info",
            "message": "Test log",
            "timestamp": "2026-02-14T12:00:00Z",
        }

        response = client.post("/api/logs", json=log_data)
        assert response.status_code == 401

    def test_ingest_log_invalid_api_key(self, client):
        """Test ingesting log with invalid API key"""
        log_data = {
            "level": "info",
            "message": "Test log",
            "timestamp": "2026-02-14T12:00:00Z",
        }

        response = client.post(
            "/api/logs", json=log_data, headers={"X-API-Key": "invalid-key"}
        )

        assert response.status_code == 401

    def test_ingest_log_missing_fields(self, client, api_headers):
        """Test ingesting log with missing required fields"""
        log_data = {
            "level": "INFO"
            # Missing message (required field)
        }

        response = client.post("/api/logs", json=log_data, headers=api_headers)

        assert response.status_code == 422  # Validation error


class TestLogQueryEndpoints:
    """Test log query endpoints"""

    def test_get_logs(self, client, test_app, admin_token, api_headers, sample_logs):
        """Test retrieving logs"""
        # First ingest some logs
        for log in sample_logs:
            log["level"] = log["level"].upper()

        client.post("/api/logs", json=sample_logs, headers=api_headers)

        # Query logs
        response = client.get(
            f"/api/logs?app_id={test_app['app_id']}",
            cookies={"session_token": admin_token},
        )

        assert response.status_code == 200
        logs = response.json()
        assert isinstance(logs, list)
        assert len(logs) >= len(sample_logs)

    def test_get_logs_with_level_filter(
        self, client, test_app, admin_token, api_headers, sample_logs
    ):
        """Test retrieving logs filtered by level"""
        # Ingest logs
        client.post("/api/logs", json={"logs": sample_logs}, headers=api_headers)

        # Query error logs only
        response = client.get(
            f"/api/logs?level=error",
            cookies={"session_token": admin_token},
        )

        assert response.status_code == 200
        data = response.json()
        error_logs = [log for log in data["logs"] if log["level"] == "error"]
        assert len(error_logs) >= 1

    def test_get_logs_with_search(self, client, test_app, admin_token, api_headers):
        """Test searching logs by message"""
        # Ingest test logs
        logs = [
            {
                "level": "info",
                "message": "User login successful",
                "timestamp": "2026-02-14T12:00:00Z",
            },
            {
                "level": "info",
                "message": "Database connection established",
                "timestamp": "2026-02-14T12:01:00Z",
            },
        ]
        client.post("/api/logs", json={"logs": logs}, headers=api_headers)

        # Search for "user"
        response = client.get(
            f"/api/logs?search=user",
            cookies={"session_token": admin_token},
        )

        assert response.status_code == 200
        data = response.json()
        # Should find at least the user login log
        assert any("user" in log["message"].lower() for log in data["logs"])

    def test_get_logs_pagination(self, client, test_app, admin_token, api_headers):
        """Test log pagination"""
        # Ingest many logs
        logs = [
            {
                "level": "info",
                "message": f"Log {i}",
                "timestamp": "2026-02-14T12:00:00Z",
            }
            for i in range(50)
        ]
        client.post("/api/logs", json={"logs": logs}, headers=api_headers)

        # Get first page
        response = client.get(
            f"/api/logs?limit=20&offset=0",
            cookies={"session_token": admin_token},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["logs"]) <= 20

    def test_get_logs_unauthorized(self, client, test_app):
        """Test getting logs without authentication"""
        response = client.get(f"/api/logs")
        assert response.status_code == 401


class TestAppManagementEndpoints:
    """Test app management endpoints"""

    def test_create_app(self, client, admin_token):
        """Test creating a new app"""
        response = client.post(
            "/api/apps",
            json={"name": "new-app"},
            cookies={"session_token": admin_token},
        )

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["name"] == "new-app"

    def test_get_all_apps(self, client, test_app, admin_token):
        """Test getting all apps"""
        response = client.get("/api/apps", cookies={"session_token": admin_token})

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(app["id"] == test_app["app_id"] for app in data)


class TestAPIKeyManagementEndpoints:
    """Test API key management endpoints"""

    def test_create_api_key(self, client, test_app, admin_token):
        """Test creating a new API key"""
        response = client.post(
            f"/api/api-keys",
            cookies={"session_token": admin_token},
        )

        assert response.status_code == 200
        data = response.json()
        assert "key" in data
        assert data["key"].startswith("jlo_")

    def test_get_api_keys(self, client, test_app, admin_token):
        """Test getting all API keys for an app"""
        response = client.get(
            f"/api/api-keys",
            cookies={"session_token": admin_token},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1  # At least the test app key

    def test_deactivate_api_key(self, client, test_app, admin_token):
        """Test deactivating an API key"""
        # Get existing key
        response = client.get(
            f"/api/api-keys",
            cookies={"session_token": admin_token},
        )
        keys = response.json()
        key_id = keys[0]["id"]

        # Deactivate
        response = client.put(
            f"/api/api-keys/{key_id}/deactivate", cookies={"session_token": admin_token}
        )

        assert response.status_code == 200


class TestUserManagementEndpoints:
    """Test user management endpoints"""

    def test_create_user(self, client, admin_token):
        """Test creating a new user"""
        response = client.post(
            "/api/users",
            json={
                "username": "newuser",
                "password": "password123",
                "email": "newuser@example.com",
                "role": "viewer",
            },
            cookies={"session_token": admin_token},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert "password" not in data

    def test_get_all_users(self, client, admin_token):
        """Test getting all users"""
        response = client.get("/api/users", cookies={"session_token": admin_token})

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_update_user(self, client, test_app, admin_token):
        """Test updating a user"""
        response = client.put(
            f"/api/users/{test_app['user_id']}",
            json={"email": "updated@example.com", "full_name": "Updated Name"},
            cookies={"session_token": admin_token},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "updated@example.com"

    def test_delete_user(self, client, admin_token):
        """Test deleting a user"""
        # Create a user to delete
        response = client.post(
            "/api/users",
            json={"username": "deleteme", "password": "password123", "role": "viewer"},
            cookies={"session_token": admin_token},
        )
        user_id = response.json()["id"]

        # Delete the user
        response = client.delete(
            f"/api/users/{user_id}", cookies={"session_token": admin_token}
        )

        assert response.status_code == 200


class TestServerSentEvents:
    """Test SSE endpoints"""

    def test_logs_stream_endpoint(self, client, test_app, admin_token):
        """Test that logs stream endpoint exists"""
        # Note: Testing actual SSE streaming is complex
        # This just verifies the endpoint is accessible
        response = client.get(
            f"/api/logs/stream",
            cookies={"session_token": admin_token},
            timeout=1,  # Short timeout
        )

        # Should start responding (200 or timeout)
        # Actual streaming would need async testing
        assert response.status_code in [200, 408]  # 408 = timeout
