"""
Signed URL handler - GET and PUT operations with signed URLs (Phase 3)

Endpoints:
    GET /signed/{bucket}/{object} - Download with signed URL
    PUT /signed/{bucket}/{object} - Upload with signed URL
"""
from flask import Blueprint, request, send_file, jsonify
from io import BytesIO
from app.services.object_versioning_service import ObjectVersioningService
from app.utils.signer import SignedURLService
from app.utils.gcs_errors import (
    not_found_error,
    invalid_argument_error,
    internal_error
)

signed_bp = Blueprint("signed", __name__)


@signed_bp.route("/signed/<bucket>/<path:object_name>", methods=["GET"])
def signed_download(bucket, object_name):
    """
    Download object using signed URL (Phase 3)
    
    GET /signed/{bucket}/{object}?X-Goog-Algorithm=...&X-Goog-Timestamp=...&X-Goog-Signature=...
    
    Query Parameters:
        X-Goog-Algorithm: GOOG4-HMAC-SHA256
        X-Goog-Expires: Expiration duration in seconds
        X-Goog-Timestamp: Absolute expiry timestamp
        X-Goog-Signature: HMAC signature
        
    Returns:
        Binary file content if signature valid
        Error response if signature invalid or expired
    """
    try:
        # Extract query parameters
        query_params = request.args.to_dict()
        
        # Get expiry timestamp
        expiry_str = query_params.get('X-Goog-Timestamp')
        if not expiry_str:
            return invalid_argument_error("Missing X-Goog-Timestamp parameter")
        
        try:
            expiry = int(expiry_str)
        except ValueError:
            return invalid_argument_error("Invalid X-Goog-Timestamp value")
        
        # Check if expired
        import time
        if time.time() > expiry:
            return invalid_argument_error("Signed URL has expired")
        
        # Verify signature
        path = f"/signed/{bucket}/{object_name}"
        string_to_sign = f"GET\n{path}\n{expiry}"
        
        from app.utils.signer import SignedURLService
        import hmac
        import hashlib
        import base64
        
        expected_signature = hmac.new(
            SignedURLService.SECRET_KEY.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            hashlib.sha256
        ).digest()
        expected_b64 = base64.urlsafe_b64encode(expected_signature).decode('utf-8').rstrip('=')
        
        provided_signature = query_params.get('X-Goog-Signature', '')
        
        if provided_signature != expected_b64:
            return invalid_argument_error("Invalid signature")
        
        # Download object
        generation = request.args.get("generation", type=int)
        content, version = ObjectVersioningService.download_object_version(
            bucket, object_name, generation
        )
        
        response = send_file(
            BytesIO(content),
            mimetype=version.content_type,
            as_attachment=True,
            download_name=object_name
        )
        
        return response, 200
        
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            if "bucket" in error_msg.lower():
                return not_found_error(bucket, "bucket")
            else:
                return not_found_error(object_name, "object")
        return invalid_argument_error(error_msg)
    except Exception as e:
        return internal_error(f"Internal server error: {str(e)}")


@signed_bp.route("/signed/<bucket>/<path:object_name>", methods=["PUT"])
def signed_upload(bucket, object_name):
    """
    Upload object using signed URL (Phase 3)
    
    PUT /signed/{bucket}/{object}?X-Goog-Algorithm=...&X-Goog-Timestamp=...&X-Goog-Signature=...
    
    Query Parameters:
        X-Goog-Algorithm: GOOG4-HMAC-SHA256
        X-Goog-Expires: Expiration duration in seconds
        X-Goog-Timestamp: Absolute expiry timestamp
        X-Goog-Signature: HMAC signature
        
    Request Body:
        Binary file content
        
    Returns:
        Object metadata if upload successful
        Error response if signature invalid or expired
    """
    try:
        # Extract query parameters
        query_params = request.args.to_dict()
        
        # Get expiry timestamp
        expiry_str = query_params.get('X-Goog-Timestamp')
        if not expiry_str:
            return invalid_argument_error("Missing X-Goog-Timestamp parameter")
        
        try:
            expiry = int(expiry_str)
        except ValueError:
            return invalid_argument_error("Invalid X-Goog-Timestamp value")
        
        # Check if expired
        import time
        if time.time() > expiry:
            return invalid_argument_error("Signed URL has expired")
        
        # Verify signature
        path = f"/signed/{bucket}/{object_name}"
        string_to_sign = f"PUT\n{path}\n{expiry}"
        
        from app.utils.signer import SignedURLService
        import hmac
        import hashlib
        import base64
        
        expected_signature = hmac.new(
            SignedURLService.SECRET_KEY.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            hashlib.sha256
        ).digest()
        expected_b64 = base64.urlsafe_b64encode(expected_signature).decode('utf-8').rstrip('=')
        
        provided_signature = query_params.get('X-Goog-Signature', '')
        
        if provided_signature != expected_b64:
            return invalid_argument_error("Invalid signature")
        
        # Get file content
        content = request.get_data()
        if not content:
            return invalid_argument_error("Empty file content")
        
        content_type = request.headers.get("Content-Type", "application/octet-stream")
        
        # Upload object
        obj = ObjectVersioningService.upload_object_with_versioning(
            bucket_name=bucket,
            object_name=object_name,
            content=content,
            content_type=content_type
        )
        
        return jsonify(obj.to_dict()), 200
        
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            if "bucket" in error_msg.lower():
                return not_found_error(bucket, "bucket")
            else:
                return not_found_error(object_name, "object")
        return invalid_argument_error(error_msg)
    except Exception as e:
        return internal_error(f"Internal server error: {str(e)}")
