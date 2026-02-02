"""
Security Headers Middleware - Add security headers to all responses

Implements:
- Content Security Policy (CSP)
- HSTS (HTTP Strict Transport Security)
- X-Frame-Options
- X-Content-Type-Options
- X-XSS-Protection
- Referrer-Policy
- Permissions-Policy
"""

from flask import Flask, Response
from typing import Dict, Optional


class SecurityHeaders:
    """Security headers configuration and middleware"""
    
    # Default security headers for production
    DEFAULT_HEADERS = {
        # Prevent clickjacking
        'X-Frame-Options': 'DENY',
        
        # Prevent MIME type sniffing
        'X-Content-Type-Options': 'nosniff',
        
        # Enable XSS protection (legacy browsers)
        'X-XSS-Protection': '1; mode=block',
        
        # Control referrer information
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        
        # Content Security Policy - restrictive by default
        'Content-Security-Policy': (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        ),
        
        # Permissions Policy (formerly Feature-Policy)
        'Permissions-Policy': (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "accelerometer=(), "
            "gyroscope=()"
        ),
        
        # Remove server information
        'Server': 'GCP-Stimulator',
    }
    
    # HSTS header (only for HTTPS)
    HSTS_HEADER = {
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload'
    }
    
    # Relaxed CSP for development/API
    API_CSP = {
        'Content-Security-Policy': "default-src 'self' *; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'"
    }
    
    @staticmethod
    def get_default_headers(is_https: bool = False, is_api: bool = False) -> Dict[str, str]:
        """
        Get appropriate security headers
        
        Args:
            is_https: Whether connection is HTTPS
            is_api: Whether this is an API endpoint (relaxed CSP)
        
        Returns:
            Dictionary of security headers
        """
        headers = SecurityHeaders.DEFAULT_HEADERS.copy()
        
        # Add HSTS for HTTPS connections
        if is_https:
            headers.update(SecurityHeaders.HSTS_HEADER)
        
        # Use relaxed CSP for API endpoints
        if is_api:
            headers.update(SecurityHeaders.API_CSP)
        
        return headers
    
    @staticmethod
    def apply_to_response(response: Response, custom_headers: Dict[str, str] = None,
                         is_https: bool = False, is_api: bool = False) -> Response:
        """
        Apply security headers to Flask response
        
        Args:
            response: Flask Response object
            custom_headers: Optional custom headers to override defaults
            is_https: Whether connection is HTTPS
            is_api: Whether this is an API endpoint
        
        Returns:
            Response with security headers added
        """
        # Get default headers
        headers = SecurityHeaders.get_default_headers(is_https, is_api)
        
        # Override with custom headers if provided
        if custom_headers:
            headers.update(custom_headers)
        
        # Apply headers to response
        for header, value in headers.items():
            response.headers[header] = value
        
        return response


def add_security_headers(app: Flask, custom_headers: Dict[str, str] = None,
                        api_paths: list = None):
    """
    Add security headers middleware to Flask app
    
    Args:
        app: Flask application instance
        custom_headers: Optional custom headers to override defaults
        api_paths: List of path prefixes to treat as API endpoints (relaxed CSP)
    
    Usage:
        app = Flask(__name__)
        add_security_headers(app, api_paths=['/api', '/storage', '/compute'])
    """
    api_paths = api_paths or ['/api', '/v1', '/storage', '/compute', '/cloudresourcemanager']
    
    @app.after_request
    def apply_security_headers(response):
        # Check if HTTPS
        is_https = app.config.get('HTTPS_ENABLED', False) or 'https' in str(response.headers.get('Location', ''))
        
        # Check if API endpoint
        is_api = any(response.request.path.startswith(path) for path in api_paths) if hasattr(response, 'request') else True
        
        # Apply headers
        response = SecurityHeaders.apply_to_response(
            response,
            custom_headers=custom_headers,
            is_https=is_https,
            is_api=is_api
        )
        
        return response
    
    print("✅ Security headers middleware enabled")
    print(f"   API paths (relaxed CSP): {', '.join(api_paths)}")


