"""
GCP Compute Engine API v1 Handler
Translates SDK requests to internal ComputeService calls
"""
from flask import jsonify, request
from datetime import datetime
import logging
import uuid
import re

from app.models.instance import Instance
from app.models.compute_operation import ComputeOperation
from app.factory import db

logger = logging.getLogger(__name__)


def gcp_error_response(code, message, errors=None):
    """
    Create GCP-compliant error response
    Matches official Compute Engine API error format
    """
    error_body = {
        "error": {
            "code": code,
            "message": message,
            "errors": errors or [{"message": message, "domain": "global", "reason": _map_code_to_reason(code)}]
        }
    }
    return jsonify(error_body), code


def _map_code_to_reason(code):
    """Map HTTP status code to GCP error reason"""
    reason_map = {
        400: "invalid",
        404: "notFound",
        409: "alreadyExists",
        412: "conditionNotMet",
        500: "backendError",
        503: "backendError"
    }
    return reason_map.get(code, "backendError")


def validate_instance_name(name):
    """
    Validate instance name per GCP rules:
    - 1-63 characters
    - Lowercase letters, numbers, hyphens
    - Must start with lowercase letter
    - Must not end with hyphen
    """
    if not name:
        return False, "Instance name is required"
    
    if len(name) < 1 or len(name) > 63:
        return False, "Instance name must be between 1 and 63 characters"
    
    if not re.match(r'^[a-z]([-a-z0-9]*[a-z0-9])?$', name):
        return False, "Instance name must start with lowercase letter and contain only lowercase letters, numbers, and hyphens"
    
    return True, None


def validate_zone(zone):
    """Validate zone format"""
    if not zone:
        return False, "Zone is required"
    
    # Basic validation: zone should match pattern like us-central1-a
    if not re.match(r'^[a-z]+-[a-z]+\d+-[a-z]$', zone):
        return False, f"Invalid zone format: {zone}"
    
    return True, None


