"""
Artifact Registry image storage layer.

Manages Docker images, tags, and related metadata in memory.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import logging
import json
from collections import defaultdict

from .models import (
    DockerImage, ImageTag, ImageMetadata, 
    compute_digest, generate_image_id,
    ImageState
)

logger = logging.getLogger(__name__)


class ArtifactImageStorage:
    """In-memory storage for Docker images and tags."""

    def __init__(self):
        # Structure: {project: {location: {repository: {digest: DockerImage}}}}
        self.images: Dict[str, Dict[str, Dict[str, Dict[str, DockerImage]]]] = defaultdict(
            lambda: defaultdict(lambda: defaultdict(dict))
        )
        
        # Structure: {project: {location: {repository: {tag: ImageTag}}}}
        self.tags: Dict[str, Dict[str, Dict[str, Dict[str, ImageTag]]]] = defaultdict(
            lambda: defaultdict(lambda: defaultdict(dict))
        )
        
        # Image metadata: {digest: ImageMetadata}
        self.metadata: Dict[str, ImageMetadata] = {}

    # ========================================================================
    # IMAGE OPERATIONS
    # ========================================================================

    def create_image(
        self,
        project_id: str,
        location: str,
        repository_id: str,
        image_digest: str,
        size_bytes: int,
        config: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> DockerImage:
        """Create/upload a new image."""
        
        # Check if image already exists
        if self._get_image_internal(project_id, location, repository_id, image_digest):
            raise ValueError(f"Image {image_digest} already exists in repository")
        
        # Create image object
        image = DockerImage(
            repository_id=repository_id,
            project_id=project_id,
            location=location,
            digest=image_digest,
            image_id=generate_image_id(image_digest),
            size_bytes=size_bytes,
            config=config or {},
            **kwargs
        )
        
        # Store image
        self.images[project_id][location][repository_id][image_digest] = image
        
        logger.info(f"Created image {image_digest} in {project_id}/{location}/{repository_id}")
        return image

    def get_image(
        self,
        project_id: str,
        location: str,
        repository_id: str,
        image_digest: str
    ) -> Optional[DockerImage]:
        """Get image by digest."""
        return self._get_image_internal(project_id, location, repository_id, image_digest)

    def _get_image_internal(
        self,
        project_id: str,
        location: str,
        repository_id: str,
        image_digest: str
    ) -> Optional[DockerImage]:
        """Internal get image."""
        return self.images[project_id][location][repository_id].get(image_digest)

    def list_images(
        self,
        project_id: str,
        location: str,
        repository_id: str
    ) -> List[DockerImage]:
        """List all images in a repository."""
        return list(self.images[project_id][location][repository_id].values())

    def delete_image(
        self,
        project_id: str,
        location: str,
        repository_id: str,
        image_digest: str
    ) -> bool:
        """Delete an image."""
        if image_digest not in self.images[project_id][location][repository_id]:
            return False
        
        # Delete image
        del self.images[project_id][location][repository_id][image_digest]
        
        # Delete associated tags
        for tag_name in list(self.tags[project_id][location][repository_id].keys()):
            tag = self.tags[project_id][location][repository_id][tag_name]
            if tag.image_digest == image_digest:
                del self.tags[project_id][location][repository_id][tag_name]
        
        # Delete metadata
        self.metadata.pop(image_digest, None)
        
        logger.info(f"Deleted image {image_digest}")
        return True

    # ========================================================================
    # TAG OPERATIONS
    # ========================================================================

    def create_tag(
        self,
        project_id: str,
        location: str,
        repository_id: str,
        tag_name: str,
        image_digest: str
    ) -> ImageTag:
        """Create or update a tag."""
        
        # Verify image exists
        if not self._get_image_internal(project_id, location, repository_id, image_digest):
            raise ValueError(f"Image {image_digest} not found")
        
        # Create tag (overwrites if exists)
        tag = ImageTag(
            repository_id=repository_id,
            project_id=project_id,
            location=location,
            tag=tag_name,
            image_digest=image_digest,
            created_time=datetime.now(timezone.utc),
            update_time=datetime.now(timezone.utc)
        )
        
        self.tags[project_id][location][repository_id][tag_name] = tag
        
        logger.info(f"Created tag {tag_name} -> {image_digest}")
        return tag

    def get_tag(
        self,
        project_id: str,
        location: str,
        repository_id: str,
        tag_name: str
    ) -> Optional[ImageTag]:
        """Get a tag."""
        return self.tags[project_id][location][repository_id].get(tag_name)

    def list_tags(
        self,
        project_id: str,
        location: str,
        repository_id: str,
        image_digest: Optional[str] = None
    ) -> List[ImageTag]:
        """List tags, optionally filtered by image digest."""
        tags = self.tags[project_id][location][repository_id].values()
        
        if image_digest:
            tags = [t for t in tags if t.image_digest == image_digest]
        
        return list(tags)

    def delete_tag(
        self,
        project_id: str,
        location: str,
        repository_id: str,
        tag_name: str
    ) -> bool:
        """Delete a tag."""
        if tag_name not in self.tags[project_id][location][repository_id]:
            return False
        
        del self.tags[project_id][location][repository_id][tag_name]
        logger.info(f"Deleted tag {tag_name}")
        return True

    # ========================================================================
    # METADATA OPERATIONS
    # ========================================================================

    def set_image_metadata(
        self,
        image_digest: str,
        metadata: ImageMetadata
    ) -> ImageMetadata:
        """Set metadata for an image."""
        self.metadata[image_digest] = metadata
        return metadata

    def get_image_metadata(self, image_digest: str) -> Optional[ImageMetadata]:
        """Get metadata for an image."""
        return self.metadata.get(image_digest)

    # ========================================================================
    # PUSH/PULL OPERATIONS
    # ========================================================================

    def push_image(
        self,
        project_id: str,
        location: str,
        repository_id: str,
        image_digest: str,
        config: Dict[str, Any],
        tags: List[str]
    ) -> Dict[str, Any]:
        """
        Push (upload) an image.
        
        Simulates the Docker push operation:
        1. Create image entry
        2. Apply tags
        3. Update metadata
        """
        
        # Create/update image
        size_bytes = len(json.dumps(config).encode())  # Approximate
        image = self.create_image(
            project_id, location, repository_id,
            image_digest, size_bytes,
            config=config
        )
        
        # Apply tags
        tag_bindings = {}
        for tag_name in tags:
            tag = self.create_tag(
                project_id, location, repository_id,
                tag_name, image_digest
            )
            tag_bindings[tag_name] = image_digest
        
        logger.info(f"Pushed image {image_digest} with tags {tags}")
        
        return {
            'image': image.to_dict(),
            'tags': tag_bindings
        }

    def pull_image(
        self,
        project_id: str,
        location: str,
        repository_id: str,
        image_reference: str  # Can be digest or tag
    ) -> Optional[DockerImage]:
        """
        Pull (download) an image.
        
        Simulates the Docker pull operation:
        1. Resolve reference (tag or digest)
        2. Return image metadata
        """
        
        # Try as digest first
        image = self._get_image_internal(
            project_id, location, repository_id,
            image_reference
        )
        if image:
            logger.info(f"Pulled image {image_reference} (digest)")
            return image
        
        # Try as tag
        tag = self.tags[project_id][location][repository_id].get(image_reference)
        if tag:
            image = self._get_image_internal(
                project_id, location, repository_id,
                tag.image_digest
            )
            if image:
                logger.info(f"Pulled image {image_reference} (tag)")
                return image
        
        return None

    # ========================================================================
    # STATISTICS
    # ========================================================================

    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        total_images = 0
        total_tags = 0
        total_size = 0
        
        # Iterate through all images: {project: {location: {repository: {digest: image}}}}
        for project, locations in self.images.items():
            for location, repositories in locations.items():
                for repo_id, images_dict in repositories.items():
                    total_images += len(images_dict)
                    for digest, img in images_dict.items():
                        total_size += img.size_bytes
        
        # Iterate through all tags: {project: {location: {repository: {tag: tag_obj}}}}
        for project, locations in self.tags.items():
            for location, repositories in locations.items():
                for repo_id, tags_dict in repositories.items():
                    total_tags += len(tags_dict)
        
        return {
            'total_images': total_images,
            'total_tags': total_tags,
            'total_size_bytes': total_size,
            'metadata_entries': len(self.metadata),
        }

    def clear(self):
        """Clear all storage."""
        self.images.clear()
        self.tags.clear()
        self.metadata.clear()
        logger.info("Cleared all image storage")


# Global storage instance
storage = ArtifactImageStorage()
