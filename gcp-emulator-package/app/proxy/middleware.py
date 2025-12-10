"""
Flask middleware for proxying GCP API requests.
"""
import logging
from flask import Flask, Request, Response
from werkzeug.exceptions import HTTPException

from .config import proxy_config, ProxyMode
from .upstream import upstream_client

logger = logging.getLogger(__name__)


class ProxyMiddleware:
    """
    Middleware that intercepts requests and routes them to local handlers or upstream GCP.
    """
    
    def __init__(self, app: Flask):
        self.app = app
        self.wsgi_app = app.wsgi_app
        
    def __call__(self, environ, start_response):
        """WSGI application interface."""
        # Parse request
        request = Request(environ)
        
        # Determine API and resource path
        api, resource_path = self._parse_request_path(request.path)
        
        # Decide: local or upstream?
        if proxy_config.should_handle_locally(api, resource_path):
            # Handle locally - pass to Flask app
            if proxy_config.log_requests:
                logger.info(f"[LOCAL] {request.method} {request.path}")
            return self.wsgi_app(environ, start_response)
        else:
            # Forward to GCP
            if proxy_config.log_requests:
                logger.info(f"[UPSTREAM] {request.method} {request.path}")
            return self._forward_to_gcp(request, environ, start_response)
    
    def _parse_request_path(self, path: str) -> tuple:
        """
        Parse API and resource path from request.
        
        Args:
            path: Request path like /storage/v1/b/bucket-name
            
        Returns:
            (api_name, resource_path)
        """
        parts = path.lstrip('/').split('/')
        
        if len(parts) >= 1:
            # First part is typically the API
            api = parts[0]
            
            # Special cases
            if api == 'v1' and len(parts) >= 2:
                # IAM uses /v1/projects/... format
                api = 'iam'
            elif api == 'storage':
                api = 'storage'
            elif api == 'compute':
                api = 'compute'
            
            return api, path
        
        return 'unknown', path
    
    def _forward_to_gcp(self, request: Request, environ, start_response):
        """Forward request to upstream GCP API."""
        try:
            # Extract request details
            method = request.method
            api, resource_path = self._parse_request_path(request.path)
            headers = dict(request.headers)
            query_params = dict(request.args)
            body = request.get_data() if request.method in ['POST', 'PUT', 'PATCH'] else None
            
            # Remove hop-by-hop headers
            headers.pop('Host', None)
            headers.pop('Connection', None)
            
            # Forward to GCP
            status_code, response_headers, response_body = upstream_client.forward_request(
                method=method,
                api=api,
                path=resource_path,
                headers=headers,
                query_params=query_params,
                body=body
            )
            
            # Build response
            status_line = f'{status_code} {self._get_status_text(status_code)}'
            response_headers_list = [(k, v) for k, v in response_headers.items()]
            
            start_response(status_line, response_headers_list)
            return [response_body]
            
        except Exception as e:
            logger.error(f"Error in proxy middleware: {e}", exc_info=True)
            # Return error response
            error_response = Response(
                response=f'{{"error": {{"message": "Proxy error: {str(e)}"}}}}',
                status=502,
                mimetype='application/json'
            )
            return error_response(environ, start_response)
    
    def _get_status_text(self, status_code: int) -> str:
        """Get status text for status code."""
        status_texts = {
            200: 'OK',
            201: 'Created',
            204: 'No Content',
            400: 'Bad Request',
            401: 'Unauthorized',
            403: 'Forbidden',
            404: 'Not Found',
            409: 'Conflict',
            500: 'Internal Server Error',
            502: 'Bad Gateway',
            503: 'Service Unavailable'
        }
        return status_texts.get(status_code, 'Unknown')


def add_proxy_middleware(app: Flask):
    """Add proxy middleware to Flask app."""
    if proxy_config.mode != ProxyMode.LOCAL_ONLY:
        logger.info(f"Enabling proxy mode: {proxy_config.mode.value}")
        
        # Validate configuration
        errors = proxy_config.validate()
        if errors:
            logger.error(f"Proxy configuration errors: {errors}")
            raise ValueError(f"Invalid proxy configuration: {errors}")
        
        # Add middleware
        app.wsgi_app = ProxyMiddleware(app)
        
        # Test upstream connection
        if upstream_client.health_check():
            logger.info("✓ Upstream GCP connection verified")
        else:
            logger.warning("⚠ Could not verify upstream GCP connection")
    else:
        logger.info("Running in LOCAL_ONLY mode (no proxy)")
