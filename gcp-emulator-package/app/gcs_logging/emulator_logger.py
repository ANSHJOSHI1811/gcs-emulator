"""
Execution logging system for GCS Emulator
Provides structured logging with request tracing across all 8 pipeline stages
"""
import json
import time
import uuid
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any
from contextvars import ContextVar
from flask import request as flask_request, has_request_context, current_app
# Context variable to store request ID across the request lifecycle
current_request_id: ContextVar[str] = ContextVar('request_id', default='')

class EmulatorLogger:
    """
    Centralized logging system for the GCS Emulator
    Writes structured JSON logs with request tracing
    """
    
    def __init__(self, log_file_path: str = "logs/emulator.log"):
        self.log_file_path = Path(log_file_path)
        # Ensure log directory exists
        self.log_file_path.parent.mkdir(parents=True, exist_ok=True)
        # Thread lock for safe concurrent file writing
        self._file_lock = threading.Lock()
        # Maximum file size before rotation (100MB)
        self.max_file_size = 100 * 1024 * 1024
        
    def _get_request_id(self) -> str:
        """Get current request ID from context"""
        request_id = current_request_id.get('')
        if not request_id and has_request_context():
            # Generate new request ID if none exists
            request_id = f"req_{uuid.uuid4().hex[:12]}"
            current_request_id.set(request_id)
        return request_id
    
    def _write_log_entry(self, entry: Dict[str, Any]) -> None:
        """Write a single log entry to the log file and Flask logger with thread safety"""
        log_line = json.dumps(entry, separators=(',', ':'))
        
        # Write to file with thread safety and rotation
        with self._file_lock:
            try:
                # Check if rotation needed
                if self.log_file_path.exists() and self.log_file_path.stat().st_size > self.max_file_size:
                    self._rotate_log_file()
                
                # Write to log file
                with open(self.log_file_path, 'a', encoding='utf-8') as f:
                    f.write(log_line + '\n')
                    f.flush()  # Ensure immediate write to disk
                    
            except Exception as e:
                # Fallback - write to stderr if log file fails
                import sys
                print(f"File logging failed: {e}", file=sys.stderr)
        
        # Also write to Flask logger for pytest caplog compatibility
        try:
            if current_app:
                flask_logger = current_app.logger
                level = getattr(logging, entry.get('level', 'INFO').upper(), logging.INFO)
                flask_logger.log(level, log_line)
        except Exception:
            # If Flask app context not available, use standard logging
            try:
                level = getattr(logging, entry.get('level', 'INFO').upper(), logging.INFO)
                logging.log(level, log_line)
            except Exception:
                pass
    
    def log_stage(self, 
                  stage: str, 
                  message: str, 
                  level: str = "INFO",
                  details: Optional[Dict[str, Any]] = None,
                  duration_ms: Optional[float] = None,
                  status: str = "success") -> None:
        """
        Log a pipeline stage execution
        
        Args:
            stage: Pipeline stage identifier (e.g., 'stage_5_handler')
            message: Human-readable description
            level: Log level (DEBUG, INFO, WARN, ERROR, FATAL)
            details: Stage-specific structured data
            duration_ms: Time spent in this stage
            status: Outcome (success, error, pending)
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "request_id": self._get_request_id(),
            "stage": stage,
            "level": level,
            "message": message,
            "status": status
        }
        
        if details:
            entry["details"] = details
        if duration_ms is not None:
            entry["duration_ms"] = round(duration_ms, 2)
            
        self._write_log_entry(entry)
    
    def log_request_start(self, details: Optional[Dict[str, Any]] = None) -> str:
        """
        Log the start of a new request and return the request ID
        
        Args:
            details: Request-specific details (HTTP method, path, etc.)
            
        Returns:
            Generated request ID
        """
        request_id = f"req_{uuid.uuid4().hex[:12]}"
        current_request_id.set(request_id)
        
        default_details = {}
        if has_request_context():
            default_details.update({
                "method": flask_request.method,
                "path": flask_request.path,
                "content_length": flask_request.content_length or 0,
                "user_agent": flask_request.headers.get('User-Agent', 'unknown')
            })
        
        if details:
            default_details.update(details)
        
        self.log_stage(
            stage="request_start",
            message="New request initiated",
            details=default_details
        )
        
        return request_id
    
    def log_request_end(self, 
                       total_duration_ms: float,
                       final_status: int,
                       stages_executed: int = 8,
                       status: Optional[str] = None) -> None:
        """
        Log the completion of a request
        
        Args:
            total_duration_ms: Total time for request processing
            final_status: Final HTTP status code
            stages_executed: Number of pipeline stages executed
        """
        resolved_status = status or ("error" if final_status >= 400 else "success")

        self.log_stage(
            stage="request_end",
            message="Request completed",
            duration_ms=total_duration_ms,
            status=resolved_status,
            details={
                "final_status": final_status,
                "stages_executed": stages_executed
            }
        )
    
    def _rotate_log_file(self) -> None:
        """Rotate log file when size limit exceeded"""
        try:
            # Find next available rotation number
            rotation_num = 1
            while True:
                rotated_path = Path(f"{self.log_file_path}.{rotation_num}")
                if not rotated_path.exists():
                    break
                rotation_num += 1
            
            # Move current log to rotated name
            self.log_file_path.rename(rotated_path)
            
        except Exception as e:
            import sys
            print(f"Log rotation failed: {e}", file=sys.stderr)
    
    def log_error(self, 
                  stage: str,
                  message: str,
                  error: Exception,
                  details: Optional[Dict[str, Any]] = None) -> None:
        """
        Log an error with full context
        
        Args:
            stage: Pipeline stage where error occurred
            message: Error description
            error: Exception instance
            details: Additional error context
        """
        error_details = {
            "error_type": type(error).__name__,
            "error_message": str(error)
        }
        
        if details:
            error_details.update(details)
            
        # Add stack trace for debugging
        import traceback
        error_details["stacktrace"] = traceback.format_exc()
        
        self.log_stage(
            stage=stage,
            message=message,
            level="ERROR",
            details=error_details,
            status="error"
        )

    def _extract_stage_number(self, stage: str) -> int:
        """Extract numeric stage from stage identifier"""
        stage_mapping = {
            "stage_1_client": 1,
            "stage_2_options": 2, 
            "stage_3_emulator": 3,
            "stage_4_router": 4,
            "stage_5_handler": 5,
            "stage_6_service": 6,
            "stage_7_repository": 7,
            "stage_8_formatter": 8
        }
        return stage_mapping.get(stage, 0)
    
    def _extract_stage_name(self, stage: str) -> str:
        """Extract readable stage name from stage identifier"""
        name_mapping = {
            "stage_1_client": "Client SDK",
            "stage_2_options": "ClientOptions",
            "stage_3_emulator": "Emulator", 
            "stage_4_router": "Router",
            "stage_5_handler": "Handler",
            "stage_6_service": "Service",
            "stage_7_repository": "Repository",
            "stage_8_formatter": "Response Formatter"
        }
        return name_mapping.get(stage, stage.replace("_", " ").title())
    
    def clear_log_file(self) -> None:
        """Clear the log file for testing purposes"""
        with self._file_lock:
            try:
                if self.log_file_path.exists():
                    self.log_file_path.unlink()
            except Exception as e:
                import sys
                print(f"Failed to clear log file: {e}", file=sys.stderr)
    
    def read_log_entries(self) -> list[Dict[str, Any]]:
        """Read and parse all log entries from file"""
        entries = []
        try:
            if self.log_file_path.exists():
                with open(self.log_file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                entries.append(json.loads(line))
                            except json.JSONDecodeError:
                                pass  # Skip malformed lines
        except Exception:
            pass  # Return empty list if file read fails
        return entries


# Global logger instance
logger = EmulatorLogger()


# Stage-specific logging functions for easy use
def log_emulator_stage(message: str, details: Optional[Dict[str, Any]] = None, duration_ms: Optional[float] = None, **kwargs):
    """Log Stage 3: Emulator reception"""
    logger.log_stage("stage_3_emulator", message, details=details, duration_ms=duration_ms)

def log_router_stage(message: str, details: Optional[Dict[str, Any]] = None, duration_ms: Optional[float] = None, **kwargs):
    """Log Stage 4: Router mapping"""
    logger.log_stage("stage_4_router", message, details=details, duration_ms=duration_ms)

def log_handler_stage(message: str, details: Optional[Dict[str, Any]] = None, duration_ms: Optional[float] = None, **kwargs):
    """Log Stage 5: Handler processing"""
    logger.log_stage("stage_5_handler", message, details=details, duration_ms=duration_ms)

def log_service_stage(message: str, details: Optional[Dict[str, Any]] = None, duration_ms: Optional[float] = None, **kwargs):
    """Log Stage 6: Service business logic"""
    logger.log_stage("stage_6_service", message, details=details, duration_ms=duration_ms)

def log_repository_stage(message: str, details: Optional[Dict[str, Any]] = None, duration_ms: Optional[float] = None, **kwargs):
    """Log Stage 7: Repository/Database"""
    logger.log_stage("stage_7_repository", message, details=details, duration_ms=duration_ms)

def log_formatter_stage(message: str, details: Optional[Dict[str, Any]] = None, duration_ms: Optional[float] = None, **kwargs):
    """Log Stage 8: Response formatting"""
    logger.log_stage("stage_8_formatter", message, details=details, duration_ms=duration_ms)


# Test utilities
def clear_log_file():
    """Clear log file for testing"""
    logger.clear_log_file()

def get_log_entries() -> list[Dict[str, Any]]:
    """Get all log entries for testing"""
    return logger.read_log_entries()

def get_log_entries_for_request(request_id: str) -> list[Dict[str, Any]]:
    """Get log entries for specific request ID"""
    return [entry for entry in logger.read_log_entries() if entry.get('request_id') == request_id]