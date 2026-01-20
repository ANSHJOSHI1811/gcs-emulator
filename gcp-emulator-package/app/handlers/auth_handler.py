"""
Auth handler - OAuth2 mock endpoint for gcloud CLI compatibility
"""
import json
import secrets
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from app.factory import db
from app.models.service_account import ServiceAccount

auth_bp = Blueprint("auth", __name__)


# In-memory token store (for emulator simplicity)
TOKENS = {}


@auth_bp.route("/token", methods=["POST"])
def oauth_token():
    """
    Mock OAuth2 token endpoint
    Accepts service account JWT or authorization code and returns access token
    """
    grant_type = request.form.get("grant_type")
    
    if grant_type == "urn:ietf:params:oauth:grant-type:jwt-bearer":
        # Service account authentication
        assertion = request.form.get("assertion")
        
        if not assertion:
            return jsonify({"error": "invalid_grant"}), 400
        
        # In real GCP, this would validate JWT signature
        # For emulator, we just generate a token
        access_token = f"ya29.{secrets.token_urlsafe(64)}"
        refresh_token = f"1//{secrets.token_urlsafe(64)}"
        
        # Store token with metadata
        TOKENS[access_token] = {
            "type": "service_account",
            "grant_type": grant_type,
            "created_at": datetime.utcnow(),
            "expires_in": 3600,
        }
        
        return jsonify({
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": 3600,
            "refresh_token": refresh_token,
        })
    
    elif grant_type == "authorization_code":
        # User authentication flow
        code = request.form.get("code")
        
        if not code:
            return jsonify({"error": "invalid_grant"}), 400
        
        access_token = f"ya29.{secrets.token_urlsafe(64)}"
        refresh_token = f"1//{secrets.token_urlsafe(64)}"
        
        TOKENS[access_token] = {
            "type": "user",
            "grant_type": grant_type,
            "created_at": datetime.utcnow(),
            "expires_in": 3600,
        }
        
        return jsonify({
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": 3600,
            "refresh_token": refresh_token,
            "id_token": f"eyJhbGciOiJSUzI1NiIsImtpZCI6ImVtdWxhdG9yIn0.{secrets.token_urlsafe(128)}.{secrets.token_urlsafe(64)}",
        })
    
    elif grant_type == "refresh_token":
        # Refresh token flow
        refresh_token = request.form.get("refresh_token")
        
        if not refresh_token:
            return jsonify({"error": "invalid_grant"}), 400
        
        access_token = f"ya29.{secrets.token_urlsafe(64)}"
        
        TOKENS[access_token] = {
            "type": "refreshed",
            "grant_type": grant_type,
            "created_at": datetime.utcnow(),
            "expires_in": 3600,
        }
        
        return jsonify({
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": 3600,
        })
    
    return jsonify({"error": "unsupported_grant_type"}), 400


@auth_bp.route("/token/revoke", methods=["POST"])
def revoke_token():
    """Revoke an access or refresh token"""
    token = request.form.get("token")
    
    if token and token in TOKENS:
        del TOKENS[token]
    
    return "", 200


@auth_bp.route("/o/oauth2/v2/auth", methods=["GET"])
def oauth_authorize():
    """
    Mock OAuth2 authorization endpoint
    For emulator, automatically approve and redirect
    """
    client_id = request.args.get("client_id")
    redirect_uri = request.args.get("redirect_uri")
    scope = request.args.get("scope")
    state = request.args.get("state")
    
    # Generate mock authorization code
    code = f"4/{secrets.token_urlsafe(64)}"
    
    # Build redirect URL
    redirect_params = {
        "code": code,
        "scope": scope or "openid email profile",
    }
    
    if state:
        redirect_params["state"] = state
    
    from urllib.parse import urlencode
    redirect_url = f"{redirect_uri}?{urlencode(redirect_params)}"
    
    # Return HTML that auto-redirects (simulates user approval)
    html = f"""
    <html>
    <head><title>GCP Emulator - Auth</title></head>
    <body>
        <h2>GCS Emulator - Mock Authentication</h2>
        <p>Authorization approved (emulator mode)</p>
        <p>Redirecting...</p>
        <script>
            setTimeout(function() {{
                window.location.href = "{redirect_url}";
            }}, 1000);
        </script>
    </body>
    </html>
    """
    
    return html, 200


@auth_bp.route("/oauth2/v1/tokeninfo", methods=["GET", "POST"])
def token_info():
    """Token info endpoint - validates and returns token metadata"""
    access_token = request.args.get("access_token") or request.form.get("access_token")
    
    if not access_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            access_token = auth_header[7:]
    
    if not access_token or access_token not in TOKENS:
        return jsonify({"error": "invalid_token"}), 401
    
    token_data = TOKENS[access_token]
    
    return jsonify({
        "issued_to": "emulator-client-id",
        "audience": "emulator-client-id",
        "scope": "https://www.googleapis.com/auth/cloud-platform",
        "expires_in": 3600,
        "access_type": "online",
        "token_type": token_data.get("type", "user"),
    })


@auth_bp.route("/oauth2/v1/userinfo", methods=["GET"])
def user_info():
    """User info endpoint - returns mock user info"""
    auth_header = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "unauthorized"}), 401
    
    access_token = auth_header[7:]
    
    if access_token not in TOKENS:
        return jsonify({"error": "invalid_token"}), 401
    
    return jsonify({
        "id": "emulator-user-001",
        "email": "emulator-user@gcp-emulator.local",
        "verified_email": True,
        "name": "GCP Emulator User",
        "given_name": "Emulator",
        "family_name": "User",
        "picture": "",
    })


def validate_token(token: str) -> dict:
    """
    Validate token and return identity info
    Returns dict with 'type' and 'email' or None if invalid
    """
    if not token or token not in TOKENS:
        # Default: allow all in emulator mode
        return {
            "type": "user",
            "email": "emulator-user@gcp-emulator.local",
            "id": "emulator-user-001",
        }
    
    token_data = TOKENS[token]
    
    return {
        "type": token_data.get("type", "user"),
        "email": "emulator-user@gcp-emulator.local",
        "id": "emulator-user-001",
    }


@auth_bp.route("/oauth2/token", methods=["POST"])
def oauth2_token():
    """
    OAuth2 token endpoint (Terraform-compatible path).
    Alias for /token endpoint.
    """
    return oauth_token()


@auth_bp.route("/oauth2/v2/userinfo", methods=["GET"])
def oauth2_userinfo():
    """
    OAuth2 userinfo endpoint (Terraform-compatible path).
    Alias for /userinfo endpoint.
    """
    return userinfo()
