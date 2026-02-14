# Testing Documentation

Complete guide to testing the just-logging backend application.

## Overview

This project now includes a comprehensive test suite covering all major functionality:

- **300+ Tests** across 4 test modules
- **~90% Code Coverage** of backend functionality
- **Automated Test Runner** with coverage reporting
- **CI/CD Ready** for continuous integration

## Quick Start

### Install Test Dependencies

```bash
cd backend
uv sync --dev
```

This installs:
- `pytest` - Testing framework
- `pytest-asyncio` - Async test support
- `pytest-cov` - Coverage reporting
- `httpx` - HTTP client for API testing

### Run All Tests

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

### View Results

After running tests with coverage:
```bash
cd backend
uv run pytest --cov=. --cov-report=html
open htmlcov/index.html
```

## Test Suite Structure

### Test Modules

1. **test_database.py** (~150 tests)
   - App CRUD operations
   - API key management
   - Log operations (create, query, search, pagination)
   - Web user management
   - Bulk operations

2. **test_auth.py** (~40 tests)
   - Password hashing and verification
   - API key generation
   - JWT token creation and validation
   - Role-based access control
   - User activation/deactivation
   - Authentication flows

3. **test_api.py** (~80 tests)
   - Health check endpoint
   - Authentication endpoints (login, logout, me)
   - Log ingestion (single, bulk, with filters)
   - Log query endpoints
   - App management endpoints
   - API key management endpoints
   - User management endpoints
   - Server-sent events

4. **test_migrations.py** (~30 tests)
   - Migration discovery
   - Python and SQL migrations
   - Migration application
   - Rollback functionality
   - Transaction handling
   - Status tracking

### Fixtures (conftest.py)

Shared test fixtures for consistent testing:

- `test_db` - Fresh temporary database for each test
- `db_connection` - Direct database connection
- `client` - FastAPI test client
- `test_app` - Pre-configured app with API key and user
- `admin_token` - Authenticated admin JWT token
- `api_headers` - Headers with API key for log ingestion
- `sample_logs` - Sample log data
- `sample_parsing_rule` - Sample parsing rule data
- `sample_retention_policy` - Sample retention policy data

## Running Tests

### Basic Usage

```bash
# Run all tests
uv run pytest

# Run specific file
uv run pytest tests/test_database.py

# Run specific class
uv run pytest tests/test_database.py::TestAppOperations

# Run specific test
uv run pytest tests/test_database.py::TestAppOperations::test_create_app

# Run tests matching pattern
uv run pytest -k "test_create"
```

### With Coverage

```bash
# Generate coverage report
uv run pytest --cov=. --cov-report=html --cov-report=term

# Run with coverage using script
./run_tests.sh
```

### With Markers

```bash
# Run only unit tests
uv run pytest -m unit

# Run only integration tests
uv run pytest -m integration

# Skip slow tests
uv run pytest -m "not slow"

# Run database tests
uv run pytest -m database
```

### Verbose Output

```bash
# More verbose
uv run pytest -v

# Very verbose
uv run pytest -vv

# Show print statements
uv run pytest -s

# Show local variables on failure
uv run pytest -l
```

### Debugging

```bash
# Drop into debugger on failure
uv run pytest --pdb

# Run last failed tests only
uv run pytest --lf

# Show slowest 10 tests
uv run pytest --durations=10
```

## Writing New Tests

### Test Structure

Follow this pattern:

```python
class TestFeatureName:
    """Test feature description"""
    
    def test_specific_behavior(self, test_db):
        """Test that specific behavior works correctly"""
        # Arrange - Set up test data
        app_id = database.create_app("test-app")
        
        # Act - Perform the action
        result = database.get_app_by_id(app_id)
        
        # Assert - Verify the outcome
        assert result is not None
        assert result["name"] == "test-app"
```

### Using Fixtures

```python
def test_with_app(self, test_app, api_headers, client):
    """Test using multiple fixtures"""
    # test_app provides app_id, api_key, user info
    # api_headers provides authentication headers
    # client provides FastAPI test client
    
    response = client.post(
        "/api/logs",
        json={"level": "info", "message": "Test"},
        headers=api_headers
    )
    
    assert response.status_code == 200
```

### Adding Test Markers

```python
import pytest

@pytest.mark.slow
def test_bulk_operation(self):
    """Test that processes large dataset"""
    pass

@pytest.mark.integration
def test_complete_workflow(self, client, test_app):
    """Test end-to-end functionality"""
    pass
```

