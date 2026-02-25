"""
Artifact Registry data models for Docker images and tags.

Represents Docker images, tags, and metadata for Artifact Registry repositories.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional, Dict, List, Any
import hashlib

# ============================================================================
# ENUMS
# ============================================================================

class ImageMediaType:
    """Docker image media types."""
    MANIFEST_V2 = "application/vnd.docker.distribution.manifest.v2+json"
    MANIFEST_LIST = "application/vnd.docker.distribution.manifest.list.v2+json"
    CONFIG = "application/vnd.docker.container.image.v1+json"
    LAYER = "application/vnd.docker.image.rootfs.diff.tar.gzip"


class ImageState:
    """Image lifecycle states."""
    READY = "READY"
    DELETING = "DELETING"
    FAILED = "FAILED"


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class ImageLayer:
    """Represents a Docker image layer."""
    digest: str                      # SHA256 digest
    media_type: str                  # e.g., application/vnd.docker.image.rootfs.diff.tar.gzip
    size_bytes: int                  # Layer size in bytes
    urls: List[str] = field(default_factory=list)  # Where to download layer

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DockerImage:
    """Represents a Docker image with metadata."""
    repository_id: str               # Repository name
    project_id: str                  # GCP project
    location: str                    # Regional location
    digest: str                      # Image SHA256 digest (config)
    image_id: str                    # Short ID for reference
    size_bytes: int                  # Total image size
    media_type: str = ImageMediaType.MANIFEST_V2
    layers: List[ImageLayer] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)  # Docker config JSON
    created_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    uploaded_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    state: str = ImageState.READY
    update_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['created_time'] = self.created_time.isoformat() + 'Z'
        data['uploaded_time'] = self.uploaded_time.isoformat() + 'Z'
        data['update_time'] = self.update_time.isoformat() + 'Z'
        data['layers'] = [l.to_dict() if hasattr(l, 'to_dict') else l for l in self.layers]
        return data


@dataclass
class ImageTag:
    """Represents a Docker image tag."""
    repository_id: str               # Repository name
    project_id: str                  # GCP project
    location: str                    # Regional location
    tag: str                          # Tag name (e.g., "latest", "v1.0")
    image_digest: str                # Digest of tagged image
    created_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    update_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def name(self) -> str:
        """Full image name with tag."""
        return f"{self.repository_id}:{self.tag}"

    @property
    def full_name(self) -> str:
        """Full GCP path with tag."""
        return f"{self.location}-docker.pkg.dev/{self.project_id}/{self.repository_id}:{self.tag}"

    def to_dict(self) -> Dict[str, Any]:
        data = {
            'name': self.full_name,
            'digest': self.image_digest,
            'publishTime': self.created_time.isoformat() + 'Z',
            'updateTime': self.update_time.isoformat() + 'Z',
        }
        return data


@dataclass
class PushRequest:
    """Request to push an image."""
    image_digest: str                # Image SHA256 digest
    config_digest: str               # Config blob digest
    repository_id: str               # Repository name
    tags: List[str] = field(default_factory=list)  # Tags to apply
    config_media_type: str = ImageMediaType.CONFIG
    config_data: Dict[str, Any] = field(default_factory=dict)  # Docker config
    tag_bindings: Dict[str, str] = field(default_factory=dict)  # tag -> digest


@dataclass  
class PullRequest:
    """Request to pull an image."""
    image_reference: str             # Image ref or digest
    repository_id: str               # Repository name


@dataclass
class ImageMetadata:
    """Extended metadata for an image."""
    image_digest: str
    repository_id: str
    project_id: str
    location: str
    
    # Build info
    build_time: Optional[datetime] = None
    build_id: Optional[str] = None
    
    # Source info
    source_image: Optional[str] = None
    source_digest: Optional[str] = None
    
    # Labels/annotations
    labels: Dict[str, str] = field(default_factory=dict)
    
    # Vulnerability scanning
    is_scanned: bool = False
    scan_time: Optional[datetime] = None
    vulnerability_counts: Dict[str, int] = field(default_factory=dict)  # severity -> count

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if self.build_time:
            data['build_time'] = self.build_time.isoformat() + 'Z'
        if self.scan_time:
            data['scan_time'] = self.scan_time.isoformat() + 'Z'
        return data


# ============================================================================
# API REQUEST/RESPONSE MODELS
# ============================================================================

@dataclass
class CreateImageRequest:
    """Create/upload an image."""
    image_digest: Optional[str] = None  # Computed if not provided
    config: Optional[Dict[str, Any]] = None
    tags: List[str] = field(default_factory=list)
    media_type: str = ImageMediaType.MANIFEST_V2


@dataclass
class ImportImageRequest:
    """Import an image from another source."""
    source_uri: str                  # GCS path or Docker Hub ref
    destination_repository: str      # Target repository
    tags: List[str] = field(default_factory=list)


@dataclass
class ImageOperationResponse:
    """Response for image operations."""
    name: str                         # Full image name
    digest: str                       # Image digest
    media_type: str                   # Media type
    size_bytes: int                   # Image size
    upload_time: str                  # ISO timestamp
    tags: Dict[str, str] = field(default_factory=dict)  # tag -> create_time


def compute_digest(content: bytes) -> str:
    """Compute SHA256 digest for image content."""
    return "sha256:" + hashlib.sha256(content).hexdigest()


def generate_image_id(digest: str) -> str:
    """Generate short image ID from digest."""
    if digest.startswith("sha256:"):
        return digest[7:19]  # First 12 hex chars
    return digest[:12]
