"""
Bucket serializer - Format bucket responses
"""


def serialize_bucket(bucket) -> dict:
    """Serialize bucket to API response"""
    return bucket.to_dict() if hasattr(bucket, 'to_dict') else bucket


def serialize_buckets(buckets: list) -> dict:
    """Serialize bucket list to API response"""
    return {
        "kind": "storage#buckets",
        "items": [serialize_bucket(b) for b in buckets]
    }