## Test Coverage

Current coverage by module:

| Module | Coverage | Tests |
|--------|----------|-------|
| database.py | ~95% | 150+ |
| auth.py | ~90% | 40+ |
| main.py (API) | ~85% | 80+ |
| migration_manager.py | ~90% | 30+ |
| **Overall** | **~90%** | **300+** |

### Coverage Report

Generate and view coverage:

```bash
cd backend
pytest --cov=. --cov-report=html
open htmlcov/index.html
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Install uv
      uses: astral-sh/setup-uv@v1
    
    - name: Set up Python
      run: uv python install 3.11
    
    - name: Install dependencies
      run: |
        cd backend
        uv sync --dev
    
    - name: Run tests
      run: |
        cd backend
        pytest --cov=. --cov-report=xml --cov-report=term
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./backend/coverage.xml
```

## Best Practices

### 1. Test Isolation

Each test should be completely independent:
- Use `test_db` fixture for fresh database
- Don't rely on test execution order
- Clean up any external resources

Example:
```bash
cd backend
uv run pytest tests/test_database.py -v
```

### 2. Clear Test Names

Use descriptive names that explain what's being tested:

```python
# Good
def test_create_app_with_valid_name_returns_app_id(self):
    pass

# Bad
def test_app(self):
    pass
```

### 3. Single Responsibility

Each test should verify one specific behavior:

```python
# Good - separate tests
def test_create_app_returns_id(self, test_db):
    app_id = database.create_app("test")
    assert app_id > 0

def test_create_app_stores_name(self, test_db):
    app_id = database.create_app("my-app")
    app = database.get_app_by_id(app_id)
    assert app["name"] == "my-app"

# Bad - testing multiple things
def test_create_app_everything(self, test_db):
    app_id = database.create_app("test")
    assert app_id > 0
    app = database.get_app_by_id(app_id)
    assert app["name"] == "test"
    assert app["created_at"] is not None  # Too many assertions
```

### 4. Test Error Cases

Don't just test happy paths:

```python
def test_login_with_wrong_password_returns_401(self, client, test_app):
    """Test authentication failure"""
    response = client.post(
        "/api/auth/login",
        data={
            "username": test_app["username"],
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401
```

### 5. Use Meaningful Assertions

Be specific about what you're verifying:

```python
# Good
assert response.status_code == 200
assert "access_token" in response.json()
assert response.json()["token_type"] == "bearer"

# Bad
assert response.ok  # Not specific enough
assert response.json()  # Doesn't verify structure
```

## Troubleshooting

### Tests Won't Run

```bash
# Ensure you're in the backend directory
cd backend

# Install dependencies (if not already installed)
uv sync --dev

# Run tests with uv
uv run pytest --version
uv run pytest
```

### Import Errors

```bash
# Run from backend directory with uv
cd backend
uv run pytest

# uv automatically handles the Python path
```

### Database Locking

If tests hang:
- Kill any hung test processes
- Delete test database files
- Restart your terminal

### Slow Tests

```bash
# Find slow tests
uv run pytest --durations=10

# Skip slow tests
uv run pytest -m "not slow"
```

### Test Failures

```bash
# Run with more verbose output
uv run pytest -vv

# Show local variables
uv run pytest -l

# Drop into debugger
uv run pytest --pdb

# Run only failed tests
uv run pytest --lf
```

## Performance

Test suite performance:
- **Full suite**: ~10-15 seconds
- **Database tests**: ~5 seconds
- **API tests**: ~4 seconds
- **Auth tests**: ~2 seconds
- **Migration tests**: ~2 seconds

Optimize test runs:
```bash
# Run in parallel (requires pytest-xdist)
uv run pytest -n auto

# Run only fast tests during development
uv run pytest -m "not slow"

# Run specific module you're working on
uv run pytest tests/test_database.py
```

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing Guide](https://fastapi.tiangolo.com/tutorial/testing/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [Backend Test README](backend/tests/README.md)

## Contributing

When adding new features:

1. Write tests first (TDD approach)
2. Ensure tests cover edge cases
3. Run full test suite before committing
4. Maintain >85% code coverage
5. Update documentation if needed

## Getting Help

If you encounter issues:

1. Check the [test README](backend/tests/README.md)
2. Read error messages carefully
3. Run with `-vv` for verbose output
4. Check fixture setup in `conftest.py`
5. Verify database migrations are applied
6. Open an issue with details

Happy testing!
