"""
GCP Compute Engine API v1 Handler
Translates SDK requests to internal ComputeService calls
"""
from flask import jsonify, request
from datetime import datetime
import logging
import uuid
import re
import json

from app.models.instance import Instance
from app.models.compute_operation import ComputeOperation
from app.factory import db
from app.utils.machine_types import get_machine_type_specs, is_valid_machine_type, list_machine_types
from app.utils.zones import is_valid_zone, list_zones, get_zone_info

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
    """
    Validate zone against catalog
    Phase 3: Now checks against static zone catalog
    """
    if not zone:
        return False, "Zone is required"
    
    if not is_valid_zone(zone):
        # Provide helpful error with available zones
        available = list_zones()[:10]  # Show first 10
        return False, f"Invalid zone '{zone}'. Available zones include: {', '.join(available)}..."
    
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
            print(f"[DEBUG] insert_instance called for zone: {zone}")
            
            # Validate zone format
            zone_valid, zone_error = validate_zone(zone)
            print(f"[DEBUG] Zone validation result: valid={zone_valid}, error={zone_error}")
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
            
            logger.info(f"Extracted machine_type: '{machine_type}' from URL: '{machine_type_url}'")
            
            # Phase 3: Validate machine type against catalog
            if not is_valid_machine_type(machine_type):
                available = list_machine_types()[:10]  # Show first 10
                logger.warning(f"Invalid machine type '{machine_type}' rejected")
                return gcp_error_response(
                    400,
                    f"Invalid machine type '{machine_type}'. Available types include: {', '.join(available)}..."
                )
            
            # Get machine type specifications from catalog
            try:
                machine_specs = get_machine_type_specs(machine_type)
                cpu = machine_specs['cpus']
                memory = machine_specs['memory_mb']
            except ValueError as e:
                return gcp_error_response(400, str(e))
            
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
            
            # Phase 2: Extract metadata and labels
            metadata_obj = data.get('metadata', {})
            labels_obj = data.get('labels', {})
            description = data.get('description', '')
            
            # Convert metadata items array to dict
            metadata_dict = {}
            if isinstance(metadata_obj, dict):
                metadata_items = metadata_obj.get('items', [])
                for item in metadata_items:
                    if isinstance(item, dict) and 'key' in item and 'value' in item:
                        metadata_dict[item['key']] = item['value']
            
            # Validate labels format (lowercase alphanumeric, hyphens, underscores)
            if labels_obj and isinstance(labels_obj, dict):
                for key, value in labels_obj.items():
                    if not re.match(r'^[a-z0-9_-]+$', key):
                        return gcp_error_response(400, f"Invalid label key: {key}")
                    if not re.match(r'^[a-z0-9_-]+$', str(value)):
                        return gcp_error_response(400, f"Invalid label value: {value}")
            
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
            
            # Update instance with zone, machine_type, metadata_items, labels, description
            instance.zone = zone
            instance.machine_type = machine_type
            instance.metadata_items = json.dumps(metadata_dict)
            instance.labels = json.dumps(labels_obj) if labels_obj else '{}'
            instance.description = description if description else None
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
