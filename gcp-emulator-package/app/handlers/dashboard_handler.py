"""
Dashboard Handler - Aggregated statistics endpoint

Provides efficient server-side aggregation for dashboard metrics.
"""
from flask import Blueprint, jsonify
from sqlalchemy import func
from app.factory import db
from app.models.bucket import Bucket
from app.models.object import Object

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@dashboard_bp.route("/stats", methods=["GET"])
def get_dashboard_stats():
    """
    Get aggregated dashboard statistics
    
    GET /dashboard/stats
    
    Returns:
        {
            "totalBuckets": 10,
            "totalObjects": 150,
            "totalStorageBytes": 1048576
        }
    """
    try:
        # Count total buckets
        total_buckets = db.session.query(func.count(Bucket.id)).scalar() or 0
        
        # Count total objects and sum their sizes
        stats = db.session.query(
            func.count(Object.id).label('count'),
            func.coalesce(func.sum(Object.size), 0).label('total_size')
        ).first()
        
        total_objects = stats.count or 0
        total_storage_bytes = int(stats.total_size or 0)
        
        return jsonify({
            "totalBuckets": total_buckets,
            "totalObjects": total_objects,
            "totalStorageBytes": total_storage_bytes
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": "Failed to fetch dashboard stats",
            "message": str(e)
        }), 500
