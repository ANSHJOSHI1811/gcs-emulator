"""
Test file-based logging system for GCS Emulator
Validates log file writing, reading, and request correlation
"""
import json
import pytest
from app.logging import (
    logger, clear_log_file, get_log_entries, get_log_entries_for_request,
    log_emulator_stage, log_router_stage, log_handler_stage,
    log_service_stage, log_repository_stage, log_formatter_stage
)


class TestFileBasedLogging:
    """Test suite for file-based logging system"""

    @pytest.fixture(autouse=True)
    def setup_and_cleanup(self):
        """Clear log file before and after each test"""
        clear_log_file()
        yield
        clear_log_file()

    def test_log_file_creation_and_writing(self):
        """Test that log file is created and entries are written correctly"""
        # Ensure log file doesn't exist initially
        assert not logger.log_file_path.exists()
        
        # Log a test entry
        log_emulator_stage(
            message="Test message",
            details={"test": "data"}
        )
        
        # Verify log file was created
        assert logger.log_file_path.exists()
        
        # Read log entries
        entries = get_log_entries()
        assert len(entries) == 1
        
        entry = entries[0]
        assert entry["stage"] == "stage_3_emulator"
        assert entry["message"] == "Test message"
        assert entry["status"] == "success"
        assert entry["details"]["test"] == "data"
        assert "timestamp" in entry
        assert "request_id" in entry

    def test_json_lines_format(self):
        """Test that log entries are written in JSON Lines format"""
        # Log multiple entries
        log_emulator_stage("First message")
        log_router_stage("Second message")
        log_handler_stage("Third message")
        
        # Read raw file content
        with open(logger.log_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        assert len(lines) == 3
        
        # Each line should be valid JSON
        for line in lines:
            parsed = json.loads(line.strip())
            assert isinstance(parsed, dict)
            assert "timestamp" in parsed
            assert "request_id" in parsed
            assert "stage" in parsed
            assert "message" in parsed

    def test_stage_identifiers(self):
        """Test that different stages have correct identifiers"""
        log_emulator_stage("Emulator message")
        log_router_stage("Router message")
        log_handler_stage("Handler message")
        log_service_stage("Service message")
        log_repository_stage("Repository message")
        log_formatter_stage("Formatter message")
        
        entries = get_log_entries()
        assert len(entries) == 6
        
        # Verify stage identifiers
        expected_stages = {
            "stage_3_emulator",
            "stage_4_router", 
            "stage_5_handler",
            "stage_6_service",
            "stage_7_repository",
            "stage_8_formatter"
        }
        
        actual_stages = {entry["stage"] for entry in entries}
        assert actual_stages == expected_stages

    def test_timestamp_format(self):
        """Test that timestamps are in correct ISO format"""
        log_emulator_stage("Timestamp test")
        
        entries = get_log_entries()
        entry = entries[0]
        
        timestamp = entry["timestamp"]
        assert isinstance(timestamp, str)
        assert timestamp.endswith('Z')  # UTC format
        assert 'T' in timestamp  # ISO format

    def test_request_id_format(self):
        """Test that request IDs have correct format"""
        # Generate a request ID by calling logger method directly
        logger._get_request_id()  # This will generate one if none exists
        
        log_emulator_stage("Request ID test")
        
        entries = get_log_entries()
        entry = entries[0]
        
        request_id = entry["request_id"]
        assert isinstance(request_id, str)
        if request_id:  # May be empty outside Flask context
            assert request_id.startswith('req_')
            assert len(request_id) > 4  # Should have UUID suffix
        else:
            # In test context without Flask, request_id might be empty
            assert request_id == ""

    def test_multiple_entries_same_request(self):
        """Test that multiple log entries share same request ID"""
        log_emulator_stage("First entry")
        log_router_stage("Second entry") 
        log_handler_stage("Third entry")
        
        entries = get_log_entries()
        assert len(entries) == 3
        
        # All should have same request_id
        request_ids = {entry["request_id"] for entry in entries}
        assert len(request_ids) == 1

    def test_log_with_details(self):
        """Test logging with additional details"""
        details = {
            "bucket_name": "test-bucket",
            "operation": "create",
            "size": 1024
        }
        
        log_service_stage("Service operation", details=details)
        
        entries = get_log_entries()
        entry = entries[0]
        
        assert "details" in entry
        assert entry["details"]["bucket_name"] == "test-bucket"
        assert entry["details"]["operation"] == "create"
        assert entry["details"]["size"] == 1024

    def test_log_with_duration(self):
        """Test logging with duration measurement"""
        log_handler_stage("Handler processing", duration_ms=15.75)
        
        entries = get_log_entries()
        entry = entries[0]
        
        assert "duration_ms" in entry
        assert entry["duration_ms"] == 15.75

    def test_log_with_extra_details(self):
        """Test logging with additional details in details dict"""
        details_with_extras = {
            "bucket_name": "test-bucket",
            "method": "POST",
            "route": "/storage/v1/b",
            "project_id": "test-project"
        }
        
        log_service_stage("Service operation", details=details_with_extras)
        
        entries = get_log_entries()
        entry = entries[0]
        
        assert "details" in entry
        details = entry["details"]
        assert details["bucket_name"] == "test-bucket"
        assert details["method"] == "POST"
        assert details["route"] == "/storage/v1/b"
        assert details["project_id"] == "test-project"

    def test_get_log_entries_for_request_function(self):
        """Test filtering entries by request ID"""
        # Log some entries 
        log_emulator_stage("Entry 1")
        log_router_stage("Entry 2")
        log_handler_stage("Entry 3")
        
        all_entries = get_log_entries()
        assert len(all_entries) == 3
        
        # All entries should have same request_id (or empty)
        request_id = all_entries[0]["request_id"]
        for entry in all_entries:
            assert entry["request_id"] == request_id
        
        # Filter by the request_id
        filtered_entries = get_log_entries_for_request(request_id)
        
        # Should get all entries since they all have same request_id
        assert len(filtered_entries) == len(all_entries)
        
        for entry in filtered_entries:
            assert entry["request_id"] == request_id
        
        # Test with non-existent request_id
        non_existent_entries = get_log_entries_for_request("non-existent-id")
        assert len(non_existent_entries) == 0

    def test_log_file_append_behavior(self):
        """Test that entries are appended to log file"""
        # First batch of entries
        log_emulator_stage("First entry")
        log_router_stage("Second entry")
        
        first_count = len(get_log_entries())
        assert first_count == 2
        
        # Add more entries (should append)
        log_handler_stage("Third entry")
        log_service_stage("Fourth entry")
        
        total_count = len(get_log_entries())
        assert total_count == 4
        
        # Verify all entries are present
        entries = get_log_entries()
        messages = [entry["message"] for entry in entries]
        assert "First entry" in messages
        assert "Second entry" in messages
        assert "Third entry" in messages
        assert "Fourth entry" in messages

    def test_clear_log_file_function(self):
        """Test that clear_log_file removes all entries"""
        # Add some entries
        log_emulator_stage("Entry 1")
        log_router_stage("Entry 2")
        log_handler_stage("Entry 3")
        
        assert len(get_log_entries()) == 3
        
        # Clear log file
        clear_log_file()
        
        # Should be empty now
        assert len(get_log_entries()) == 0
        assert not logger.log_file_path.exists()

    def test_all_stage_functions_work(self):
        """Test that all stage logging functions work correctly"""
        stage_functions = [
            (log_emulator_stage, "stage_3_emulator"),
            (log_router_stage, "stage_4_router"),
            (log_handler_stage, "stage_5_handler"),
            (log_service_stage, "stage_6_service"),
            (log_repository_stage, "stage_7_repository"),
            (log_formatter_stage, "stage_8_formatter")
        ]
        
        for log_func, expected_stage in stage_functions:
            clear_log_file()
            
            stage_name = expected_stage.split('_', 2)[2].replace('_', ' ').title()
            log_func(f"Testing {stage_name} stage")
            
            entries = get_log_entries()
            assert len(entries) == 1
            
            entry = entries[0]
            assert entry["stage"] == expected_stage
            assert entry["message"] == f"Testing {stage_name} stage"

    def test_complex_details_serialization(self):
        """Test that complex details are properly serialized"""
        complex_details = {
            "nested": {
                "data": "value",
                "number": 42
            },
            "list": [1, 2, 3],
            "boolean": True,
            "null_value": None
        }
        
        log_service_stage("Complex details test", details=complex_details)
        
        entries = get_log_entries()
        entry = entries[0]
        
        details = entry["details"]
        assert details["nested"]["data"] == "value"
        assert details["nested"]["number"] == 42
        assert details["list"] == [1, 2, 3]
        assert details["boolean"] is True
        assert details["null_value"] is None

    def test_log_file_path_and_structure(self):
        """Test that log file is created in correct location"""
        log_emulator_stage("Path test")
        
        # Verify file exists and is in correct location
        assert logger.log_file_path.exists()
        assert logger.log_file_path.name == "emulator.log"
        assert logger.log_file_path.parent.name == "logs"
        
        # Verify file contains valid JSON
        with open(logger.log_file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            
        # Should be one line of JSON
        lines = content.split('\n')
        assert len(lines) == 1
        
        # Should be valid JSON
        parsed = json.loads(lines[0])
        assert isinstance(parsed, dict)
        assert parsed["message"] == "Path test"