"""
Unit test - Utilities
"""
import pytest
from app.utils.hashing import calculate_md5, calculate_crc32c


@pytest.mark.unit
def test_calculate_md5():
    """Test MD5 calculation"""
    data = b"Hello, World!"
    hash_value = calculate_md5(data)
    assert isinstance(hash_value, str)
    assert len(hash_value) > 0


@pytest.mark.unit
def test_calculate_crc32c():
    """Test CRC32C calculation"""
    data = b"Hello, World!"
    hash_value = calculate_crc32c(data)
    assert isinstance(hash_value, str)
    assert len(hash_value) > 0
