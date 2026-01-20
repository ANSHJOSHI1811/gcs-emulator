"""
Operation Utilities

Helper functions for creating and managing operations.
"""

import uuid
from datetime import datetime
from app.factory import db
from app.models.operation import Operation


def create_operation(project_id, operation_type, target_link, target_id=None, 
                    zone=None, region=None, status='DONE'):
    """
    Create a new operation record.
    
    Args:
        project_id (str): Project ID
        operation_type (str): insert, delete, update, patch
        target_link (str): Full URL to the target resource
        target_id (str, optional): ID of the target resource
        zone (str, optional): Zone for zonal operations
        region (str, optional): Region for regional operations
        status (str): Operation status (default: DONE for instant completion)
        
    Returns:
        Operation: The created operation
    """
    operation = Operation(
        id=uuid.uuid4(),
        name=f"operation-{uuid.uuid4().hex[:16]}",
        operation_type=operation_type,
        status=status,
        progress=100 if status == 'DONE' else 0,
        target_link=target_link,
        target_id=target_id,
        project_id=project_id,
        zone=zone,
        region=region,
        insert_time=datetime.utcnow(),
        start_time=datetime.utcnow(),
        end_time=datetime.utcnow() if status == 'DONE' else None
    )
    
    db.session.add(operation)
    db.session.commit()
    
    return operation


def operation_response(operation):
    """
    Create a standard operation response dict.
    
    Args:
        operation (Operation): The operation object
        
    Returns:
        dict: GCP-compatible operation response
    """
    return operation.to_dict()
