"""
Operation Handler

Handles operation polling endpoints for GCP API compatibility.
Terraform uses these to check the status of long-running operations.
"""

from flask import jsonify
from app.models.operation import Operation


def get_global_operation(project, operation_name):
    """
    Get global operation details.
    
    GET /compute/v1/projects/{project}/global/operations/{operation}
    """
    operation = Operation.query.filter_by(
        project_id=project,
        name=operation_name,
        zone=None,
        region=None
    ).first()
    
    if not operation:
        return jsonify({
            'error': {
                'code': 404,
                'message': f"Operation '{operation_name}' not found"
            }
        }), 404
    
    return jsonify(operation.to_dict()), 200


def get_regional_operation(project, region, operation_name):
    """
    Get regional operation details.
    
    GET /compute/v1/projects/{project}/regions/{region}/operations/{operation}
    """
    operation = Operation.query.filter_by(
        project_id=project,
        region=region,
        name=operation_name
    ).first()
    
    if not operation:
        return jsonify({
            'error': {
                'code': 404,
                'message': f"Operation '{operation_name}' not found in region '{region}'"
            }
        }), 404
    
    return jsonify(operation.to_dict()), 200


def get_zonal_operation(project, zone, operation_name):
    """
    Get zonal operation details.
    
    GET /compute/v1/projects/{project}/zones/{zone}/operations/{operation}
    """
    operation = Operation.query.filter_by(
        project_id=project,
        zone=zone,
        name=operation_name
    ).first()
    
    if not operation:
        return jsonify({
            'error': {
                'code': 404,
                'message': f"Operation '{operation_name}' not found in zone '{zone}'"
            }
        }), 404
    
    return jsonify(operation.to_dict()), 200


def list_global_operations(project):
    """
    List all global operations.
    
    GET /compute/v1/projects/{project}/global/operations
    """
    operations = Operation.query.filter_by(
        project_id=project,
        zone=None,
        region=None
    ).all()
    
    return jsonify({
        'kind': 'compute#operationList',
        'items': [op.to_dict() for op in operations]
    }), 200


def list_regional_operations(project, region):
    """
    List all regional operations.
    
    GET /compute/v1/projects/{project}/regions/{region}/operations
    """
    operations = Operation.query.filter_by(
        project_id=project,
        region=region
    ).all()
    
    return jsonify({
        'kind': 'compute#operationList',
        'items': [op.to_dict() for op in operations]
    }), 200


def list_zonal_operations(project, zone):
    """
    List all zonal operations.
    
    GET /compute/v1/projects/{project}/zones/{zone}/operations
    """
    operations = Operation.query.filter_by(
        project_id=project,
        zone=zone
    ).all()
    
    return jsonify({
        'kind': 'compute#operationList',
        'items': [op.to_dict() for op in operations]
    }), 200
