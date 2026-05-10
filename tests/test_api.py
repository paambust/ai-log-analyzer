#!/usr/bin/env python3
"""
Integration tests for AI Log Analyzer microservices.
Tests API health, database connectivity, and basic functionality.
"""

import requests
import time
import sys
import json

# Configuration
# Use 'api' service name when running in Docker Compose network, fallback to localhost for local dev
import os
API_URL = os.getenv("API_URL", "http://localhost:8000")
HEALTH_CHECK_RETRIES = 10
HEALTH_CHECK_DELAY = 2

def log_test(test_name, status, message=""):
    """Log test results"""
    symbol = "✓" if status else "✗"
    print(f"{symbol} {test_name}: {message}")
    if not status:
        print(f"  ERROR: {message}")

def wait_for_service(url, max_retries=HEALTH_CHECK_RETRIES, delay=HEALTH_CHECK_DELAY):
    """Wait for a service to be ready"""
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            pass
        
        if attempt < max_retries - 1:
            print(f"  Attempt {attempt + 1}/{max_retries} - Waiting for service...")
            time.sleep(delay)
    
    return False

def test_api_health():
    """Test: API health endpoint responds"""
    print("\n--- Testing API Health ---")
    
    if not wait_for_service(f"{API_URL}/health"):
        log_test("API Health Check", False, "API did not respond within timeout")
        return False
    
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        is_ok = response.status_code == 200 and "status" in response.json()
        log_test("API Health Check", is_ok, f"Status: {response.status_code}")
        return is_ok
    except Exception as e:
        log_test("API Health Check", False, str(e))
        return False

def test_create_log():
    """Test: POST /logs endpoint"""
    print("\n--- Testing Log Creation ---")
    
    log_data = {
        "service": "test-service",
        "level": "INFO",
        "message": "Test log message"
    }
    
    try:
        response = requests.post(f"{API_URL}/logs", json=log_data, timeout=5)
        is_ok = response.status_code == 200 and "status" in response.json()
        log_test("Create Log", is_ok, f"Status: {response.status_code}")
        return is_ok
    except Exception as e:
        log_test("Create Log", False, str(e))
        return False

def test_retrieve_logs():
    """Test: GET /logs endpoint"""
    print("\n--- Testing Log Retrieval ---")
    
    try:
        response = requests.get(f"{API_URL}/logs?limit=5", timeout=5)
        is_ok = response.status_code == 200 and isinstance(response.json(), list)
        log_count = len(response.json()) if is_ok else 0
        log_test("Retrieve Logs", is_ok, f"Retrieved {log_count} logs")
        return is_ok
    except Exception as e:
        log_test("Retrieve Logs", False, str(e))
        return False

def test_multiple_log_levels():
    """Test: Logs with different severity levels"""
    print("\n--- Testing Different Log Levels ---")
    
    levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    all_ok = True
    
    for level in levels:
        log_data = {
            "service": "test-service",
            "level": level,
            "message": f"Test {level} message"
        }
        try:
            response = requests.post(f"{API_URL}/logs", json=log_data, timeout=5)
            is_ok = response.status_code == 200
            log_test(f"Log Level: {level}", is_ok, f"Status: {response.status_code}")
            all_ok = all_ok and is_ok
        except Exception as e:
            log_test(f"Log Level: {level}", False, str(e))
            all_ok = False
    
    return all_ok

def test_log_analysis():
    """Test: Verify worker analyzes logs and marks them as analyzed"""
    print("\n--- Testing Log Analysis (LLM) ---")
    
    # Create a log
    log_data = {
        "service": "analysis-test",
        "level": "ERROR",
        "message": "Test error for analysis"
    }
    
    try:
        # Create the log
        response = requests.post(f"{API_URL}/logs", json=log_data, timeout=5)
        if response.status_code != 200:
            log_test("Log Analysis", False, "Failed to create log")
            return False
        
        # Wait for worker to analyze (worker runs every 10 seconds)
        print("  Waiting for worker to analyze logs (15 seconds)...")
        for i in range(15):
            if i > 0 and i % 5 == 0:
                print(f"    {15 - i} seconds remaining...")
            time.sleep(1)
        
        # Check if any logs are marked as analyzed
        response = requests.get(f"{API_URL}/logs?analyzed=true&limit=10", timeout=5)
        
        if response.status_code != 200:
            log_test("Log Analysis", False, "Failed to retrieve analyzed logs")
            return False
        
        analyzed_logs = response.json()
        is_ok = len(analyzed_logs) > 0
        
        if is_ok and len(analyzed_logs) > 0:
            log_test("Log Analysis", True, f"Found {len(analyzed_logs)} analyzed logs with LLM insights")
            # Print a sample analysis
            sample = analyzed_logs[0]
            print(f"    Sample analysis (first 100 chars): {sample.get('analysis', 'N/A')[:100]}...")
        else:
            log_test("Log Analysis", False, "No analyzed logs found (worker may not have LLM access)")
        
        return is_ok
    except Exception as e:
        log_test("Log Analysis", False, str(e))
        return False

def test_service_connectivity():
    """Test: Database connectivity through API"""
    print("\n--- Testing Database Connectivity ---")
    
    # Create a log to verify DB connection
    log_data = {
        "service": "db-test",
        "level": "INFO",
        "message": "Database connectivity test"
    }
    
    try:
        response = requests.post(f"{API_URL}/logs", json=log_data, timeout=5)
        is_ok = response.status_code == 200
        log_test("Database Connectivity", is_ok, f"Status: {response.status_code}")
        return is_ok
    except Exception as e:
        log_test("Database Connectivity", False, str(e))
        return False

def main():
    """Run all tests"""
    print("\n" + "=" * 50)
    print("AI Log Analyzer - Integration Tests")
    print("=" * 50)
    
    tests = [
        ("API Health Check", test_api_health),
        ("Service Connectivity", test_service_connectivity),
        ("Create Log", test_create_log),
        ("Retrieve Logs", test_retrieve_logs),
        ("Test Log Levels", test_multiple_log_levels),
        ("Log Analysis (LLM)", test_log_analysis),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"\n✗ Unexpected error in {test_name}: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    passed = sum(results)
    total = len(results)
    print(f"Tests Passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
