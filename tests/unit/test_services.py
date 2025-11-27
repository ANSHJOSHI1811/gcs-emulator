"""Unit tests for service layer."""
import uuid

import pytest

from app.factory import db
from app.models.object import Object
from app.services.bucket_service import BucketService


@pytest.mark.unit
def test_create_bucket_success(app):
    """BucketService.create_bucket stores bucket with expected attributes."""
    unique_name = f"unit-bucket-{uuid.uuid4().hex[:8]}"
    with app.app_context():
        bucket = BucketService.create_bucket(
            project_id="unit-project",
            name=unique_name,
            location="EU",
            storage_class="NEARLINE",
        )

        assert bucket.name == unique_name
        assert bucket.project_id == "unit-project"
        assert bucket.location == "EU"
        assert bucket.storage_class == "NEARLINE"


@pytest.mark.unit
def test_create_bucket_duplicate_raises(app):
    """Creating a bucket with an existing name raises ValueError."""
    bucket_name = f"dup-bucket-{uuid.uuid4().hex[:8]}"
    with app.app_context():
        BucketService.create_bucket("dup-project", bucket_name)

        with pytest.raises(ValueError) as error:
            BucketService.create_bucket("dup-project", bucket_name)

        assert "already exists" in str(error.value)


@pytest.mark.unit
def test_list_buckets_scoped_by_project(app):
    """Buckets are listed only for the requested project."""
    projects = {"project-a": [], "project-b": []}
    with app.app_context():
        for project_id in projects:
            for _ in range(2):
                bucket = BucketService.create_bucket(
                    project_id=project_id,
                    name=f"{project_id}-{uuid.uuid4().hex[:6]}",
                )
                projects[project_id].append(bucket.name)

        project_a_buckets = BucketService.list_buckets("project-a")
        retrieved_names = {bucket.name for bucket in project_a_buckets}

        assert retrieved_names == set(projects["project-a"])


@pytest.mark.unit
def test_get_bucket_not_found_returns_none(app):
    """BucketService.get_bucket returns None when name is unknown."""
    with app.app_context():
        result = BucketService.get_bucket("missing-bucket")
        assert result is None


@pytest.mark.unit
def test_delete_bucket_requires_empty_bucket(app):
    """Deleting a non-empty bucket raises ValueError before removal."""
    bucket_name = f"nonempty-{uuid.uuid4().hex[:8]}"
    with app.app_context():
        bucket = BucketService.create_bucket("delete-project", bucket_name)
        # Create object tied to bucket to make it non-empty.
        obj = Object(
            id=f"obj-{uuid.uuid4().hex[:8]}",
            bucket_id=bucket.id,
            name="file.txt",
            size=42,
        )
        db.session.add(obj)
        db.session.commit()

        with pytest.raises(ValueError) as error:
            BucketService.delete_bucket(bucket_name)

        assert "not empty" in str(error.value)


@pytest.mark.unit
def test_delete_bucket_success(app):
    """Deleting an empty bucket removes it from the database."""
    bucket_name = f"empty-delete-{uuid.uuid4().hex[:8]}"
    with app.app_context():
        BucketService.create_bucket("clean-project", bucket_name)

        BucketService.delete_bucket(bucket_name)
        assert BucketService.get_bucket(bucket_name) is None
