"""Integration tests for file-based logging via real HTTP requests."""
import json
import pytest
from app.logging import logger, clear_log_file, get_log_entries


@pytest.fixture(autouse=True)
def cleanup_log_file():
    """Ensure a clean log file around each test run."""
    clear_log_file()
    yield
    clear_log_file()


def _request_end_entries(entries):
    return [entry for entry in entries if entry.get("stage") == "request_end"]


def test_successful_request_logs_request_end_success(client):
    """A successful bucket create should log request_end with success status."""
    response = client.post(
        "/storage/v1/b?project=logging-project",
        json={"name": "logging-success-bucket", "location": "US"}
    )

    assert response.status_code == 201

    entries = get_log_entries()
    assert entries, "Expected log entries to be written"

    request_ids = {entry.get("request_id") for entry in entries if entry.get("request_id")}
    assert len(request_ids) == 1

    request_end = _request_end_entries(entries)[-1]
    assert request_end["status"] == "success"
    assert request_end["details"]["final_status"] == 201


def test_failed_request_logs_request_end_error(client):
    """A validation failure should log request_end with error status."""
    response = client.post(
        "/storage/v1/b",
        json={"name": "missing-project"}
    )

    assert response.status_code == 400

    entries = get_log_entries()
    assert entries, "Expected log entries to be written"

    request_ids = {entry.get("request_id") for entry in entries if entry.get("request_id")}
    assert len(request_ids) == 1

    request_end = _request_end_entries(entries)[-1]
    assert request_end["status"] == "error"
    assert request_end["details"]["final_status"] == 400


def test_log_file_contains_json_lines(client):
    """Log file should store newline-delimited JSON objects for each request."""
    client.post(
        "/storage/v1/b?project=logging-project",
        json={"name": "json-lines-bucket", "location": "US"}
    )

    assert logger.log_file_path.exists(), "Log file should exist after request"

    with open(logger.log_file_path, "r", encoding="utf-8") as log_file:
        lines = [line.strip() for line in log_file if line.strip()]

    assert lines, "Log file should contain at least one entry"

    parsed_entries = [json.loads(line) for line in lines]
    for entry in parsed_entries:
        assert isinstance(entry, dict)
        assert "timestamp" in entry
        assert "request_id" in entry
        assert "stage" in entry
        assert "message" in entry

    request_ids = {entry.get("request_id") for entry in parsed_entries if entry.get("request_id")}
    assert len(request_ids) == 1