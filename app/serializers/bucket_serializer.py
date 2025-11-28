"""
Bucket serializer - Format bucket responses
"""
import time
from app.logging import log_formatter_stage


def serialize_bucket(bucket) -> dict:
    """Serialize bucket to API response"""
    start_time = time.time()
    
    log_formatter_stage(
        message="Single bucket serialization starting",
        details={
            "operation": "serialize_single",
            "bucket_name": getattr(bucket, 'name', 'unknown'),
            "has_to_dict": hasattr(bucket, 'to_dict')
        }
    )
    
    result = bucket.to_dict() if hasattr(bucket, 'to_dict') else bucket
    
    duration_ms = (time.time() - start_time) * 1000
    log_formatter_stage(
        message="Single bucket serialization completed",
        duration_ms=duration_ms,
        details={
            "operation": "serialize_single",
            "fields_serialized": len(result) if isinstance(result, dict) else 1,
            "gcs_compliant": isinstance(result, dict) and "name" in result
        }
    )
    
    return result


def serialize_buckets(buckets: list) -> dict:
    """Serialize bucket list to API response"""
    start_time = time.time()
    
    log_formatter_stage(
        message="Bucket list serialization starting",
        details={
            "operation": "serialize_list",
            "bucket_count": len(buckets),
            "target_format": "storage#buckets"
        }
    )
    
    items = [serialize_bucket(b) for b in buckets]
    result = {
        "kind": "storage#buckets",
        "items": items
    }
    
    duration_ms = (time.time() - start_time) * 1000
    log_formatter_stage(
        message="Bucket list serialization completed",
        duration_ms=duration_ms,
        details={
            "operation": "serialize_list",
            "buckets_processed": len(buckets),
            "total_fields": sum(len(item) if isinstance(item, dict) else 1 for item in items),
            "gcs_api_format": "storage#buckets"
        }
    )
    
    return result
