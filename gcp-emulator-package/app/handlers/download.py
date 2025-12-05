"""
Download handler - SDK-compatible download endpoint

The Google Cloud Storage SDK uses /download/storage/v1/b/{bucket}/o/{object} 
for downloading objects, separate from the metadata endpoint.

Reference: https://cloud.google.com/storage/docs/json_api/v1/objects/get
"""
from flask import Blueprint, request, send_file, jsonify
from io import BytesIO
from app.services.object_versioning_service import ObjectVersioningService

download_bp = Blueprint("download", __name__)


@download_bp.route("/storage/v1/b/<bucket>/o/<path:object_name>", methods=["GET"])
def download_object(bucket, object_name):
    """
    Download object content (SDK-compatible endpoint)
    
    GET /download/storage/v1/b/{bucket}/o/{object}
    GET /download/storage/v1/b/{bucket}/o/{object}?generation=123
    
    The SDK calls this endpoint directly for downloads instead of 
    using ?alt=media on the metadata endpoint.
    
    Query Parameters:
        generation: Download specific version (optional)
        
    Returns:
        Binary file content with appropriate Content-Type
    """
    try:
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
        
        # Add generation header for SDK compatibility
        response.headers['x-goog-generation'] = str(version.generation)
        response.headers['x-goog-metageneration'] = str(version.metageneration)
        
        return response, 200
        
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            return jsonify({"error": {"message": "Resource not found"}}), 404
        return jsonify({"error": {"message": error_msg}}), 400
    except Exception as e:
        return jsonify({
            "error": {
                "code": 500,
                "message": f"Internal server error: {str(e)}"
            }
        }), 500
