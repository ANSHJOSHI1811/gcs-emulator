"""
Signed URL utility - Generate and verify signed URLs

Uses HMAC-SHA256 for signing.
Minimal implementation without IAM/service accounts.
"""
import hmac
import hashlib
import base64
import time
from urllib.parse import urlencode, parse_qs
from typing import Dict, Tuple
import os


class SignedURLService:
    """Service for generating and verifying signed URLs"""
    
    # Shared secret key for HMAC signing
    SECRET_KEY = os.getenv("SIGNED_URL_SECRET", "gcs-emulator-secret-key-change-in-production")
    
    ALGORITHM = "GOOG4-HMAC-SHA256"
    
    @staticmethod
    def generate_signed_url(
        method: str,
        bucket: str,
        object_name: str,
        expires_in: int = 3600
    ) -> str:
        """
        Generate a signed URL for GET or PUT operations
        
        Args:
            method: HTTP method (GET or PUT)
            bucket: Bucket name
            object_name: Object name
            expires_in: Expiration time in seconds (default 1 hour)
            
        Returns:
            Signed URL string
        """
        # Calculate expiry timestamp
        current_time = int(time.time())
        expiry = current_time + expires_in
        
        # Construct path
        path = f"/signed/{bucket}/{object_name}"
        
        # String to sign: method + "\n" + path + "\n" + expiry
        string_to_sign = f"{method}\n{path}\n{expiry}"
        
        # Compute HMAC-SHA256
        signature = hmac.new(
            SignedURLService.SECRET_KEY.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            hashlib.sha256
        ).digest()
        
        # Base64 URL-safe encoding
        signature_b64 = base64.urlsafe_b64encode(signature).decode('utf-8').rstrip('=')
        
        # Construct query parameters (include both expires_in AND expiry timestamp)
        query_params = {
            'X-Goog-Algorithm': SignedURLService.ALGORITHM,
            'X-Goog-Expires': str(expires_in),
            'X-Goog-Timestamp': str(expiry),  # Include absolute expiry
            'X-Goog-Signature': signature_b64
        }
        
        # Build full URL
        base_url = os.getenv("STORAGE_EMULATOR_HOST", "http://localhost:8080")
        signed_url = f"{base_url}{path}?{urlencode(query_params)}"
        
        return signed_url
    
    @staticmethod
    def verify_signed_url(
        method: str,
        path: str,
        query_params: Dict[str, str]
    ) -> Tuple[bool, str]:
        """
        Verify a signed URL
        
        Args:
            method: HTTP method
            path: Request path
            query_params: Query parameters dict
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Extract required parameters
        algorithm = query_params.get('X-Goog-Algorithm')
        expires_in_str = query_params.get('X-Goog-Expires')
        provided_signature = query_params.get('X-Goog-Signature')
        
        if not all([algorithm, expires_in_str, provided_signature]):
            return False, "Missing required signature parameters"
        
        # Validate algorithm
        if algorithm != SignedURLService.ALGORITHM:
            return False, f"Unsupported algorithm: {algorithm}"
        
        # Calculate expiry timestamp
        try:
            expires_in = int(expires_in_str)
        except ValueError:
            return False, "Invalid expiry value"
        
        # Check if expired
        # We need to extract the original expiry timestamp from the signature
        # Since we signed with absolute expiry, we need to recalculate
        current_time = int(time.time())
        
        # Try to verify signature - we'll compute expiry from current time
        # In a real implementation, you'd include timestamp in the URL
        # For simplicity, we reconstruct the expiry timestamp
        
        # Attempt verification with a range of possible expiry times
        # This is simplified - in production, include timestamp in URL
        for test_expiry in range(current_time, current_time + expires_in + 1):
            string_to_sign = f"{method}\n{path}\n{test_expiry}"
            
            computed_signature = hmac.new(
                SignedURLService.SECRET_KEY.encode('utf-8'),
                string_to_sign.encode('utf-8'),
                hashlib.sha256
            ).digest()
            
            computed_signature_b64 = base64.urlsafe_b64encode(computed_signature).decode('utf-8').rstrip('=')
            
            if hmac.compare_digest(provided_signature, computed_signature_b64):
                # Check if expired
                if test_expiry < current_time:
                    return False, "Signed URL has expired"
                return True, ""
        
        return False, "Invalid signature"
    
    @staticmethod
    def verify_signed_url_v2(
        method: str,
        path: str,
        query_params: Dict[str, str],
        request_time: int
    ) -> Tuple[bool, str]:
        """
        Simplified verification that includes request timestamp
        
        Args:
            method: HTTP method
            path: Request path
            query_params: Query parameters dict
            request_time: Time when URL was generated (from X-Goog-Date if present)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Extract parameters
        algorithm = query_params.get('X-Goog-Algorithm')
        expires_in_str = query_params.get('X-Goog-Expires')
        provided_signature = query_params.get('X-Goog-Signature')
        
        if not all([algorithm, expires_in_str, provided_signature]):
            return False, "Missing required signature parameters"
        
        if algorithm != SignedURLService.ALGORITHM:
            return False, f"Unsupported algorithm: {algorithm}"
        
        try:
            expires_in = int(expires_in_str)
        except ValueError:
            return False, "Invalid expiry value"
        
        # Calculate expiry timestamp
        expiry = request_time + expires_in
        current_time = int(time.time())
        
        # Check if expired
        if expiry < current_time:
            return False, "Signed URL has expired"
        
        # Recompute signature
        string_to_sign = f"{method}\n{path}\n{expiry}"
        
        computed_signature = hmac.new(
            SignedURLService.SECRET_KEY.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            hashlib.sha256
        ).digest()
        
        computed_signature_b64 = base64.urlsafe_b64encode(computed_signature).decode('utf-8').rstrip('=')
        
        # Compare signatures
        if not hmac.compare_digest(provided_signature, computed_signature_b64):
            return False, "Invalid signature"
        
        return True, ""
