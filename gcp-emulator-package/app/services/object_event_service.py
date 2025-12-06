"""
Object Event Service - Phase 4

Local event notification system for object changes.
"""
import uuid
import json
from datetime import datetime
from app.factory import db
from app.models.object_event import ObjectEvent


class EventType:
    """Event type constants"""
    OBJECT_FINALIZE = "OBJECT_FINALIZE"
    OBJECT_DELETE = "OBJECT_DELETE"
    OBJECT_METADATA_UPDATE = "OBJECT_METADATA_UPDATE"


class ObjectEventService:
    """Service for logging and retrieving object events"""
    
    @staticmethod
    def log_event(
        bucket_name: str,
        object_name: str,
        event_type: str,
        generation: int = None,
        metadata: dict = None
    ):
        """
        Log an object change event
        
        Args:
            bucket_name: Bucket name
            object_name: Object name
            event_type: One of OBJECT_FINALIZE, OBJECT_DELETE, OBJECT_METADATA_UPDATE
            generation: Object generation (optional)
            metadata: Additional metadata (optional)
        """
        event = ObjectEvent(
            event_id=str(uuid.uuid4()),
            bucket_name=bucket_name,
            object_name=object_name,
            event_type=event_type,
            generation=generation,
            timestamp=datetime.utcnow(),
            metadata_json=json.dumps(metadata) if metadata else None,
            delivered=False
        )
        
        db.session.add(event)
        db.session.commit()
        
        return event
    
    @staticmethod
    def get_events(bucket_name: str = None, delivered: bool = None, limit: int = 100):
        """
        Get events with optional filtering
        
        Args:
            bucket_name: Filter by bucket name (optional)
            delivered: Filter by delivered status (optional)
            limit: Maximum number of events to return
            
        Returns:
            List of ObjectEvent instances
        """
        query = ObjectEvent.query.order_by(ObjectEvent.timestamp.desc())
        
        if bucket_name:
            query = query.filter_by(bucket_name=bucket_name)
        
        if delivered is not None:
            query = query.filter_by(delivered=delivered)
        
        return query.limit(limit).all()
    
    @staticmethod
    def mark_delivered(event_id: str):
        """Mark an event as delivered"""
        event = ObjectEvent.query.filter_by(event_id=event_id).first()
        if event:
            event.delivered = True
            db.session.commit()
        return event
    
    @staticmethod
    def clear_old_events(days: int = 7):
        """Delete events older than specified days"""
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(days=days)
        ObjectEvent.query.filter(ObjectEvent.timestamp < cutoff).delete()
        db.session.commit()
