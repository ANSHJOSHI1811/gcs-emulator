"""
Hashing utilities for object integrity verification
Provides MD5 and CRC32C checksum calculation functions
"""
import hashlib
import base64


def calculate_md5(data: bytes) -> str:
    """
    Calculate MD5 hash of data and return as base64-encoded string
    
    Args:
        data: Raw bytes to hash
        
    Returns:
        Base64-encoded MD5 hash string
    """
    md5_hash = hashlib.md5(data).digest()
    return base64.b64encode(md5_hash).decode('utf-8')


def calculate_crc32c(data: bytes) -> str:
    """
    Calculate CRC32C checksum of data and return as base64-encoded string
    
    Note: This is a placeholder implementation using CRC32 instead of CRC32C.
    For production, use google-crc32c library for proper CRC32C calculation.
    
    Args:
        data: Raw bytes to hash
        
    Returns:
        Base64-encoded CRC32C checksum string
    """
    import zlib
    # Using standard CRC32 as placeholder
    # Production should use: import google_crc32c; checksum = google_crc32c.value(data)
    crc = zlib.crc32(data)
    # Convert to 4-byte big-endian representation
    crc_bytes = crc.to_bytes(4, byteorder='big')
    return base64.b64encode(crc_bytes).decode('utf-8')
