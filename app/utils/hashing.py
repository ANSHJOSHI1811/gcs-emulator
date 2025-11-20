"""
Hashing utilities - MD5 and CRC32C calculation
"""
import hashlib
import base64
import crcmod


def calculate_md5(data: bytes) -> str:
    """
    Calculate MD5 hash of data
    
    Args:
        data: Binary data
        
    Returns:
        Base64-encoded MD5 hash
    """
    md5 = hashlib.md5(data).digest()
    return base64.b64encode(md5).decode('utf-8')


def calculate_crc32c(data: bytes) -> str:
    """
    Calculate CRC32C hash of data (Google's standard)
    
    Args:
        data: Binary data
        
    Returns:
        Base64-encoded CRC32C hash
    """
    crc32c_func = crcmod.mkCrcFun(0x11EDC6F41, rev=True, initCrc=0, xorOut=0xFFFFFFFF)
    crc32c = crc32c_func(data)
    crc32c_bytes = crc32c.to_bytes(4, byteorder='big')
    return base64.b64encode(crc32c_bytes).decode('utf-8')
