"""
Resumable Upload Service - Handles resumable upload sessions

Implements simplified GCS resumable upload flow:
1. Initiate session (POST)
2. Upload chunks (PUT)
3. Finalize object on last chunk
"""
import os
import uuid
import json
from pathlib import Path
from typing import Tuple, Optional
from app.factory import db
from app.models.resumable_session import ResumableSession
from app.models.bucket import Bucket
from app.services.object_versioning_service import ObjectVersioningService
from app.utils.hashing import calculate_md5, calculate_crc32c


class ResumableUploadService:
    """Service for resumable upload operations"""
    
    STORAGE_PATH = os.getenv("STORAGE_PATH", "./storage")
    TMP_PATH = str(Path(STORAGE_PATH) / "tmp")
    
    @staticmethod
    def initiate_session(
        bucket_name: str,
        object_name: str,
        metadata: dict,
        total_size: Optional[int] = None
    ) -> ResumableSession:
        """
        Initiate a resumable upload session
        
        Args:
            bucket_name: Target bucket name
            object_name: Target object name
            metadata: Object metadata (contentType, etc.)
            total_size: Total upload size if known
            
        Returns:
            ResumableSession instance
            
        Raises:
            ValueError: If bucket doesn't exist
        """
        # Validate bucket exists
        bucket = Bucket.query.filter_by(name=bucket_name).first()
        if not bucket:
            raise ValueError(f"Bucket '{bucket_name}' not found")
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Create tmp directory if not exists
        tmp_dir = Path(ResumableUploadService.TMP_PATH)
        tmp_dir.mkdir(parents=True, exist_ok=True)
        
        # Create temp file path
        temp_path = str(tmp_dir / session_id)
        
        # Create session record
        session = ResumableSession(
            session_id=session_id,
            bucket_id=bucket.id,
            object_name=object_name,
            metadata_json=json.dumps(metadata),
            current_offset=0,
            total_size=total_size,
            temp_path=temp_path
        )
        
        db.session.add(session)
        db.session.commit()
        
        return session
    
    @staticmethod
    def upload_chunk(
        session_id: str,
        chunk_data: bytes,
        content_range: str
    ) -> Tuple[bool, int, Optional[dict]]:
        """
        Upload a chunk to resumable session
        
        Args:
            session_id: Session ID
            chunk_data: Binary chunk data
            content_range: Content-Range header value
            
        Returns:
            Tuple of (is_complete, current_offset, object_metadata or None)
            
        Raises:
            ValueError: If session not found or offset mismatch
        """
        # Get session
        session = ResumableSession.query.filter_by(session_id=session_id).first()
        if not session:
            raise ValueError(f"Session '{session_id}' not found")
        
        # Parse Content-Range: bytes start-end/total OR bytes */total
        start, end, total = ResumableUploadService._parse_content_range(content_range)
        
        # Validate offset matches current position (simple linear append)
        if start is not None and start != session.current_offset:
            raise ValueError(
                f"Offset mismatch: expected {session.current_offset}, got {start}"
            )
        
        # Append chunk to temp file
        temp_file = Path(session.temp_path)
        with open(temp_file, 'ab') as f:
            f.write(chunk_data)
        
        # Update offset
        session.current_offset += len(chunk_data)
        
        # Update total size if provided
        if total is not None and total > 0:
            session.total_size = total
        
        # Check if complete
        is_complete = False
        object_metadata = None
        
        if session.total_size and session.current_offset >= session.total_size:
            # Finalize upload
            is_complete = True
            object_metadata = ResumableUploadService._finalize_upload(session)
            
            # Cleanup session and temp file
            db.session.delete(session)
            if temp_file.exists():
                temp_file.unlink()
        
        db.session.commit()
        
        return is_complete, session.current_offset, object_metadata
    
    @staticmethod
    def get_session(session_id: str) -> Optional[ResumableSession]:
        """Get session by ID"""
        return ResumableSession.query.filter_by(session_id=session_id).first()
    
    @staticmethod
    def _parse_content_range(content_range: str) -> Tuple[Optional[int], Optional[int], Optional[int]]:
        """
        Parse Content-Range header
        
        Examples:
            "bytes 0-999/1000" -> (0, 999, 1000)
            "bytes */1000" -> (None, None, 1000)
            
        Returns:
            Tuple of (start, end, total)
        """
        if not content_range or not content_range.startswith("bytes "):
            return None, None, None
        
        range_part = content_range[6:]  # Remove "bytes "
        
        if range_part.startswith("*/"):
            # Format: bytes */total
            total = int(range_part[2:])
            return None, None, total
        
        # Format: bytes start-end/total
        parts = range_part.split('/')
        if len(parts) != 2:
            return None, None, None
        
        range_str, total_str = parts
        total = int(total_str) if total_str != '*' else None
        
        if '-' in range_str:
            start_str, end_str = range_str.split('-')
            start = int(start_str)
            end = int(end_str)
            return start, end, total
        
        return None, None, total
    
    @staticmethod
    def _finalize_upload(session: ResumableSession) -> dict:
        """
        Finalize resumable upload - create actual object
        
        Args:
            session: ResumableSession to finalize
            
        Returns:
            Object metadata dict
        """
        # Read complete file from temp
        temp_file = Path(session.temp_path)
        content = temp_file.read_bytes()
        
        # Parse metadata
        metadata = json.loads(session.metadata_json) if session.metadata_json else {}
        content_type = metadata.get("contentType", "application/octet-stream")
        
        # Get bucket
        bucket = Bucket.query.filter_by(id=session.bucket_id).first()
        
        # Create object using versioning service
        obj = ObjectVersioningService.upload_object_with_versioning(
            bucket_name=bucket.name,
            object_name=session.object_name,
            content=content,
            content_type=content_type
        )
        
        return obj.to_dict()
