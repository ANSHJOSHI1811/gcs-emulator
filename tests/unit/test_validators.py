"""
Unit test - Validators
"""
import pytest
from app.services.validation import validate_bucket_name, validate_object_name


@pytest.mark.unit
def test_validate_bucket_name_valid():
    """Test valid bucket name validation"""
    is_valid, msg = validate_bucket_name("my-bucket")
    assert is_valid is True


@pytest.mark.unit
def test_validate_bucket_name_too_short():
    """Test bucket name too short"""
    is_valid, msg = validate_bucket_name("ab")
    assert is_valid is False


@pytest.mark.unit
def test_validate_object_name_valid():
    """Test valid object name"""
    is_valid, msg = validate_object_name("path/to/file.txt")
    assert is_valid is True


@pytest.mark.unit
def test_validate_object_name_empty():
    """Test empty object name"""
    is_valid, msg = validate_object_name("")
    assert is_valid is False
