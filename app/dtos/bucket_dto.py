"""
Bucket DTOs - Data Transfer Objects for bucket operations

Defines the data structures used to transfer bucket data between layers:
- CreateBucketRequestDTO: Input from HTTP request
- BucketResponseDTO: Output to HTTP response (GCS-compliant JSON)
"""
from typing import Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class CreateBucketRequestDTO:
    """
    Request DTO for bucket creation
    Owner: Handler Layer
    Purpose: Represents validated HTTP request data
    """
    project_id: str
    name: str
    location: str = "US"
    storage_class: str = "STANDARD"
    versioning_enabled: bool = False
    labels: Optional[Dict[str, str]] = field(default_factory=dict)
    
    def validate(self) -> None:
        """
        Validate DTO fields
        Raises ValueError if validation fails
        """
        if not self.project_id:
            raise ValueError("project_id is required")
        if not self.name:
            raise ValueError("name is required")
        if len(self.name) < 3 or len(self.name) > 63:
            raise ValueError("Bucket name must be 3-63 characters")
        if self.storage_class not in ["STANDARD", "NEARLINE", "COLDLINE", "ARCHIVE"]:
            raise ValueError(f"Invalid storage class: {self.storage_class}")


@dataclass
class GetBucketRequestDTO:
    """
    Request DTO for bucket retrieval
    Owner: Handler Layer
    """
    bucket_name: str
    projection: Optional[str] = "full"
    
    def validate(self) -> None:
        """Validate DTO fields"""
        if not self.bucket_name:
            raise ValueError("bucket_name is required")


@dataclass
class DeleteBucketRequestDTO:
    """
    Request DTO for bucket deletion
    Owner: Handler Layer
    """
    bucket_name: str
    if_metageneration_match: Optional[int] = None
    
    def validate(self) -> None:
        """Validate DTO fields"""
        if not self.bucket_name:
            raise ValueError("bucket_name is required")


@dataclass
class ListBucketsRequestDTO:
    """
    Request DTO for listing buckets
    Owner: Handler Layer
    """
    project_id: str
    max_results: Optional[int] = None
    page_token: Optional[str] = None
    
    def validate(self) -> None:
        """Validate DTO fields"""
        if not self.project_id:
            raise ValueError("project_id is required")


class BucketResponseDTO:
    """
    Response DTO for bucket operations
    Owner: Response Formatter Layer (Serializer)
    Purpose: Represents bucket in GCS API v1 JSON format
    
    Note: This is a static class with transformation methods.
    Actual response is a plain dict matching GCS spec.
    """
    
    @staticmethod
    def from_model(bucket_model) -> Dict[str, Any]:
        """
        Transform bucket model to GCS-compliant response
        
        Args:
            bucket_model: Bucket domain/DB model instance
            
        Returns:
            Dict in GCS API v1 format
        """
        return {
            "kind": "storage#bucket",
            "id": bucket_model.id,
            "name": bucket_model.name,
            "projectNumber": bucket_model.project_id,
            "location": bucket_model.location,
            "storageClass": bucket_model.storage_class,
            "timeCreated": bucket_model.created_at.isoformat() + "Z",
            "updated": bucket_model.updated_at.isoformat() + "Z",
            "versioning": {
                "enabled": bucket_model.versioning_enabled
            } if hasattr(bucket_model, 'versioning_enabled') else None,
            "labels": bucket_model.meta.get('labels', {}) if hasattr(bucket_model, 'meta') and bucket_model.meta else {}
        }
    
    @staticmethod
    def from_model_list(bucket_models) -> Dict[str, Any]:
        """
        Transform list of bucket models to GCS-compliant list response
        
        Args:
            bucket_models: List of Bucket model instances
            
        Returns:
            Dict in GCS API v1 list format
        """
        return {
            "kind": "storage#buckets",
            "items": [BucketResponseDTO.from_model(b) for b in bucket_models]
        }
