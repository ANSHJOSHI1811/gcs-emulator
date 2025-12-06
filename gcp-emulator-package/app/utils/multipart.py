"""
Multipart Parser Utility for GCS Multipart Uploads

Parses multipart/related request bodies according to GCS API specification.

GCS Multipart Format:
    --BOUNDARY_STRING
    Content-Type: application/json; charset=UTF-8
    
    {"name": "object-name", "contentType": "text/plain"}
    
    --BOUNDARY_STRING
    Content-Type: text/plain
    
    <file content bytes>
    --BOUNDARY_STRING--

Reference: https://cloud.google.com/storage/docs/uploading-objects#multipart-upload
"""
import re
import json
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class MultipartUploadData:
    """Container for parsed multipart upload data."""
    object_name: str
    content: bytes
    content_type: str
    metadata: dict


class MultipartParseError(Exception):
    """Raised when multipart parsing fails."""
    pass


def extract_boundary(content_type: str) -> str:
    """
    Extract the boundary string from Content-Type header.
    
    Args:
        content_type: Content-Type header value like 
                     'multipart/related; boundary=----=_Part_0_1234567890'
    
    Returns:
        The boundary string without quotes
        
    Raises:
        MultipartParseError: If boundary cannot be extracted
    """
    if not content_type:
        raise MultipartParseError("Content-Type header is required")
    
    # Check if it's multipart/related or multipart/form-data
    if "multipart/" not in content_type.lower():
        raise MultipartParseError(f"Expected multipart content type, got: {content_type}")
    
    # Extract boundary parameter
    # Format: boundary="value" or boundary=value
    match = re.search(r'boundary=(["\']?)([^"\';,\s]+)\1', content_type, re.IGNORECASE)
    if not match:
        raise MultipartParseError(f"Could not extract boundary from Content-Type: {content_type}")
    
    return match.group(2)


def parse_multipart_body(body: bytes, boundary: str) -> MultipartUploadData:
    """
    Parse a multipart/related request body into its components.
    
    The GCS multipart format consists of two parts:
    1. JSON metadata containing at minimum the object name
    2. Binary content of the file
    
    Args:
        body: Raw request body bytes
        boundary: The boundary string extracted from Content-Type header
        
    Returns:
        MultipartUploadData with parsed object name, content, and metadata
        
    Raises:
        MultipartParseError: If parsing fails
    """
    # Normalize boundary (remove leading dashes if present in boundary value)
    boundary_bytes = boundary.encode('utf-8')
    
    # Split body by boundary
    # Each boundary is preceded by -- and followed by CRLF or -- for final boundary
    delimiter = b'--' + boundary_bytes
    final_delimiter = delimiter + b'--'
    
    # Remove final boundary marker first
    if final_delimiter in body:
        body = body.split(final_delimiter)[0]
    
    # Split by boundary
    parts = body.split(delimiter)
    
    # Filter out empty parts (first split usually empty)
    parts = [p for p in parts if p.strip()]
    
    if len(parts) < 2:
        raise MultipartParseError(f"Expected at least 2 parts, got {len(parts)}")
    
    # Parse first part - JSON metadata
    metadata_part = parts[0]
    metadata, _ = _parse_part(metadata_part)
    
    try:
        metadata_json = json.loads(metadata.decode('utf-8'))
    except json.JSONDecodeError as e:
        raise MultipartParseError(f"Failed to parse JSON metadata: {e}")
    
    # Extract object name from metadata
    object_name = metadata_json.get('name')
    if not object_name:
        raise MultipartParseError("Missing 'name' field in metadata")
    
    # Parse second part - file content
    content_part = parts[1]
    content, content_headers = _parse_part(content_part)
    
    # Get content type from part headers or metadata
    content_type = content_headers.get('content-type', 
                   metadata_json.get('contentType', 'application/octet-stream'))
    
    return MultipartUploadData(
        object_name=object_name,
        content=content,
        content_type=content_type,
        metadata=metadata_json
    )


def _parse_part(part: bytes) -> Tuple[bytes, dict]:
    """
    Parse a single multipart part into headers and body.
    
    Part format:
        [headers]
        [blank line]
        [body]
    
    Args:
        part: Raw part bytes (may start with CRLF from boundary split)
        
    Returns:
        Tuple of (body_bytes, headers_dict)
    """
    # Strip leading CRLF or whitespace
    part = part.lstrip(b'\r\n')
    
    # Find the separator between headers and body (double CRLF)
    separator_patterns = [b'\r\n\r\n', b'\n\n']
    
    header_end = -1
    separator_len = 0
    
    for sep in separator_patterns:
        idx = part.find(sep)
        if idx != -1 and (header_end == -1 or idx < header_end):
            header_end = idx
            separator_len = len(sep)
    
    if header_end == -1:
        # No headers, entire part is body
        return part, {}
    
    header_section = part[:header_end]
    body = part[header_end + separator_len:]
    
    # Parse headers
    headers = {}
    header_lines = header_section.decode('utf-8', errors='replace').split('\n')
    
    for line in header_lines:
        line = line.strip()
        if ':' in line:
            key, value = line.split(':', 1)
            headers[key.strip().lower()] = value.strip()
    
    # Strip trailing CRLF from body
    body = body.rstrip(b'\r\n')
    
    return body, headers


def create_multipart_body(object_name: str, content: bytes, 
                          content_type: str = "application/octet-stream",
                          metadata: Optional[dict] = None) -> Tuple[bytes, str]:
    """
    Create a multipart/related request body (useful for testing).
    
    Args:
        object_name: Name of the object
        content: File content bytes
        content_type: MIME type of the content
        metadata: Additional metadata fields (optional)
        
    Returns:
        Tuple of (body_bytes, content_type_header)
    """
    boundary = "----=_Part_0_GCSLocalStack"
    
    # Build metadata JSON
    meta = {"name": object_name}
    if content_type != "application/octet-stream":
        meta["contentType"] = content_type
    if metadata:
        meta.update(metadata)
    
    metadata_json = json.dumps(meta, indent=None)
    
    # Build multipart body
    parts = []
    parts.append(f"--{boundary}\r\n")
    parts.append("Content-Type: application/json; charset=UTF-8\r\n")
    parts.append("\r\n")
    parts.append(f"{metadata_json}\r\n")
    parts.append(f"--{boundary}\r\n")
    parts.append(f"Content-Type: {content_type}\r\n")
    parts.append("\r\n")
    
    # Combine text parts, then add binary content
    header_bytes = "".join(parts).encode('utf-8')
    footer_bytes = f"\r\n--{boundary}--\r\n".encode('utf-8')
    
    body = header_bytes + content + footer_bytes
    content_type_header = f"multipart/related; boundary={boundary}"
    
    return body, content_type_header
