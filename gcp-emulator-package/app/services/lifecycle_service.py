"""
Lifecycle Service - Phase 4

Basic lifecycle management (Delete/Archive actions).
"""
import uuid
from datetime import datetime, timedelta
from app.factory import db
from app.models.lifecycle_rule import LifecycleRule
from app.models.bucket import Bucket
from app.models.object import Object, ObjectVersion


class LifecycleAction:
    """Lifecycle action constants"""
    DELETE = "Delete"
    ARCHIVE = "Archive"
    
    @staticmethod
    def is_valid(action: str) -> bool:
        """Check if action is valid"""
        return action in [LifecycleAction.DELETE, LifecycleAction.ARCHIVE]


class LifecycleService:
    """Service for lifecycle rule management and evaluation"""
    
    @staticmethod
    def create_rule(bucket_name: str, action: str, age_days: int) -> LifecycleRule:
        """
        Create lifecycle rule
        
        Args:
            bucket_name: Bucket name
            action: Delete or Archive
            age_days: Age threshold in days
            
        Returns:
            Created LifecycleRule
            
        Raises:
            ValueError: If bucket not found or invalid parameters
        """
        if not LifecycleAction.is_valid(action):
            raise ValueError(f"Invalid action: {action}. Must be 'Delete' or 'Archive'")
        
        if age_days < 0:
            raise ValueError("Age days must be non-negative")
        
        bucket = Bucket.query.filter_by(name=bucket_name).first()
        if not bucket:
            raise ValueError(f"Bucket '{bucket_name}' not found")
        
        rule = LifecycleRule(
            rule_id=str(uuid.uuid4()),
            bucket_name=bucket.id,
            action=action,
            age_days=age_days,
            created_at=datetime.utcnow()
        )
        
        db.session.add(rule)
        db.session.commit()
        
        return rule
    
    @staticmethod
    def list_rules(bucket_name: str = None):
        """
        List lifecycle rules
        
        Args:
            bucket_name: Filter by bucket name (optional)
            
        Returns:
            List of LifecycleRule instances
        """
        if bucket_name:
            bucket = Bucket.query.filter_by(name=bucket_name).first()
            if not bucket:
                raise ValueError(f"Bucket '{bucket_name}' not found")
            return LifecycleRule.query.filter_by(bucket_name=bucket.id).all()
        else:
            return LifecycleRule.query.all()
    
    @staticmethod
    def delete_rule(rule_id: str) -> bool:
        """
        Delete lifecycle rule
        
        Args:
            rule_id: Rule ID
            
        Returns:
            True if deleted
            
        Raises:
            ValueError: If rule not found
        """
        rule = LifecycleRule.query.filter_by(rule_id=rule_id).first()
        if not rule:
            raise ValueError(f"Rule '{rule_id}' not found")
        
        db.session.delete(rule)
        db.session.commit()
        
        return True
    
    @staticmethod
    def evaluate_all_rules():
        """
        Evaluate all lifecycle rules and apply actions
        
        Returns:
            Dictionary with evaluation results
        """
        rules = LifecycleRule.query.all()
        
        results = {
            "rulesEvaluated": len(rules),
            "objectsDeleted": 0,
            "objectsArchived": 0,
            "details": []
        }
        
        for rule in rules:
            rule_result = LifecycleService._evaluate_rule(rule)
            results["objectsDeleted"] += rule_result["deleted"]
            results["objectsArchived"] += rule_result["archived"]
            results["details"].append({
                "ruleId": rule.rule_id,
                "action": rule.action,
                "ageDays": rule.age_days,
                "objectsAffected": rule_result["deleted"] + rule_result["archived"]
            })
        
        return results
    
    @staticmethod
    def _evaluate_rule(rule: LifecycleRule):
        """
        Evaluate single lifecycle rule
        
        Args:
            rule: LifecycleRule instance
            
        Returns:
            Dictionary with counts of affected objects
        """
        cutoff_date = datetime.utcnow() - timedelta(days=rule.age_days)
        
        # Get all objects in the bucket older than cutoff
        objects = Object.query.filter_by(
            bucket_id=rule.bucket_name,
            deleted=False,
            is_latest=True
        ).filter(
            Object.time_created < cutoff_date
        ).all()
        
        deleted_count = 0
        archived_count = 0
        
        for obj in objects:
            if rule.action == LifecycleAction.DELETE:
                # Delete object (marks all versions as deleted)
                versions = ObjectVersion.query.filter_by(
                    bucket_id=obj.bucket_id,
                    name=obj.name,
                    deleted=False
                ).all()
                
                for version in versions:
                    version.deleted = True
                
                obj.deleted = True
                obj.is_latest = False
                deleted_count += 1
                
            elif rule.action == LifecycleAction.ARCHIVE:
                # Change storage class to ARCHIVE
                obj.storage_class = "ARCHIVE"
                
                # Update all versions
                versions = ObjectVersion.query.filter_by(
                    bucket_id=obj.bucket_id,
                    name=obj.name,
                    deleted=False
                ).all()
                
                for version in versions:
                    version.storage_class = "ARCHIVE"
                
                archived_count += 1
        
        db.session.commit()
        
        return {
            "deleted": deleted_count,
            "archived": archived_count
        }
