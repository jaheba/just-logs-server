# Backend Test Suite

Comprehensive test suite for the just-logging backend application.

## Overview

The test suite covers:
- **Database Operations** - CRUD operations for all database models
- **Authentication & Authorization** - Password hashing, JWT tokens, API keys, roles
- **API Endpoints** - All REST API endpoints
- **Migration System** - Database migration functionality
- **Integration Tests** - End-to-end testing of complete workflows

## Test Structure

```
tests/
├── __init__.py           # Package initialization
├── conftest.py           # Shared fixtures and configuration
├── test_database.py      # Database operation tests
├── test_auth.py          # Authentication tests
├── test_api.py           # API endpoint tests
└── test_migrations.py    # Migration system tests
```

## Running Tests

### Quick Start

Run all tests:
```bash
cd backend
uv run pytest
```

Or using the test runner script:
```bash
cd backend
./run_tests.sh
```

Or if you have pytest in your environment:
```bash
cd backend
pytest
```

### Run Specific Test Files

```bash
# Run only database tests
uv run pytest tests/test_database.py

# Run only API tests
uv run pytest tests/test_api.py

# Run only auth tests
uv run pytest tests/test_auth.py
```

### Run Specific Test Classes

```bash
# Run tests for app operations
uv run pytest tests/test_database.py::TestAppOperations

# Run tests for log ingestion
uv run pytest tests/test_api.py::TestLogIngestionEndpoints
```

### Run Specific Tests

```bash
# Run a single test
uv run pytest tests/test_database.py::TestAppOperations::test_create_app

# Run tests matching a pattern
uv run pytest -k "test_create"
```

### Run with Coverage

```bash
# Generate coverage report
uv run pytest --cov=. --cov-report=html --cov-report=term

# View HTML report
open htmlcov/index.html
```

### Run with Markers

```bash
# Run only unit tests
uv run pytest -m unit

# Run only integration tests
uv run pytest -m integration

# Run all except slow tests
uv run pytest -m "not slow"

# Run database tests
uv run pytest -m database
```

## Environment Variables

Set environment variables for test configuration:

```bash
# Disable coverage
COVERAGE=false ./run_tests.sh

# Run specific markers
MARKERS="unit" ./run_tests.sh

# Run specific test path
./run_tests.sh tests/test_database.py
```

## Writing Tests

### Test Structure

Follow this pattern for test classes:

```python
class TestFeatureName:
    """Test feature description"""
    
    def test_specific_behavior(self, test_db):
        """Test that specific behavior works"""
        # Arrange
        expected = "value"
        
        # Act
        result = function_under_test()
        
        # Assert
        assert result == expected
```

### Using Fixtures

#### test_db
Provides a fresh temporary database for each test:

```python
def test_something(self, test_db):
    """Test uses isolated database"""
    app_id = database.create_app("test-app")
    assert app_id > 0
```

#### client
Provides a FastAPI test client:

```python
def test_api_endpoint(self, client):
    """Test API endpoint"""
    response = client.get("/api/health")
    assert response.status_code == 200
```

#### test_app
Provides a pre-configured app with API key and user:

```python
def test_with_app(self, test_app):
    """Test with existing app"""
    app_id = test_app["app_id"]
    api_key = test_app["api_key"]
    # Use app for testing
```

#### admin_token
Provides an authenticated admin token:

```python
def test_authenticated_endpoint(self, client, admin_token):
    """Test endpoint requiring authentication"""
    response = client.get(
        "/api/users",
        cookies={"token": admin_token}
    )
    assert response.status_code == 200
```

#### api_headers
Provides headers with API key for log ingestion:

```python
def test_log_ingestion(self, client, api_headers):
    """Test ingesting logs"""
    response = client.post(
        "/api/logs",
        json={"level": "info", "message": "test"},
        headers=api_headers
    )
    assert response.status_code == 200
```

### Test Markers

Add markers to categorize tests:

```python
@pytest.mark.slow
def test_slow_operation(self):
    """Test that takes a long time"""
    pass

@pytest.mark.integration
def test_complete_workflow(self, client, test_app):
    """Test end-to-end workflow"""
    pass

@pytest.mark.database
def test_database_query(self, test_db):
    """Test database operations"""
    pass
```

## Test Coverage

Current test coverage:

- **Database Operations**: ~95% coverage
  - App CRUD
  - API Key management
  - Log operations
  - User management

