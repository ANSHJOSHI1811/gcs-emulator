"""APIClient for making HTTP requests to GCP Simulator API"""
import requests
import json
import os
from typing import Dict, Any, Optional
from urllib.parse import urljoin


class APIClient:
    """Helper class for making HTTP API requests"""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.getenv("TEST_API_URL", "http://localhost:8080")
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
        self.timeout = int(os.getenv("TEST_TIMEOUT", "30"))
    
    def _build_url(self, path: str) -> str:
        """Build full URL from path"""
        if path.startswith("http"):
            return path
        return urljoin(self.base_url, path.lstrip("/"))
    
    def get(self, path: str, **kwargs) -> requests.Response:
        """GET request"""
        url = self._build_url(path)
        return self.session.get(url, timeout=self.timeout, **kwargs)
    
    def post(self, path: str, data: Dict = None, json_data: Dict = None, **kwargs) -> requests.Response:
        """POST request"""
        url = self._build_url(path)
        if json_data is None and data is not None:
            json_data = data
        return self.session.post(url, json=json_data, timeout=self.timeout, **kwargs)
    
    def patch(self, path: str, data: Dict = None, json_data: Dict = None, **kwargs) -> requests.Response:
        """PATCH request"""
        url = self._build_url(path)
        if json_data is None and data is not None:
            json_data = data
        return self.session.patch(url, json=json_data, timeout=self.timeout, **kwargs)
    
    def put(self, path: str, data: Dict = None, json_data: Dict = None, **kwargs) -> requests.Response:
        """PUT request"""
        url = self._build_url(path)
        if json_data is None and data is not None:
            json_data = data
        return self.session.put(url, json=json_data, timeout=self.timeout, **kwargs)
    
    def delete(self, path: str, **kwargs) -> requests.Response:
        """DELETE request"""
        url = self._build_url(path)
        return self.session.delete(url, timeout=self.timeout, **kwargs)
    
    def wait_for_ready(self, max_attempts: int = 5) -> bool:
        """Wait for API to be ready"""
        import time
        for attempt in range(max_attempts):
            try:
                response = self.session.get(urljoin(self.base_url, "/"), timeout=self.timeout)
                if response.status_code in [200, 404]:
                    return True
            except Exception:
                pass
            
            if attempt < max_attempts - 1:
                time.sleep(2)
        
        return False
    
    def close(self):
        """Close session"""
        self.session.close()
