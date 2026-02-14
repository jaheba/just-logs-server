#!/usr/bin/env python3
"""
Test script to verify security fixes:
1. Rate limiting on authentication
2. SQL injection protection in tag filtering
"""

import sys
import time
import requests
from datetime import datetime

BASE_URL = "http://localhost:8000"


def test_rate_limiting():
    """Test that rate limiting is working on login endpoint"""
    print("\n=== Testing Rate Limiting on Login ===")

    # Attempt to login 6 times rapidly (limit is 5/minute)
    results = []
    for i in range(6):
        try:
            response = requests.post(
                f"{BASE_URL}/api/auth/login",
                json={"username": "test", "password": "test"},
                timeout=5,
            )
            results.append(
                {
                    "attempt": i + 1,
                    "status": response.status_code,
                    "detail": response.json().get("detail", ""),
                }
            )
        except Exception as e:
            results.append({"attempt": i + 1, "status": "ERROR", "detail": str(e)})
        time.sleep(0.5)  # Small delay between requests

    # Check results
    rate_limited = any(r["status"] == 429 for r in results)

    print(f"\nResults:")
    for r in results:
        print(f"  Attempt {r['attempt']}: HTTP {r['status']} - {r['detail']}")

    if rate_limited:
        print("\n✅ PASS: Rate limiting is working!")
        return True
    else:
        print(
            "\n❌ FAIL: No rate limiting detected. Expected HTTP 429 after 5 attempts."
        )
        return False


def test_sql_injection_protection():
    """Test that SQL injection is prevented in tag filtering"""
    print("\n=== Testing SQL Injection Protection ===")

    # Test with valid tag keys
    valid_keys = ["env", "region", "app-name", "user_id", "trace.id"]
    print("\nTesting valid tag keys:")
    for key in valid_keys:
        try:
            # This would be tested via the query_logs function in the database module
            from backend.database import validate_tag_key

            result = validate_tag_key(key)
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {status}: '{key}' -> {result}")
        except Exception as e:
            print(f"  ❌ ERROR: '{key}' -> {e}")

    # Test with malicious tag keys (SQL injection attempts)
    malicious_keys = [
        "env') OR '1'='1",
        "env'); DROP TABLE logs; --",
        "env' UNION SELECT * FROM web_users--",
        "../../../etc/passwd",
        'env"; DELETE FROM logs; --',
    ]

    print("\nTesting malicious tag keys (should all be rejected):")
    all_blocked = True
    for key in malicious_keys:
        try:
            from backend.database import validate_tag_key

            result = validate_tag_key(key)
            if result:
                print(f"  ❌ FAIL: '{key}' was ALLOWED (should be blocked)")
                all_blocked = False
            else:
                print(f"  ✅ PASS: '{key}' was blocked")
        except Exception as e:
            print(f"  ✅ PASS: '{key}' raised exception: {e}")

    return all_blocked


def main():
    print("=" * 60)
    print("Security Fixes Validation Test")
    print("=" * 60)

    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=2)
        if response.status_code != 200:
            print(f"\n❌ ERROR: Server returned status {response.status_code}")
            print("Please start the server with: cd backend && uvicorn main:app")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to server at", BASE_URL)
        print("Please start the server with: cd backend && uvicorn main:app")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        sys.exit(1)

    print("✅ Server is running")

    # Run tests
    results = []

    # Test SQL injection protection (doesn't require server)
    results.append(("SQL Injection Protection", test_sql_injection_protection()))

    # Test rate limiting (requires server)
    results.append(("Rate Limiting", test_rate_limiting()))

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")

    all_passed = all(r[1] for r in results)
    if all_passed:
        print("\n🎉 All security fixes are working correctly!")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Please review the output above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
