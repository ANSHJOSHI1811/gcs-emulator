"""
Proxy configuration for routing requests between local emulator and real GCP API.
"""
import os
from enum import Enum
from typing import Dict, Set, Optional


class ProxyMode(Enum):
    """Proxy operation modes."""
    LOCAL_ONLY = "local"  # All requests handled locally (current behavior)
    PROXY = "proxy"  # Intercept and route to local or GCP
    PASSTHROUGH = "passthrough"  # Forward all to GCP


class ProxyConfig:
    """Configuration for GCP API proxy."""
    
    def __init__(self):
        # Proxy mode
        self.mode = ProxyMode(os.getenv('GCP_PROXY_MODE', 'local'))
        
        # GCP project for upstream calls
        self.gcp_project_id = os.getenv('GCP_PROJECT_ID')
        
        # GCP credentials path for real API calls
        self.gcp_credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        
        # APIs to handle locally (when in PROXY mode)
        self.local_apis: Set[str] = self._parse_local_apis()
        
        # Resource patterns to handle locally (regex patterns)
        self.local_patterns: Set[str] = self._parse_local_patterns()
        
        # Request timeout for upstream calls
        self.upstream_timeout = int(os.getenv('GCP_UPSTREAM_TIMEOUT', '30'))
        
        # Enable request/response logging
        self.log_requests = os.getenv('GCP_PROXY_LOG_REQUESTS', 'true').lower() == 'true'
        
        # Cache upstream responses
        self.cache_upstream = os.getenv('GCP_PROXY_CACHE', 'false').lower() == 'true'
        
    def _parse_local_apis(self) -> Set[str]:
        """Parse which APIs to handle locally."""
        local_apis_str = os.getenv('GCP_LOCAL_APIS', 'storage,iam')
        return set(api.strip() for api in local_apis_str.split(',') if api.strip())
    
    def _parse_local_patterns(self) -> Set[str]:
        """Parse resource patterns to handle locally."""
        patterns_str = os.getenv('GCP_LOCAL_PATTERNS', '')
        return set(p.strip() for p in patterns_str.split(',') if p.strip())
    
    def should_handle_locally(self, api: str, resource_path: str) -> bool:
        """
        Determine if a request should be handled locally.
        
        Args:
            api: API name (storage, iam, compute, etc.)
            resource_path: Resource path from URL
            
        Returns:
            True if should handle locally, False to forward to GCP
        """
        if self.mode == ProxyMode.LOCAL_ONLY:
            return True
        
        if self.mode == ProxyMode.PASSTHROUGH:
            return False
        
        # PROXY mode - check configuration
        if api in self.local_apis:
            return True
        
        # Check patterns
        import re
        for pattern in self.local_patterns:
            if re.search(pattern, resource_path):
                return True
        
        return False
    
    def validate(self) -> Dict[str, Optional[str]]:
        """
        Validate proxy configuration.
        
        Returns:
            Dict of validation errors (empty if valid)
        """
        errors = {}
        
        if self.mode in [ProxyMode.PROXY, ProxyMode.PASSTHROUGH]:
            if not self.gcp_project_id:
                errors['gcp_project_id'] = 'GCP_PROJECT_ID required for proxy/passthrough mode'
            
            if not self.gcp_credentials_path:
                errors['gcp_credentials_path'] = 'GOOGLE_APPLICATION_CREDENTIALS required for proxy/passthrough mode'
            
            # Check if credentials file exists
            if self.gcp_credentials_path and not os.path.exists(self.gcp_credentials_path):
                errors['gcp_credentials_file'] = f'Credentials file not found: {self.gcp_credentials_path}'
        
        return errors


# Global config instance
proxy_config = ProxyConfig()