class ComputeV1Handler:
    """
    Handler for GCP Compute Engine API v1 endpoints
    Provides SDK compatibility while using existing ComputeService
    """
    
    def __init__(self, compute_service):
        self.compute_service = compute_service
    
    def _create_operation(self, project, zone, operation_type, target_id=None, target_name=None):
        """
        Create a Long-Running Operation (LRO) object
        For emulator, operations complete immediately (status=DONE)
        """
        operation_id = str(uuid.uuid4())
        operation_name = f"operation-{int(datetime.utcnow().timestamp())}-{operation_id[:8]}"
        
        target_link = None
        if target_name:
            target_link = f"https://www.googleapis.com/compute/v1/projects/{project}/zones/{zone}/instances/{target_name}"
        
        operation = ComputeOperation(
            id=operation_id,
            name=operation_name,
            project_id=project,
            zone=zone,
            target_id=target_id,
            target_link=target_link,
            operation_type=operation_type,
            status='DONE',  # Complete immediately for emulator
            progress=100
        )
        
        db.session.add(operation)
        db.session.commit()
        
        return operation
    
    def insert_instance(self, project, zone):
        """
        POST /compute/v1/projects/{project}/zones/{zone}/instances
        Create (insert) a new instance
        """
        try:
            # Validate zone format
            zone_valid, zone_error = validate_zone(zone)
            if not zone_valid:
                return gcp_error_response(400, zone_error)
            
            # Parse request body
            data = request.get_json()
            if not data:
                return gcp_error_response(400, "Request body is required")
            
            # Validate instance name
            name = data.get('name')
            name_valid, name_error = validate_instance_name(name)
            if not name_valid:
                return gcp_error_response(400, name_error)
            
            # Check for duplicate instance name (409 Conflict)
            existing = Instance.query.filter_by(
                name=name,
                project_id=project,
                zone=zone
            ).first()
            
            if existing:
                return gcp_error_response(
                    409, 
                    f"The resource 'projects/{project}/zones/{zone}/instances/{name}' already exists"
                )
            
            # Extract machine type (e.g., "zones/us-central1-a/machineTypes/e2-micro")
            machine_type_url = data.get('machineType', '')
            machine_type = machine_type_url.split('/')[-1] if machine_type_url else 'e2-micro'
            
            # Map machine type to CPU/memory (simplified)
            machine_specs = {
                'e2-micro': (1, 1024),
                'e2-small': (2, 2048),
                'e2-medium': (2, 4096),
                'n1-standard-1': (1, 3840),
                'n1-standard-2': (2, 7680),
            }
            cpu, memory = machine_specs.get(machine_type, (1, 512))
            
            # Extract source image from disks
            disks = data.get('disks', [])
            image = 'alpine:latest'  # Default
            if disks:
                init_params = disks[0].get('initializeParams', {})
                source_image = init_params.get('sourceImage', '')
                # Map GCP image to Docker image (simplified)
                if 'debian' in source_image.lower():
                    image = 'debian:latest'
                elif 'ubuntu' in source_image.lower():
                    image = 'ubuntu:latest'
                elif 'alpine' in source_image.lower():
                    image = 'alpine:latest'
            
            # Create instance using existing service
            instance = self.compute_service.run_instance(
                name=name,
                image=image,
                cpu=cpu,
                memory=memory,
                project_id=project
            )
            
            if not instance:
                return gcp_error_response(500, "Failed to create instance")
            
            # Update instance with zone and machine_type
            instance.zone = zone
            instance.machine_type = machine_type
            db.session.commit()
            
            # Create operation
            operation = self._create_operation(
                project=project,
                zone=zone,
                operation_type='insert',
                target_id=instance.id,
                target_name=instance.name
            )
            
            # Return operation (SDK waits for this)
            return jsonify(operation.to_gcp_dict()), 200
            
        except Exception as e:
            logger.error(f"Error in insert_instance: {e}", exc_info=True)
            return gcp_error_response(500, f"Internal server error: {str(e)}")
    
    def list_instances(self, project, zone):
        """
        GET /compute/v1/projects/{project}/zones/{zone}/instances
        List all instances in a zone
        """
        try:
            # Validate zone format
            zone_valid, zone_error = validate_zone(zone)
            if not zone_valid:
                return gcp_error_response(400, zone_error)
            
            # Get all instances for project/zone
            instances = Instance.query.filter_by(
                project_id=project,
                zone=zone
            ).all()
            
            # Convert to GCP format
            items = [instance.to_gcp_dict() for instance in instances]
            
            return jsonify({
                "kind": "compute#instanceList",
                "id": f"projects/{project}/zones/{zone}/instances",
                "items": items,
                "selfLink": f"https://www.googleapis.com/compute/v1/projects/{project}/zones/{zone}/instances"
            }), 200
            
        except Exception as e:
            logger.error(f"Error in list_instances: {e}", exc_info=True)
            return gcp_error_response(500, f"Internal server error: {str(e)}")
    
    def get_instance(self, project, zone, instance_name):
        """
        GET /compute/v1/projects/{project}/zones/{zone}/instances/{instance}
        Get single instance details
        """
        try:
            # Validate zone format
            zone_valid, zone_error = validate_zone(zone)
            if not zone_valid:
                return gcp_error_response(400, zone_error)
            
            # Validate instance name
            name_valid, name_error = validate_instance_name(instance_name)
            if not name_valid:
                return gcp_error_response(400, name_error)
            
            instance = Instance.query.filter_by(
                name=instance_name,
                project_id=project,
                zone=zone
            ).first()
            
            if not instance:
                return gcp_error_response(
                    404, 
                    f"The resource 'projects/{project}/zones/{zone}/instances/{instance_name}' was not found"
                )
            
            return jsonify(instance.to_gcp_dict()), 200
            
        except Exception as e:
            logger.error(f"Error in get_instance: {e}", exc_info=True)
            return gcp_error_response(500, f"Internal server error: {str(e)}")
    
    def delete_instance(self, project, zone, instance_name):
        """
        DELETE /compute/v1/projects/{project}/zones/{zone}/instances/{instance}
        Delete (terminate) an instance
        """
        try:
            # Validate zone format
            zone_valid, zone_error = validate_zone(zone)
            if not zone_valid:
                return gcp_error_response(400, zone_error)
            
            # Validate instance name
            name_valid, name_error = validate_instance_name(instance_name)
            if not name_valid:
                return gcp_error_response(400, name_error)
            
            instance = Instance.query.filter_by(
                name=instance_name,
                project_id=project,
                zone=zone
            ).first()
            
            if not instance:
                return gcp_error_response(
                    404, 
                    f"The resource 'projects/{project}/zones/{zone}/instances/{instance_name}' was not found"
                )
            
            # Terminate using existing service
            success = self.compute_service.terminate_instance(instance.id)
            
            if not success:
                return gcp_error_response(500, "Failed to delete instance")
            
            # Create operation
            operation = self._create_operation(
                project=project,
                zone=zone,
                operation_type='delete',
                target_id=instance.id,
                target_name=instance_name
            )
            
            return jsonify(operation.to_gcp_dict()), 200
            
        except Exception as e:
            logger.error(f"Error in delete_instance: {e}", exc_info=True)
            return gcp_error_response(500, f"Internal server error: {str(e)}")
    
    def start_instance(self, project, zone, instance_name):
        """
        POST /compute/v1/projects/{project}/zones/{zone}/instances/{instance}/start
        Start a stopped instance
        """
        try:
            # Validate zone format
            zone_valid, zone_error = validate_zone(zone)
            if not zone_valid:
                return gcp_error_response(400, zone_error)
            
            # Validate instance name
            name_valid, name_error = validate_instance_name(instance_name)
            if not name_valid:
                return gcp_error_response(400, name_error)
            
            instance = Instance.query.filter_by(
                name=instance_name,
                project_id=project,
                zone=zone
            ).first()
            
            if not instance:
                return gcp_error_response(
                    404, 
                    f"The resource 'projects/{project}/zones/{zone}/instances/{instance_name}' was not found"
                )
            
            # Check if already running
            if instance.state == 'running':
                return gcp_error_response(
                    400, 
                    f"Instance is already in RUNNING state"
                )
            
            # Start using existing service
            success = self.compute_service.start_instance(instance.id)
            
            if not success:
                return gcp_error_response(500, "Failed to start instance")
            
            # Create operation
            operation = self._create_operation(
                project=project,
                zone=zone,
                operation_type='start',
                target_id=instance.id,
                target_name=instance_name
            )
            
            return jsonify(operation.to_gcp_dict()), 200
            
        except Exception as e:
            logger.error(f"Error in start_instance: {e}", exc_info=True)
            return gcp_error_response(500, f"Internal server error: {str(e)}")
    
    def stop_instance(self, project, zone, instance_name):
        """
        POST /compute/v1/projects/{project}/zones/{zone}/instances/{instance}/stop
        Stop a running instance
        """
        try:
            # Validate zone format
            zone_valid, zone_error = validate_zone(zone)
            if not zone_valid:
                return gcp_error_response(400, zone_error)
            
            # Validate instance name
            name_valid, name_error = validate_instance_name(instance_name)
            if not name_valid:
                return gcp_error_response(400, name_error)
            
            instance = Instance.query.filter_by(
                name=instance_name,
                project_id=project,
                zone=zone
            ).first()
            
            if not instance:
                return gcp_error_response(
                    404, 
                    f"The resource 'projects/{project}/zones/{zone}/instances/{instance_name}' was not found"
                )
            
            # Check if already stopped/terminated
            if instance.state in ['stopped', 'terminated']:
                return gcp_error_response(
                    400, 
                    f"Instance is already in TERMINATED state"
                )
            
            # Stop using existing service
            success = self.compute_service.stop_instance(instance.id)
            
            if not success:
                return gcp_error_response(500, "Failed to stop instance")
            
            # Create operation
            operation = self._create_operation(
                project=project,
                zone=zone,
                operation_type='stop',
                target_id=instance.id,
                target_name=instance_name
            )
            
            return jsonify(operation.to_gcp_dict()), 200
            
        except Exception as e:
            logger.error(f"Error in stop_instance: {e}", exc_info=True)
            return gcp_error_response(500, f"Internal server error: {str(e)}")
    
    def get_operation(self, project, zone, operation_name):
        """
        GET /compute/v1/projects/{project}/zones/{zone}/operations/{operation}
        Get operation status
        """
        try:
            # Validate zone format
            zone_valid, zone_error = validate_zone(zone)
            if not zone_valid:
                return gcp_error_response(400, zone_error)
            
            operation = ComputeOperation.query.filter_by(
                name=operation_name,
                project_id=project,
                zone=zone
            ).first()
            
            if not operation:
                return gcp_error_response(
                    404, 
                    f"The resource 'projects/{project}/zones/{zone}/operations/{operation_name}' was not found"
                )
            
            return jsonify(operation.to_gcp_dict()), 200
            
        except Exception as e:
            logger.error(f"Error in get_operation: {e}", exc_info=True)
            return gcp_error_response(500, f"Internal server error: {str(e)}")
