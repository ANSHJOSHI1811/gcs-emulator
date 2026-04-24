"""
Artifact Registry service module.

Provides Docker image and tag management for container images.
"""

from .router import router
from .storage import storage as image_storage
from .models import (
    DockerImage,
    ImageTag,
    ImageMetadata,
    ImageLayer,
    PushRequest,
    PullRequest,
    CreateImageRequest,
    ImageOperationResponse,
    compute_digest,
    generate_image_id,
    ImageMediaType,
    ImageState,
)
from .storage import ArtifactImageStorage

__all__ = [
    "router",
    "image_storage",
    "DockerImage",
    "ImageTag",
    "ImageMetadata",
    "ImageLayer",
    "PushRequest",
    "PullRequest",
    "CreateImageRequest",
    "ImageOperationResponse",
    "compute_digest",
    "generate_image_id",
    "ImageMediaType",
    "ImageState",
    "ArtifactImageStorage",
]