def add_cors_headers(app: Flask, allowed_origins: list = None, 
                    allowed_methods: list = None, allowed_headers: list = None):
    """
    Add CORS (Cross-Origin Resource Sharing) headers
    
    Args:
        app: Flask application instance
        allowed_origins: List of allowed origins (default: ['*'])
        allowed_methods: List of allowed HTTP methods
        allowed_headers: List of allowed headers
    
    Usage:
        app = Flask(__name__)
        add_cors_headers(app, allowed_origins=['http://localhost:3000'])
    """
    allowed_origins = allowed_origins or ['*']
    allowed_methods = allowed_methods or ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS']
    allowed_headers = allowed_headers or ['Content-Type', 'Authorization', 'X-API-Key']
    
    @app.after_request
    def apply_cors_headers(response):
        # Get origin from request
        origin = response.request.headers.get('Origin', '*') if hasattr(response, 'request') else '*'
        
        # Check if origin is allowed
        if '*' in allowed_origins or origin in allowed_origins:
            response.headers['Access-Control-Allow-Origin'] = origin
        
        response.headers['Access-Control-Allow-Methods'] = ', '.join(allowed_methods)
        response.headers['Access-Control-Allow-Headers'] = ', '.join(allowed_headers)
        response.headers['Access-Control-Max-Age'] = '3600'
        
        # Allow credentials if not wildcard origin
        if origin != '*':
            response.headers['Access-Control-Allow-Credentials'] = 'true'
        
        return response
    
    # Handle OPTIONS preflight requests
    @app.before_request
    def handle_options():
        from flask import request
        if request.method == 'OPTIONS':
            response = app.make_default_options_response()
            return apply_cors_headers(response)
    
    print("✅ CORS headers middleware enabled")
    print(f"   Allowed origins: {', '.join(allowed_origins)}")


def remove_sensitive_headers(app: Flask, headers_to_remove: list = None):
    """
    Remove sensitive headers from responses
    
    Args:
        app: Flask application instance
        headers_to_remove: List of header names to remove
    
    Usage:
        app = Flask(__name__)
        remove_sensitive_headers(app)
    """
    headers_to_remove = headers_to_remove or [
        'X-Powered-By',
        'X-AspNet-Version',
        'X-AspNetMvc-Version',
        'Server'  # Will be replaced by custom Server header
    ]
    
    @app.after_request
    def remove_headers(response):
        for header in headers_to_remove:
            # Don't remove if it's our custom Server header
            if header == 'Server' and response.headers.get(header) == 'GCP-Stimulator':
                continue
            response.headers.pop(header, None)
        return response
    
    print(f"✅ Sensitive headers removal enabled")
    print(f"   Removing: {', '.join(headers_to_remove)}")


# Example comprehensive security setup
def configure_security(app: Flask, 
                      enable_https: bool = False,
                      custom_security_headers: Dict[str, str] = None,
                      cors_origins: list = None):
    """
    Configure all security middleware for the application
    
    Args:
        app: Flask application instance
        enable_https: Whether HTTPS is enabled
        custom_security_headers: Custom security headers
        cors_origins: List of allowed CORS origins
    
    Usage:
        app = Flask(__name__)
        configure_security(
            app,
            enable_https=True,
            cors_origins=['http://localhost:3000', 'https://app.example.com']
        )
    """
    # Set HTTPS config
    app.config['HTTPS_ENABLED'] = enable_https
    
    # Add security headers
    add_security_headers(app, custom_headers=custom_security_headers)
    
    # Add CORS if origins specified
    if cors_origins:
        add_cors_headers(app, allowed_origins=cors_origins)
    
    # Remove sensitive headers
    remove_sensitive_headers(app)
    
    print("🔒 Security configuration complete!")


if __name__ == '__main__':
    # Test security headers
    from flask import Flask
    
    app = Flask(__name__)
    configure_security(app, cors_origins=['*'])
    
    @app.route('/test')
    def test():
        return {'message': 'Security headers test'}
    
    print("\n🧪 Testing security headers...")
    print("   Run app and check response headers with:")
    print("   curl -I http://localhost:8080/test")
