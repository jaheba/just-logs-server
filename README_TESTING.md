# Quick Testing Guide

## Setup

```bash
cd backend
uv sync --dev
```

## Run Tests

```bash
# Run all tests
cd backend
uv run pytest

# Run with coverage
uv run pytest --cov=. --cov-report=html

# Run specific test file
uv run pytest tests/test_database.py

# Run specific test
uv run pytest tests/test_database.py::TestAppOperations::test_create_app

# Run with pattern
uv run pytest -k "test_create"

# Run with markers
uv run pytest -m unit
uv run pytest -m "not slow"
```

## Common Commands

```bash
# Verbose output
uv run pytest -v

# Very verbose
uv run pytest -vv

# Show print statements
uv run pytest -s

# Stop on first failure
uv run pytest -x

# Run last failed tests
uv run pytest --lf

# Show slowest tests
uv run pytest --durations=10

# Drop into debugger on failure
uv run pytest --pdb
```

## Coverage Report

```bash
cd backend
uv run pytest --cov=. --cov-report=html
open htmlcov/index.html
```

## Test Statistics

- **300+ tests** across 4 modules
- **~90% code coverage**
- **~10-15 seconds** full suite runtime

## Documentation

- Full guide: [TESTING.md](TESTING.md)
- Test documentation: [backend/tests/README.md](backend/tests/README.md)

## Test Files

- `test_database.py` - Database operations (~150 tests)
- `test_auth.py` - Authentication (~40 tests)
- `test_api.py` - API endpoints (~80 tests)
- `test_migrations.py` - Migration system (~30 tests)
