"""
Input Validation Middleware - Sanitize and validate all inputs

Provides:
- Request body validation
- Query parameter validation
- Path parameter validation
- SQL injection prevention
- XSS prevention
- Schema validation
"""

import re
import bleach
from functools import wraps
from flask import request, jsonify
from typing import Dict, Any, List, Optional


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


class InputValidator:
    """Input validation utilities"""
    
    # Common validation patterns
    PATTERNS = {
        'project_id': re.compile(r'^[a-z][a-z0-9-]{4,28}[a-z0-9]$'),
        'bucket_name': re.compile(r'^[a-z0-9][a-z0-9-_.]{1,61}[a-z0-9]$'),
        'instance_name': re.compile(r'^[a-z][a-z0-9-]{0,61}[a-z0-9]$'),
        'network_name': re.compile(r'^[a-z][a-z0-9-]{0,61}[a-z0-9]$'),
        'zone': re.compile(r'^[a-z]+-[a-z]+\d-[a-z]$'),
        'region': re.compile(r'^[a-z]+-[a-z]+\d$'),
        'email': re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'),
        'ip_address': re.compile(r'^(\d{1,3}\.){3}\d{1,3}$'),
        'cidr': re.compile(r'^(\d{1,3}\.){3}\d{1,3}/\d{1,2}$'),
    }
    
    # SQL injection patterns to block
    SQL_INJECTION_PATTERNS = [
        re.compile(r"(\bUNION\b|\bSELECT\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b|\bDROP\b|\bCREATE\b)", re.IGNORECASE),
        re.compile(r"(--|;|\/\*|\*\/)", re.IGNORECASE),
        re.compile(r"(\bOR\b\s+\d+\s*=\s*\d+|\bAND\b\s+\d+\s*=\s*\d+)", re.IGNORECASE),
    ]
    
    # XSS patterns to sanitize
    XSS_PATTERNS = [
        re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL),
        re.compile(r'javascript:', re.IGNORECASE),
        re.compile(r'on\w+\s*=', re.IGNORECASE),
    ]
    
    @staticmethod
    def validate_pattern(value: str, pattern_name: str) -> bool:
        """
        Validate value against named pattern
        
        Args:
            value: Value to validate
            pattern_name: Name of pattern from PATTERNS dict
        
        Returns:
            True if valid, False otherwise
        """
        pattern = InputValidator.PATTERNS.get(pattern_name)
        if not pattern:
            return True  # Unknown pattern, skip validation
        
        return bool(pattern.match(str(value)))
    
    @staticmethod
    def check_sql_injection(value: str) -> bool:
        """
        Check if value contains SQL injection attempts
        
        Returns:
            True if SQL injection detected, False otherwise
        """
        for pattern in InputValidator.SQL_INJECTION_PATTERNS:
            if pattern.search(str(value)):
                return True
        return False
    
    @staticmethod
    def sanitize_html(value: str, allowed_tags: List[str] = None) -> str:
        """
        Sanitize HTML content to prevent XSS
        
        Args:
            value: HTML content to sanitize
            allowed_tags: List of allowed HTML tags
        
        Returns:
            Sanitized HTML string
        """
        if allowed_tags is None:
            allowed_tags = []  # No HTML allowed by default
        
        return bleach.clean(
            str(value),
            tags=allowed_tags,
            strip=True
        )
    
    @staticmethod
    def validate_length(value: str, min_length: int = None, max_length: int = None) -> bool:
        """Validate string length"""
        length = len(str(value))
        
        if min_length is not None and length < min_length:
            return False
        
        if max_length is not None and length > max_length:
            return False
        
        return True
    
    @staticmethod
    def validate_range(value: int, min_value: int = None, max_value: int = None) -> bool:
        """Validate numeric range"""
        try:
            num = int(value)
            
            if min_value is not None and num < min_value:
                return False
            
            if max_value is not None and num > max_value:
                return False
            
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_enum(value: str, allowed_values: List[str]) -> bool:
        """Validate value is in allowed list"""
        return str(value) in allowed_values
    
    @staticmethod
    def validate_schema(data: Dict[str, Any], schema: Dict[str, Dict]) -> List[str]:
        """
        Validate data against schema
        
        Args:
            data: Dictionary to validate
            schema: Schema definition with field rules
        
        Schema format:
            {
                'field_name': {
                    'required': True,
                    'type': 'string',  # 'string', 'int', 'float', 'bool', 'list', 'dict'
                    'pattern': 'project_id',  # Pattern name
                    'min_length': 5,
                    'max_length': 100,
                    'min_value': 0,
                    'max_value': 1000,
                    'allowed_values': ['value1', 'value2']
                }
            }
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        for field_name, rules in schema.items():
            value = data.get(field_name)
            
            # Check required
            if rules.get('required', False) and value is None:
                errors.append(f"Field '{field_name}' is required")
                continue
            
            # Skip validation if field is optional and not provided
            if value is None:
                continue
            
            # Check type
            expected_type = rules.get('type')
            if expected_type:
                type_mapping = {
                    'string': str,
                    'int': int,
                    'float': float,
                    'bool': bool,
                    'list': list,
                    'dict': dict
                }
                expected_py_type = type_mapping.get(expected_type)
                if expected_py_type and not isinstance(value, expected_py_type):
                    errors.append(f"Field '{field_name}' must be of type {expected_type}")
                    continue
            
            # String validations
            if isinstance(value, str):
                # Check pattern
                pattern = rules.get('pattern')
                if pattern and not InputValidator.validate_pattern(value, pattern):
                    errors.append(f"Field '{field_name}' has invalid format")
                
                # Check length
                min_length = rules.get('min_length')
                max_length = rules.get('max_length')
                if not InputValidator.validate_length(value, min_length, max_length):
                    errors.append(f"Field '{field_name}' length must be between {min_length} and {max_length}")
                
                # Check SQL injection
                if InputValidator.check_sql_injection(value):
                    errors.append(f"Field '{field_name}' contains invalid characters")
            
            # Numeric validations
            if isinstance(value, (int, float)):
                min_value = rules.get('min_value')
                max_value = rules.get('max_value')
                if not InputValidator.validate_range(value, min_value, max_value):
                    errors.append(f"Field '{field_name}' must be between {min_value} and {max_value}")
            
            # Enum validation
            allowed_values = rules.get('allowed_values')
            if allowed_values and not InputValidator.validate_enum(value, allowed_values):
                errors.append(f"Field '{field_name}' must be one of: {', '.join(allowed_values)}")
        
        return errors


def validate_request(body_schema: Dict = None, query_schema: Dict = None, path_schema: Dict = None):
    """
    Decorator to validate request inputs
    
    Args:
        body_schema: Schema for request body (JSON)
        query_schema: Schema for query parameters
        path_schema: Schema for path parameters
    
    Usage:
        @app.route('/api/projects/<project_id>/buckets', methods=['POST'])
        @validate_request(
            body_schema={
                'name': {'required': True, 'pattern': 'bucket_name'},
                'location': {'required': True, 'pattern': 'region'}
            },
            path_schema={
                'project_id': {'required': True, 'pattern': 'project_id'}
            }
        )
        def create_bucket(project_id):
            ...
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            errors = []
            
            # Validate request body
            if body_schema:
                try:
                    data = request.get_json() or {}
                except Exception:
                    return jsonify({
                        'error': {
                            'code': 400,
                            'message': 'Invalid JSON in request body',
                            'status': 'INVALID_ARGUMENT'
                        }
                    }), 400
                
                body_errors = InputValidator.validate_schema(data, body_schema)
                errors.extend([f"Body: {e}" for e in body_errors])
            
            # Validate query parameters
            if query_schema:
                query_data = dict(request.args)
                query_errors = InputValidator.validate_schema(query_data, query_schema)
                errors.extend([f"Query: {e}" for e in query_errors])
            
            # Validate path parameters
            if path_schema:
                path_errors = InputValidator.validate_schema(kwargs, path_schema)
                errors.extend([f"Path: {e}" for e in path_errors])
            
            # Return validation errors if any
            if errors:
                return jsonify({
                    'error': {
                        'code': 400,
                        'message': 'Validation failed',
                        'status': 'INVALID_ARGUMENT',
                        'details': errors
                    }
                }), 400
            
            # All validations passed
            return f(*args, **kwargs)
        
        return wrapper
    return decorator


def sanitize_output(data: Any, sanitize_html_fields: List[str] = None) -> Any:
    """
    Sanitize output data before sending response
    
    Args:
        data: Data to sanitize (dict, list, or primitive)
        sanitize_html_fields: List of field names to sanitize HTML
    
    Returns:
        Sanitized data
    """
    sanitize_html_fields = sanitize_html_fields or []
    
    if isinstance(data, dict):
        return {
            key: InputValidator.sanitize_html(value, []) if key in sanitize_html_fields 
                 else sanitize_output(value, sanitize_html_fields)
            for key, value in data.items()
        }
    elif isinstance(data, list):
        return [sanitize_output(item, sanitize_html_fields) for item in data]
    elif isinstance(data, str):
        # Basic XSS prevention for all strings
        for pattern in InputValidator.XSS_PATTERNS:
            data = pattern.sub('', data)
        return data
    else:
        return data
