"""
Operation utilities for GCP operations
"""
from app.models.operation import Operation
from app.factory import db
from datetime import datetime
import secrets


def create_operation(project_id, operation_type, target_link, target_id, region=None, zone=None):
    """
    Create a new GCP operation
    
    Args:
        project_id: GCP project ID
        operation_type: Type of operation (insert, delete, update, etc.)
        target_link: Full link to the target resource
        target_id: ID of the target resource (should be string of integer for gcloud compatibility)
        region: Optional region for regional operations
        zone: Optional zone for zonal operations
    
    Returns:
        Operation: The created operation object
    """
    # Generate operation name
    operation_name = f"operation-{secrets.token_hex(8)}"
    
    # Generate unique integer ID for operation
    operation_id = int(secrets.token_hex(8), 16) % (10**19)
    
    # Create operation
    operation = Operation(
        id=operation_id,
        name=operation_name,
        operation_type=operation_type,
        status='DONE',  # Synchronous operations complete immediately
        progress=100,
        target_link=target_link,
        target_id=target_id,  # This should already be a string of an integer
        project_id=project_id,
        region=region,
        zone=zone,
        insert_time=datetime.utcnow(),
        start_time=datetime.utcnow(),
        end_time=datetime.utcnow()
    )
    
    db.session.add(operation)
    db.session.commit()
    
    return operation
