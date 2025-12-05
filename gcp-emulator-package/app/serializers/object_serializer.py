"""
Object serializer - Format object responses
"""


def serialize_object(obj) -> dict:
    """Serialize object to API response"""
    return obj.to_dict() if hasattr(obj, 'to_dict') else obj


def serialize_objects(objects: list) -> dict:
    """Serialize object list to API response"""
    return {
        "kind": "storage#objects",
        "items": [serialize_object(o) for o in objects]
    }
