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
    
    Uses google-crc32c library for proper CRC32C calculation matching GCS.
    
    Args:
        data: Raw bytes to hash
        
    Returns:
        Base64-encoded CRC32C checksum string
    """
    import google_crc32c
    
    # Calculate CRC32C checksum using Google's library
    checksum = google_crc32c.Checksum()
    checksum.update(data)
    crc_value = checksum.digest()
    
    # Return base64-encoded result
    return base64.b64encode(crc_value).decode('utf-8')
