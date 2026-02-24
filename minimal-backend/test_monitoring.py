"""
Simple test script for Cloud Monitoring API endpoints.

Tests endpoints by making HTTP requests to running server.
"""

import requests
import json
from datetime import datetime, timedelta, timezone
import time


BASE_URL = "http://localhost:8080"
PROJECT = "test-project-123"


def test_create_metric_descriptor():
    """Test creating a met metric descriptor."""
    response = requests.post(
        f"{BASE_URL}/v3/projects/{PROJECT}/metricDescriptors",
        json={
            "type": "custom.googleapis.com/cpu_usage",
            "metricKind": "GAUGE",
            "valueType": "DOUBLE",
            "unit": "%",
            "displayName": "CPU Usage",
            "description": "CPU usage percentage",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "custom.googleapis.com/cpu_usage"
    print("✅ test_create_metric_descriptor passed")


def test_list_metric_descriptors():
    """Test listing metric descriptors."""
    # Create two metrics
    for i in range(2):
        requests.post(
            f"{BASE_URL}/v3/projects/{PROJECT}/metricDescriptors",
            json={
                "type": f"custom.googleapis.com/metric_{i}",
                "metricKind": "GAUGE",
                "valueType": "DOUBLE",
            },
        )

    # List them
    response = requests.get(f"{BASE_URL}/v3/projects/{PROJECT}/metricDescriptors")
    assert response.status_code == 200
    data = response.json()
    assert len(data["metricDescriptors"]) >= 2
    print("✅ test_list_metric_descriptors passed")


def test_write_time_series():
    """Test writing time series data."""
    # Create descriptor first
    requests.post(
        f"{BASE_URL}/v3/projects/{PROJECT}/metricDescriptors",
        json={
            "type": "custom.googleapis.com/cpu",
            "metricKind": "GAUGE",
            "valueType": "DOUBLE",
        },
    )

    # Write time series
    response = requests.post(
        f"{BASE_URL}/v3/projects/{PROJECT}/timeSeries",
        json={
            "timeSeries": [
                {
                    "metric": {
                        "type": "custom.googleapis.com/cpu",
                        "labels": {},
                    },
                    "resource": {
                        "type": "gce_instance",
                        "labels": {"instance_id": "vm-1", "zone": "us-central1-a"},
                    },
                    "points": [
                        {
                            "interval": {
                                "startTime": "2026-02-24T10:00:00Z",
                                "endTime": "2026-02-24T10:01:00Z",
                            },
                            "value": {"doubleValue": 75.5},
                        }
                    ],
                }
            ]
        },
    )
    assert response.status_code == 200
    print("✅ test_write_time_series passed")


def test_query_time_series():
    """Test querying time series data."""
    # Create descriptor
    requests.post(
        f"{BASE_URL}/v3/projects/{PROJECT}/metricDescriptors",
        json={
            "type": "custom.googleapis.com/requests",
            "metricKind": "DELTA",
            "valueType": "INT64",
        },
    )

    # Write data with current timestamp (will be analyzed shortly after writing)
    now = datetime.now(timezone.utc)
    later = now + timedelta(seconds=60)
    query_start = now - timedelta(minutes=5)
    query_end = later + timedelta(minutes=5)
    
    requests.post(
        f"{BASE_URL}/v3/projects/{PROJECT}/timeSeries",
        json={
            "timeSeries": [
                {
                    "metric": {"type": "custom.googleapis.com/requests"},
                    "resource": {"type": "gce_instance", "labels": {"instance_id": "vm-3"}},
                    "points": [
                        {
                            "interval": {
                                "startTime": now.isoformat(),
                                "endTime": later.isoformat(),
                            },
                            "value": {"int64Value": 100},
                        }
                    ],
                }
            ]
        },
    )

    # Query it with explicit time range to ensure it catches the data
    response = requests.get(
        f"{BASE_URL}/v3/projects/{PROJECT}/timeSeries",
        params={
            "filter": 'metric.type="custom.googleapis.com/requests"',
            "interval_start_time": query_start.isoformat(),
            "interval_end_time": query_end.isoformat(),
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["timeSeries"]) >= 1, f"Expected at least 1 timeSeries, got {len(data['timeSeries'])}"
    print("✅ test_query_time_series passed")


def test_create_alert_policy():
    """Test creating an alert policy."""
    response = requests.post(
        f"{BASE_URL}/v3/projects/{PROJECT}/alertPolicies",
        json={
            "displayName": "High CPU Alert",
            "conditions": [
                {
                    "displayName": "CPU > 80%",
                    "conditionThreshold": {
                        "filter": 'metric.type="custom.googleapis.com/cpu"',
                        "comparison": "COMPARISON_GT",
                        "thresholdValue": 80,
                        "duration": "300s",
                        "aggregations": [
                            {
                                "alignmentPeriod": "60s",
                                "perSeriesAligner": "ALIGN_MEAN",
                            }
                        ],
                    },
                }
            ],
            "notificationChannels": [],
            "enabled": True,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["displayName"] == "High CPU Alert"
    assert data["state"] == "OK"
    print("✅ test_create_alert_policy passed")


def test_create_notification_channel():
    """Test creating an email notification channel."""
    response = requests.post(
        f"{BASE_URL}/v3/projects/{PROJECT}/notificationChannels",
        json={
            "displayName": "Alert Email",
            "type": "email",
            "labels": {"emailAddress": "admin@example.com"},
            "enabled": True,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "email"
    assert data["labels"]["emailAddress"] == "admin@example.com"
    print("✅ test_create_notification_channel passed")


def test_health_check():
    """Test health check endpoint."""
    response = requests.get(f"{BASE_URL}/v3/monitoring/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "storage" in data
    print("✅ test_health_check passed")


def run_all_tests():
    """Run all tests."""
    print("\n🧪 Running Cloud Monitoring Tests\n")
    print(f"📍 Target: {BASE_URL}")
    print(f"📦 Project: {PROJECT}\n")
    
    tests = [
        test_create_metric_descriptor,
        test_list_metric_descriptors,
        test_write_time_series,
        test_query_time_series,
        test_create_notification_channel,
        test_create_alert_policy,
        test_health_check,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed")
    print(f"{'='*50}\n")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
