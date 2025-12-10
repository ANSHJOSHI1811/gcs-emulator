"""
Upstream GCP API client for forwarding requests to real Google Cloud.
"""
import os
import logging
from typing import Dict, Any, Optional, Tuple
from google.auth import default
from google.auth.transport.requests import AuthorizedSession
from google.oauth2 import service_account
import json

from .config import proxy_config

logger = logging.getLogger(__name__)


class UpstreamGCPClient:
    """Client for making authenticated requests to real GCP APIs."""
    
    def __init__(self):
        self._session: Optional[AuthorizedSession] = None
        self._credentials = None
        self._base_urls = {
            'storage': 'https://storage.googleapis.com',
            'iam': 'https://iam.googleapis.com',
            'compute': 'https://compute.googleapis.com',
            'cloudresourcemanager': 'https://cloudresourcemanager.googleapis.com'
        }
    
    def _get_session(self) -> AuthorizedSession:
        """Get or create authenticated session."""
        if self._session is None:
            self._initialize_credentials()
        return self._session
    
    def _initialize_credentials(self):
        """Initialize GCP credentials for upstream calls."""
        try:
            if proxy_config.gcp_credentials_path:
                # Load from service account file
                self._credentials = service_account.Credentials.from_service_account_file(
                    proxy_config.gcp_credentials_path,
                    scopes=['https://www.googleapis.com/auth/cloud-platform']
                )
                logger.info(f"Loaded credentials from {proxy_config.gcp_credentials_path}")
            else:
                # Use application default credentials
                self._credentials, project = default(
                    scopes=['https://www.googleapis.com/auth/cloud-platform']
                )
                logger.info(f"Using default credentials for project {project}")
            
            self._session = AuthorizedSession(self._credentials)
            
        except Exception as e:
            logger.error(f"Failed to initialize GCP credentials: {e}")
            raise
    
    def forward_request(
        self, 
        method: str, 
        api: str, 
        path: str,
        headers: Dict[str, str],
        query_params: Dict[str, str],
        body: Optional[bytes] = None
    ) -> Tuple[int, Dict[str, str], bytes]:
        """
        Forward a request to real GCP API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            api: API name (storage, iam, compute)
            path: Request path
            headers: Request headers
            query_params: Query parameters
            body: Request body (for POST/PUT/PATCH)
            
        Returns:
            Tuple of (status_code, response_headers, response_body)
        """
        session = self._get_session()
        
        # Build full URL
        base_url = self._base_urls.get(api, f'https://{api}.googleapis.com')
        url = f"{base_url}{path}"
        
        # Add query parameters
        if query_params:
            from urllib.parse import urlencode
            url = f"{url}?{urlencode(query_params)}"
        
        # Log request
        if proxy_config.log_requests:
            logger.info(f"Forwarding {method} {url}")
            if body:
                logger.debug(f"Request body: {body[:500]}")  # Log first 500 bytes
        
        try:
            # Make request
            response = session.request(
                method=method,
                url=url,
                headers=headers,
                data=body,
                timeout=proxy_config.upstream_timeout
            )
            
            # Log response
            if proxy_config.log_requests:
                logger.info(f"Response: {response.status_code}")
                logger.debug(f"Response body: {response.content[:500]}")
            
            return (
                response.status_code,
                dict(response.headers),
                response.content
            )
            
        except Exception as e:
            logger.error(f"Error forwarding request to GCP: {e}")
            # Return error response
            error_body = json.dumps({
                'error': {
                    'code': 502,
                    'message': f'Error forwarding to GCP: {str(e)}',
                    'status': 'BAD_GATEWAY'
                }
            }).encode('utf-8')
            return (502, {'Content-Type': 'application/json'}, error_body)
    
    def health_check(self) -> bool:
        """
        Check if we can authenticate with GCP.
        
        Returns:
            True if credentials are valid
        """
        try:
            session = self._get_session()
            # Try a simple API call
            response = session.get(
                f'https://cloudresourcemanager.googleapis.com/v1/projects/{proxy_config.gcp_project_id}',
                timeout=5
            )
            return response.status_code in [200, 403]  # 403 means auth works but no permission
        except Exception as e:
            logger.error(f"GCP health check failed: {e}")
            return False


# Global upstream client instance
upstream_client = UpstreamGCPClient()
