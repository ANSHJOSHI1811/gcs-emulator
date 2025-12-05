"""
Request logging middleware for Flask
Handles request start/end logging and context management
"""
import time
from functools import wraps
from flask import Flask, request, g
from app.logging import logger, log_emulator_stage


def setup_request_logging(app: Flask) -> None:
    """
    Setup request logging middleware for the Flask app
    
    Args:
        app: Flask application instance
    """
    
    @app.before_request
    def before_request():
        """Log request start and setup timing"""
        # Start request timing
        g.start_time = time.time()
        
        # Log request start with HTTP details
        request_id = logger.log_request_start()
        g.request_id = request_id
        
        # Log emulator stage - HTTP request received
        log_emulator_stage(
            message="HTTP request received",
            details={
                "method": request.method,
                "path": request.path,
                "query_string": request.query_string.decode(),
                "content_type": request.content_type,
                "content_length": request.content_length or 0,
                "remote_addr": request.remote_addr
            }
        )
    
    @app.after_request  
    def after_request(response):
        """Log request completion with response details"""
        # Calculate total request duration
        total_duration = (time.time() - g.start_time) * 1000
        
        # Log request end
        status_label = "error" if response.status_code >= 400 else "success"

        logger.log_request_end(
            total_duration_ms=total_duration,
            final_status=response.status_code,
            status=status_label
        )
        
        return response
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        """Log unhandled exceptions"""
        logger.log_error(
            stage="middleware_error_handler",
            message=f"Unhandled exception: {type(error).__name__}",
            error=error,
            details={
                "request_method": request.method if request else "unknown",
                "request_path": request.path if request else "unknown"
            }
        )
        
        # Re-raise the exception to let Flask handle it normally
        raise error


def log_performance(stage_name: str):
    """
    Decorator to log performance timing for functions
    
    Args:
        stage_name: Name of the stage being timed
        
    Usage:
        @log_performance("handler_validation")
        def validate_input(data):
            # function logic
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                logger.log_stage(
                    stage=stage_name,
                    message=f"Function {func.__name__} completed",
                    duration_ms=duration_ms,
                    details={
                        "function": func.__name__,
                        "args_count": len(args),
                        "kwargs_count": len(kwargs)
                    }
                )
                
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                
                logger.log_error(
                    stage=stage_name,
                    message=f"Function {func.__name__} failed",
                    error=e,
                    details={
                        "function": func.__name__,
                        "duration_ms": duration_ms
                    }
                )
                raise
        
        return wrapper
    return decorator