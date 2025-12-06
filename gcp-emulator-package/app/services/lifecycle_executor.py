"""
Lifecycle Rules Execution Engine
Background service that applies lifecycle rules to objects
"""
import json
import time
import threading
from datetime import datetime, timedelta
from app.factory import db
from app.models.bucket import Bucket
from app.models.object import Object
from app.logging import log_service_stage


class LifecycleExecutor:
    """Background executor for lifecycle rules"""
    
    def __init__(self, app, interval_minutes=5):
        """
        Initialize lifecycle executor
        
        Args:
            app: Flask application instance
            interval_minutes: How often to run lifecycle checks (default: 5 minutes)
        """
        self.app = app
        self.interval_minutes = interval_minutes
        self.running = False
        self.thread = None
    
    def start(self):
        """Start the background lifecycle executor thread"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        
        log_service_stage(
            message="Lifecycle executor started",
            details={
                "interval_minutes": self.interval_minutes
            }
        )
    
    def stop(self):
        """Stop the background executor"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        
        log_service_stage(
            message="Lifecycle executor stopped",
            details={}
        )
    
    def _run_loop(self):
        """Background thread loop"""
        while self.running:
            try:
                with self.app.app_context():
                    self.execute_lifecycle_rules()
            except Exception as e:
                log_service_stage(
                    message=f"Lifecycle execution error: {str(e)}",
                    details={"error": str(e)}
                )
            
            # Sleep for the configured interval
            time.sleep(self.interval_minutes * 60)
    
    def execute_lifecycle_rules(self):
        """
        Execute lifecycle rules across all buckets
        This is the main entry point for rule evaluation
        """
        log_service_stage(
            message="Starting lifecycle rules execution",
            details={}
        )
        
        # Get all buckets with lifecycle rules
        buckets_with_rules = Bucket.query.filter(
            Bucket.lifecycle_config.isnot(None)
        ).all()
        
        total_actions = 0
        
        for bucket in buckets_with_rules:
            try:
                actions_taken = self._apply_lifecycle_rules_to_bucket(bucket)
                total_actions += actions_taken
            except Exception as e:
                log_service_stage(
                    message=f"Error processing lifecycle rules for bucket {bucket.name}",
                    details={"bucket": bucket.name, "error": str(e)}
                )
        
        log_service_stage(
            message="Lifecycle rules execution completed",
            details={
                "buckets_processed": len(buckets_with_rules),
                "total_actions": total_actions
            }
        )
        
        return total_actions
    
    def _apply_lifecycle_rules_to_bucket(self, bucket):
        """
        Apply lifecycle rules to a specific bucket
        
        Args:
            bucket: Bucket model instance
            
        Returns:
            Number of actions taken
        """
        # Parse lifecycle configuration
        try:
            lifecycle_config = json.loads(bucket.lifecycle_config)
        except (json.JSONDecodeError, TypeError):
            return 0
        
        if not isinstance(lifecycle_config, list):
            return 0
        
        actions_taken = 0
        
        # Get all objects in bucket
        objects = Object.query.filter_by(bucket_id=bucket.id).all()
        
        for rule in lifecycle_config:
            action = rule.get("action")
            age_days = rule.get("ageDays")
            
            if not action or age_days is None:
                continue
            
            # Calculate cutoff date
            cutoff_date = datetime.utcnow() - timedelta(days=age_days)
            
            for obj in objects:
                if obj.created_at < cutoff_date:
                    if action == "Delete":
                        actions_taken += self._delete_object(bucket, obj)
                    elif action == "Archive":
                        actions_taken += self._archive_object(bucket, obj)
        
        return actions_taken
    
    def _delete_object(self, bucket, obj):
        """
        Delete an object as part of lifecycle rule
        
        Args:
            bucket: Bucket model instance
            obj: Object model instance
            
        Returns:
            1 if deleted, 0 if already deleted or error
        """
        try:
            # Check if already deleted
            if hasattr(obj, 'deleted') and obj.deleted:
                return 0
            
            log_service_stage(
                message="Lifecycle rule: Deleting object",
                details={
                    "bucket": bucket.name,
                    "object": obj.name,
                    "age_days": (datetime.utcnow() - obj.created_at).days
                }
            )
            
            # Delete physical file
            from pathlib import Path
            file_path = Path(obj.file_path)
            if file_path.exists():
                file_path.unlink()
            
            # Delete database record
            db.session.delete(obj)
            db.session.commit()
            
            return 1
        except Exception as e:
            log_service_stage(
                message=f"Failed to delete object: {str(e)}",
                details={
                    "bucket": bucket.name,
                    "object": obj.name,
                    "error": str(e)
                }
            )
            db.session.rollback()
            return 0
    
    def _archive_object(self, bucket, obj):
        """
        Move object to ARCHIVE storage class
        
        Args:
            bucket: Bucket model instance
            obj: Object model instance
            
        Returns:
            1 if archived, 0 if already archived or error
        """
        try:
            # Check if already archived
            if obj.storage_class == "ARCHIVE":
                return 0
            
            log_service_stage(
                message="Lifecycle rule: Archiving object",
                details={
                    "bucket": bucket.name,
                    "object": obj.name,
                    "age_days": (datetime.utcnow() - obj.created_at).days,
                    "old_class": obj.storage_class
                }
            )
            
            # Update storage class
            obj.storage_class = "ARCHIVE"
            db.session.commit()
            
            return 1
        except Exception as e:
            log_service_stage(
                message=f"Failed to archive object: {str(e)}",
                details={
                    "bucket": bucket.name,
                    "object": obj.name,
                    "error": str(e)
                }
            )
            db.session.rollback()
            return 0


# Global executor instance
_executor = None


def start_lifecycle_executor(app, interval_minutes=5):
    """
    Start the global lifecycle executor
    
    Args:
        app: Flask application instance
        interval_minutes: How often to run lifecycle checks
    """
    global _executor
    if _executor is None:
        _executor = LifecycleExecutor(app, interval_minutes)
        _executor.start()
    return _executor


def stop_lifecycle_executor():
    """Stop the global lifecycle executor"""
    global _executor
    if _executor:
        _executor.stop()
        _executor = None


def get_lifecycle_executor():
    """Get the global executor instance"""
    return _executor
