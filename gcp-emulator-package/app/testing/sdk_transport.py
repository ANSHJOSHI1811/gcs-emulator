"""
Flask Test Client Transport for Google Cloud Storage SDK

This module provides a mock HTTP transport that redirects SDK calls
into a Flask test client, enabling SDK integration tests without
starting a real server or making network connections.
"""
import json
from urllib.parse import urlparse, parse_qs
from typing import Optional, Dict, Any


class MockRequest:
    """Mimics requests.Request for exception handling"""
    
    def __init__(self, method: str, url: str):
        self.method = method
        self.url = url


class MockResponse:
    """
    Mimics requests.Response for SDK compatibility
    Wraps a Flask test response object
    """
    
    def __init__(self, flask_response, method: str = None, url: str = None):
        """
        Args:
            flask_response: werkzeug.test.Response from Flask test client
            method: HTTP method (for request attribute)
            url: Request URL (for request attribute)
        """
        self.flask_response = flask_response
        self.status_code = flask_response.status_code
        self.headers = dict(flask_response.headers)
        self.content = flask_response.data
        # Only decode as text if it's valid UTF-8
        try:
            self.text = flask_response.data.decode('utf-8')
        except UnicodeDecodeError:
            self.text = None
        self.url = url
        self.reason = self._get_reason_phrase()
        self.request = MockRequest(method, url) if method and url else None
        self._content_consumed = False
    
    def json(self):
        """Parse response body as JSON"""
        if not self.content:
            raise ValueError("No JSON content in response")
        if self.text is None:
            raise ValueError("Response is binary, cannot parse as JSON")
        return json.loads(self.text)
    
    def raise_for_status(self):
        """Raise HTTPError for bad status codes (4xx, 5xx)"""
        if 400 <= self.status_code < 600:
            from requests.exceptions import HTTPError
            error_msg = f"{self.status_code} Error: {self.reason} for url: {self.url}"
            raise HTTPError(error_msg, response=self)
    
    def _get_reason_phrase(self):
        """Get HTTP reason phrase from status code"""
        reasons = {
            200: "OK",
            201: "Created",
            204: "No Content",
            400: "Bad Request",
            404: "Not Found",
            409: "Conflict",
            412: "Precondition Failed",
            500: "Internal Server Error"
        }
        return reasons.get(self.status_code, "Unknown")
    
    def iter_content(self, chunk_size=None):
        """Iterate over response content in chunks (for streaming downloads)"""
        if chunk_size is None:
            chunk_size = 8192
        data = self.content
        for i in range(0, len(data), chunk_size):
            yield data[i:i + chunk_size]
    
    def __enter__(self):
        """Support context manager protocol for SDK downloads"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager"""
        return False


class FlaskClientTransport:
    """
    Custom HTTP transport that redirects requests to Flask test client
    Compatible with google.auth.transport.requests.AuthorizedSession
    """
    
    def __init__(self, flask_test_client):
        """
        Args:
            flask_test_client: Flask test client from app.test_client()
        """
        self.client = flask_test_client
    
    def request(
        self,
        method: str,
        url: str,
        data: Optional[bytes] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> MockResponse:
        """
        Intercept HTTP request and route to Flask test client
        
        Args:
            method: HTTP method (GET, POST, DELETE, etc.)
            url: Full URL (scheme and host are stripped)
            data: Request body as bytes
            headers: HTTP headers dict
            **kwargs: Additional request options (json, params, timeout, etc.)
        
        Returns:
            MockResponse wrapping Flask response
        """
        # Parse URL to extract path and query params
        parsed = urlparse(url)
        path = parsed.path
        
        # Extract query parameters from URL
        query_params = parse_qs(parsed.query)
        # Flatten single-item lists (parse_qs returns lists)
        query_params = {k: v[0] if len(v) == 1 else v for k, v in query_params.items()}
        
        # Merge with params kwarg if provided
        if 'params' in kwargs:
            query_params.update(kwargs['params'])
        
        # Prepare request arguments for Flask test client
        request_args = {
            'method': method.upper(),
            'headers': headers or {},
        }
        
        # Handle request body
        if 'json' in kwargs:
            # SDK passed JSON data via kwarg
            request_args['json'] = kwargs['json']
        elif data:
            # Check if data is JSON based on Content-Type
            content_type = (headers or {}).get('Content-Type', '')
            if 'application/json' in content_type:
                try:
                    # Handle both str and bytes
                    if isinstance(data, bytes):
                        request_args['json'] = json.loads(data.decode('utf-8'))
                    else:
                        request_args['json'] = json.loads(data)
                except (ValueError, UnicodeDecodeError):
                    request_args['data'] = data
            else:
                request_args['data'] = data
        
        # Add query string
        if query_params:
            request_args['query_string'] = query_params
        
        # Make request to Flask test client
        flask_response = self.client.open(path, **request_args)
        
        # Wrap and return with request metadata for exception handling
        return MockResponse(flask_response, method=method, url=url)


def create_mock_session(flask_test_client):
    """
    Create a mock session object compatible with AuthorizedSession
    
    Args:
        flask_test_client: Flask test client
        
    Returns:
        Mock session with request() method
    """
    transport = FlaskClientTransport(flask_test_client)
    
    class MockSession:
        """Mock session that routes to Flask test client"""
        
        # Required attributes for google.auth.transport.requests.AuthorizedSession compatibility
        is_mtls = False
        
        def __init__(self):
            self.headers = {}
        
        def request(self, method, url, **kwargs):
            return transport.request(method, url, **kwargs)
        
        def get(self, url, **kwargs):
            return self.request('GET', url, **kwargs)
        
        def post(self, url, **kwargs):
            return self.request('POST', url, **kwargs)
        
        def put(self, url, **kwargs):
            return self.request('PUT', url, **kwargs)
        
        def delete(self, url, **kwargs):
            return self.request('DELETE', url, **kwargs)
        
        def configure_mtls_channel(self, client_cert_source):
            """No-op for mTLS configuration compatibility"""
            pass
        
        def close(self):
            """No-op for compatibility"""
            pass
    
    return MockSession()