- **Authentication**: ~90% coverage
  - Password hashing
  - JWT tokens
  - API key validation
  - Role-based access

- **API Endpoints**: ~85% coverage
  - Health checks
  - Auth endpoints
  - Log ingestion
  - Query endpoints
  - Management endpoints

- **Migrations**: ~90% coverage
  - Migration discovery
  - Application
  - Rollback
  - Status tracking

## Best Practices

### 1. Test Isolation

Each test should be independent:

```python
def test_create_app(self, test_db):
    """Each test gets a fresh database"""
    # This won't affect other tests
    database.create_app("test-app")
```

### 2. Descriptive Names

Use clear, descriptive test names:

```python
# Good
def test_create_app_with_valid_name_returns_app_id(self):
    pass

# Bad
def test_app(self):
    pass
```

### 3. Test One Thing

Each test should verify one behavior:

```python
# Good
def test_create_app_returns_id(self, test_db):
    app_id = database.create_app("test")
    assert app_id > 0

def test_create_app_stores_name(self, test_db):
    app_id = database.create_app("test-name")
    app = database.get_app_by_id(app_id)
    assert app["name"] == "test-name"

# Bad - testing multiple things
def test_create_app(self, test_db):
    app_id = database.create_app("test")
    assert app_id > 0
    app = database.get_app_by_id(app_id)
    assert app["name"] == "test"
    assert app["created_at"] is not None
```

### 4. Use Assertions Wisely

Be specific with assertions:

```python
# Good
assert response.status_code == 200
assert "access_token" in response.json()
assert response.json()["token_type"] == "bearer"

# Bad
assert response.ok  # Not specific enough
```

### 5. Test Error Cases

Don't just test happy paths:

```python
def test_login_with_wrong_password(self, client, test_app):
    """Test that login fails with wrong password"""
    response = client.post(
        "/api/auth/login",
        data={
            "username": test_app["username"],
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401
```

### 6. Use Fixtures for Setup

Extract common setup to fixtures:

```python
@pytest.fixture
def user_with_logs(test_app, api_headers):
    """Fixture that creates user with sample logs"""
    # Setup code here
    return {"user": test_app, "log_count": 10}

def test_something(self, user_with_logs):
    """Test uses pre-configured data"""
    pass
```

## Continuous Integration

Tests should run in CI/CD:

```yaml
# Example GitHub Actions workflow
- name: Run Tests
  run: |
    cd backend
    uv sync --dev
    pytest --cov=. --cov-report=xml
    
- name: Upload Coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./backend/coverage.xml
```

## Debugging Tests

### Run with Verbose Output

```bash
pytest -vv
```

### Show Print Statements

```bash
pytest -s
```

### Drop into Debugger on Failure

```bash
pytest --pdb
```

### Run Last Failed Tests

```bash
pytest --lf
```

### Show Slowest Tests

```bash
pytest --durations=10
```

## Common Issues

### Import Errors

If you see import errors, ensure you're running from the backend directory:

```bash
cd backend
pytest
```

### Database Locking

If tests hang on database operations:
- Ensure previous test processes are killed
- Check that `test_db` fixture is cleaning up properly

### Authentication Issues

If auth tests fail:
- Verify JWT secret key is being generated
- Check token expiration settings
- Ensure cookies are being handled correctly

## Adding New Tests

When adding features, add corresponding tests:

1. Create test function in appropriate file
2. Use existing fixtures when possible
3. Follow naming conventions
4. Add markers if needed
5. Update this README if adding new test categories

Example:

```python
class TestNewFeature:
    """Test new feature description"""
    
    @pytest.mark.unit
    def test_new_feature_basic(self, test_db):
        """Test basic functionality"""
        result = new_feature()
        assert result is not None
    
    @pytest.mark.integration
    def test_new_feature_integration(self, client, test_app):
        """Test feature with full system"""
        response = client.post("/api/new-feature", json={...})
        assert response.status_code == 200
```

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)

## Getting Help

If tests are failing:

1. Read the error message carefully
2. Run with `-vv` for more details
3. Check recent changes to code
4. Verify database migrations are applied
5. Check fixture setup
6. Run single test in isolation
7. Add print statements or use debugger

For new contributors:
- Start by reading existing tests
- Follow the patterns you see
- Ask for code review
- Don't hesitate to ask questions
