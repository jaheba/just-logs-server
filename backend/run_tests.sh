#!/bin/bash
# Test runner script for just-logging backend

set -e  # Exit on error

echo "========================================="
echo "Just-Logging Backend Test Suite"
echo "========================================="
echo ""

# Change to backend directory
cd "$(dirname "$0")"

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "Error: pytest not found. Installing test dependencies..."
    echo ""
    uv sync --dev
fi

# Parse command line arguments
TEST_PATH="${1:-tests/}"
COVERAGE="${COVERAGE:-true}"
MARKERS="${MARKERS:-}"

echo "Configuration:"
echo "  Test path: $TEST_PATH"
echo "  Coverage: $COVERAGE"
if [ -n "$MARKERS" ]; then
    echo "  Markers: $MARKERS"
fi
echo ""

# Build pytest command
PYTEST_CMD="pytest $TEST_PATH"

# Add markers if specified
if [ -n "$MARKERS" ]; then
    PYTEST_CMD="$PYTEST_CMD -m \"$MARKERS\""
fi

# Add coverage if enabled
if [ "$COVERAGE" = "true" ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=. --cov-report=html --cov-report=term"
fi

# Run tests
echo "Running tests..."
echo "Command: $PYTEST_CMD"
echo ""

eval $PYTEST_CMD

TEST_EXIT_CODE=$?

echo ""
echo "========================================="

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✓ All tests passed!"
    
    if [ "$COVERAGE" = "true" ]; then
        echo ""
        echo "Coverage report generated: htmlcov/index.html"
    fi
else
    echo "✗ Some tests failed"
fi

echo "========================================="

exit $TEST_EXIT_CODE
