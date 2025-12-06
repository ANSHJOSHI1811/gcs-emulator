"""
ACL Service - Phase 4

Minimal ACL simulation (private/publicRead only).
NOT full GCS IAM or POSIX ACLs.
"""
from app.factory import db
from app.models.bucket import Bucket
from app.models.object import Object


class ACLValue:
    """ACL value constants"""
    PRIVATE = "private"
    PUBLIC_READ = "publicRead"
    
    @staticmethod
    def is_valid(acl: str) -> bool:
        """Check if ACL value is valid"""
        return acl in [ACLValue.PRIVATE, ACLValue.PUBLIC_READ]


class ACLService:
    """Service for minimal ACL management"""
    
    @staticmethod
    def set_bucket_acl(bucket_name: str, acl: str) -> Bucket:
        """
        Set bucket ACL
        
        Args:
            bucket_name: Bucket name
            acl: ACL value (private or publicRead)
            
        Returns:
            Updated Bucket
            
        Raises:
            ValueError: If bucket not found or ACL invalid
        """
        if not ACLValue.is_valid(acl):
            raise ValueError(f"Invalid ACL value: {acl}. Must be 'private' or 'publicRead'")
        
        bucket = Bucket.query.filter_by(name=bucket_name).first()
        if not bucket:
            raise ValueError(f"Bucket '{bucket_name}' not found")
        
        bucket.acl = acl
        db.session.commit()
        
        return bucket
    
    @staticmethod
    def get_bucket_acl(bucket_name: str) -> str:
        """
        Get bucket ACL
        
        Args:
            bucket_name: Bucket name
            
        Returns:
            ACL value
            
        Raises:
            ValueError: If bucket not found
        """
        bucket = Bucket.query.filter_by(name=bucket_name).first()
        if not bucket:
            raise ValueError(f"Bucket '{bucket_name}' not found")
        
        return bucket.acl or ACLValue.PRIVATE
    
    @staticmethod
    def set_object_acl(bucket_name: str, object_name: str, acl: str) -> Object:
        """
        Set object ACL
        
        Args:
            bucket_name: Bucket name
            object_name: Object name
            acl: ACL value (private or publicRead)
            
        Returns:
            Updated Object
            
        Raises:
            ValueError: If object not found or ACL invalid
        """
        if not ACLValue.is_valid(acl):
            raise ValueError(f"Invalid ACL value: {acl}. Must be 'private' or 'publicRead'")
        
        bucket = Bucket.query.filter_by(name=bucket_name).first()
        if not bucket:
            raise ValueError(f"Bucket '{bucket_name}' not found")
        
        obj = Object.query.filter_by(
            bucket_id=bucket.id,
            name=object_name,
            is_latest=True,
            deleted=False
        ).first()
        
        if not obj:
            raise ValueError(f"Object '{object_name}' not found in bucket '{bucket_name}'")
        
        obj.acl = acl
        db.session.commit()
        
        return obj
    
    @staticmethod
    def get_object_acl(bucket_name: str, object_name: str) -> str:
        """
        Get object ACL
        
        Args:
            bucket_name: Bucket name
            object_name: Object name
            
        Returns:
            ACL value
            
        Raises:
            ValueError: If object not found
        """
        bucket = Bucket.query.filter_by(name=bucket_name).first()
        if not bucket:
            raise ValueError(f"Bucket '{bucket_name}' not found")
        
        obj = Object.query.filter_by(
            bucket_id=bucket.id,
            name=object_name,
            is_latest=True,
            deleted=False
        ).first()
        
        if not obj:
            raise ValueError(f"Object '{object_name}' not found in bucket '{bucket_name}'")
        
        return obj.acl or ACLValue.PRIVATE
    
    @staticmethod
    def is_public_read(bucket_name: str, object_name: str = None) -> bool:
        """
        Check if bucket or object allows public read
        
        Args:
            bucket_name: Bucket name
            object_name: Object name (optional, checks bucket if None)
            
        Returns:
            True if publicRead is allowed
        """
        bucket = Bucket.query.filter_by(name=bucket_name).first()
        if not bucket:
            return False
        
        if object_name:
            # Check object ACL first
            obj = Object.query.filter_by(
                bucket_id=bucket.id,
                name=object_name,
                is_latest=True,
                deleted=False
            ).first()
            
            if obj and obj.acl:
                return obj.acl == ACLValue.PUBLIC_READ
            
            # Fall back to bucket ACL
            return bucket.acl == ACLValue.PUBLIC_READ
        else:
            # Check bucket ACL
            return bucket.acl == ACLValue.PUBLIC_READ
