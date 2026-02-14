#!/usr/bin/env python3
"""
Test script to verify server-side timestamp functionality.
"""

import sys
import os
import time
from datetime import datetime, timedelta

# Add parent directory to path so we can import jlo_client
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from jlo_client import JustLoggingClient


def test_server_timestamps():
    """Test that server timestamps are captured correctly."""

    # Initialize client
    client = JustLoggingClient(
        base_url="http://localhost:8000",
        api_key="test-key-1",  # Replace with your actual API key
    )

    print("Testing server-side timestamps...\n")

    # Test 1: Log with client timestamp in the past
    print("Test 1: Sending log with past client timestamp...")
    past_time = datetime.utcnow() - timedelta(hours=2)
    client.log(
        level="INFO",
        message="Test log with past client timestamp",
        structured_data={"test_id": "test1"},
        timestamp=past_time,
    )
    print(f"  ✓ Sent log with client_timestamp: {past_time.isoformat()}")
    print(f"  ✓ Server should have captured server_timestamp as current time\n")

    # Test 2: Log with client timestamp in the future
    print("Test 2: Sending log with future client timestamp...")
    future_time = datetime.utcnow() + timedelta(hours=1)
    client.log(
        level="WARN",
        message="Test log with future client timestamp",
        structured_data={"test_id": "test2"},
        timestamp=future_time,
    )
    print(f"  ✓ Sent log with client_timestamp: {future_time.isoformat()}")
    print(f"  ✓ Server should have captured server_timestamp as current time\n")

    # Test 3: Log without client timestamp
    print("Test 3: Sending log without client timestamp...")
    client.log(
        level="ERROR",
        message="Test log without client timestamp",
        structured_data={"test_id": "test3"},
    )
    print(f"  ✓ Sent log without client_timestamp")
    print(f"  ✓ Server should use server_timestamp for both fields\n")

    # Test 4: Batch logs with mixed timestamps
    print("Test 4: Sending batch of logs with mixed timestamps...")
    batch_logs = [
        {
            "level": "INFO",
            "message": "Batch log 1 with timestamp",
            "structured_data": {"test_id": "test4a"},
            "timestamp": (datetime.utcnow() - timedelta(minutes=30)).isoformat(),
        },
        {
            "level": "INFO",
            "message": "Batch log 2 without timestamp",
            "structured_data": {"test_id": "test4b"},
        },
        {
            "level": "DEBUG",
            "message": "Batch log 3 with current timestamp",
            "structured_data": {"test_id": "test4c"},
            "timestamp": datetime.utcnow().isoformat(),
        },
    ]
    client.batch_log(batch_logs)
    print(f"  ✓ Sent 3 logs in batch")
    print(f"  ✓ All should have server_timestamp captured at receipt time\n")

    print("=" * 70)
    print("All tests completed successfully!")
    print("=" * 70)
    print("\nTo verify the results:")
    print("1. Open the web UI at http://localhost:8000")
    print("2. Look for the test logs (filter by structured_data.test_id)")
    print("3. Expand a log entry to see both 'Client Timestamp' and 'Server Timestamp'")
    print("4. Verify that:")
    print("   - Test 1: client_timestamp is ~2 hours ago, server_timestamp is recent")
    print(
        "   - Test 2: client_timestamp is ~1 hour in future, server_timestamp is recent"
    )
    print("   - Test 3: both timestamps should be nearly identical (server-assigned)")
    print(
        "   - Test 4: all logs have recent server_timestamp despite varied client_timestamp"
    )


if __name__ == "__main__":
    try:
        test_server_timestamps()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure:")
        print("1. Backend server is running (cd backend && uvicorn main:app)")
        print("2. API key 'test-key-1' exists or update the script with your key")
        sys.exit(1)
