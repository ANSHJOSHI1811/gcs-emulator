"""
Events Handler - Phase 4

Endpoints for retrieving object events.
"""
from flask import Blueprint, jsonify, request
from app.services.object_event_service import ObjectEventService
from app.utils.gcs_errors import internal_error

events_bp = Blueprint("events", __name__, url_prefix="/internal/events")


@events_bp.route("", methods=["GET"])
def list_events():
    """
    List object events
    
    GET /internal/events
    GET /internal/events?bucket=my-bucket
    """
    try:
        bucket_name = request.args.get("bucket")
        events = ObjectEventService.get_events(bucket_name=bucket_name)
        
        return jsonify({
            "kind": "storage#objectEvents",
            "items": [event.to_dict() for event in events]
        }), 200
        
    except Exception as e:
        return internal_error(f"Failed to retrieve events: {str(e)}")


@events_bp.route("/<event_id>/delivered", methods=["PATCH"])
def mark_event_delivered(event_id):
    """
    Mark an event as delivered
    
    PATCH /internal/events/{eventId}/delivered
    """
    try:
        event = ObjectEventService.mark_delivered(event_id)
        if not event:
            return jsonify({"error": {"message": "Event not found"}}), 404
        
        return jsonify(event.to_dict()), 200
        
    except Exception as e:
        return internal_error(f"Failed to mark event as delivered: {str(e)}")
