"""
GCP Compute Engine API v1 Handler
Translates SDK requests to internal ComputeService calls
"""
from flask import jsonify, request
from datetime import datetime
import logging
import uuid

from app.models.instance import Instance
from app.models.compute_operation import ComputeOperation
from app.factory import db

logger = logging.getLogger(__name__)


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
            data = request.get_json()
            if not data:
                return jsonify({'error': {'message': 'Request body required'}}), 400
            
            # Extract instance name
            name = data.get('name')
            if not name:
                return jsonify({'error': {'message': 'Instance name required'}}), 400
            
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
                return jsonify({
                    'error': {
                        'code': 500,
                        'message': 'Failed to create instance'
                    }
                }), 500
            
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
            return jsonify({
                'error': {
                    'code': 500,
                    'message': f'Internal server error: {str(e)}'
                }
            }), 500
    
    def list_instances(self, project, zone):
        """
        GET /compute/v1/projects/{project}/zones/{zone}/instances
        List all instances in a zone
        """
        try:
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
            return jsonify({
                'error': {
                    'code': 500,
                    'message': f'Internal server error: {str(e)}'
                }
            }), 500
    
    def get_instance(self, project, zone, instance_name):
        """
        GET /compute/v1/projects/{project}/zones/{zone}/instances/{instance}
        Get single instance details
        """
        try:
            instance = Instance.query.filter_by(
                name=instance_name,
                project_id=project,
                zone=zone
            ).first()
            
            if not instance:
                return jsonify({
                    'error': {
                        'code': 404,
                        'message': f'Instance {instance_name} not found'
                    }
                }), 404
            
            return jsonify(instance.to_gcp_dict()), 200
            
        except Exception as e:
            logger.error(f"Error in get_instance: {e}", exc_info=True)
            return jsonify({
                'error': {
                    'code': 500,
                    'message': f'Internal server error: {str(e)}'
                }
            }), 500
    
    def delete_instance(self, project, zone, instance_name):
        """
        DELETE /compute/v1/projects/{project}/zones/{zone}/instances/{instance}
        Delete (terminate) an instance
        """
        try:
            instance = Instance.query.filter_by(
                name=instance_name,
                project_id=project,
                zone=zone
            ).first()
            
            if not instance:
                return jsonify({
                    'error': {
                        'code': 404,
                        'message': f'Instance {instance_name} not found'
                    }
                }), 404
            
            # Terminate using existing service
            success = self.compute_service.terminate_instance(instance.id)
            
            if not success:
                return jsonify({
                    'error': {
                        'code': 500,
                        'message': 'Failed to delete instance'
                    }
                }), 500
            
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
            return jsonify({
                'error': {
                    'code': 500,
                    'message': f'Internal server error: {str(e)}'
                }
            }), 500
    
    def start_instance(self, project, zone, instance_name):
        """
        POST /compute/v1/projects/{project}/zones/{zone}/instances/{instance}/start
        Start a stopped instance
        """
        try:
            instance = Instance.query.filter_by(
                name=instance_name,
                project_id=project,
                zone=zone
            ).first()
            
            if not instance:
                return jsonify({
                    'error': {
                        'code': 404,
                        'message': f'Instance {instance_name} not found'
                    }
                }), 404
            
            # Start using existing service
            success = self.compute_service.start_instance(instance.id)
            
            if not success:
                return jsonify({
                    'error': {
                        'code': 500,
                        'message': 'Failed to start instance'
                    }
                }), 500
            
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
            return jsonify({
                'error': {
                    'code': 500,
                    'message': f'Internal server error: {str(e)}'
                }
            }), 500
    
    def stop_instance(self, project, zone, instance_name):
        """
        POST /compute/v1/projects/{project}/zones/{zone}/instances/{instance}/stop
        Stop a running instance
        """
        try:
            instance = Instance.query.filter_by(
                name=instance_name,
                project_id=project,
                zone=zone
            ).first()
            
            if not instance:
                return jsonify({
                    'error': {
                        'code': 404,
                        'message': f'Instance {instance_name} not found'
                    }
                }), 404
            
            # Stop using existing service
            success = self.compute_service.stop_instance(instance.id)
            
            if not success:
                return jsonify({
                    'error': {
                        'code': 500,
                        'message': 'Failed to stop instance'
                    }
                }), 500
            
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
            return jsonify({
                'error': {
                    'code': 500,
                    'message': f'Internal server error: {str(e)}'
                }
            }), 500
    
    def get_operation(self, project, zone, operation_name):
        """
        GET /compute/v1/projects/{project}/zones/{zone}/operations/{operation}
        Get operation status
        """
        try:
            operation = ComputeOperation.query.filter_by(
                name=operation_name,
                project_id=project,
                zone=zone
            ).first()
            
            if not operation:
                return jsonify({
                    'error': {
                        'code': 404,
                        'message': f'Operation {operation_name} not found'
                    }
                }), 404
            
            return jsonify(operation.to_gcp_dict()), 200
            
        except Exception as e:
            logger.error(f"Error in get_operation: {e}", exc_info=True)
            return jsonify({
                'error': {
                    'code': 500,
                    'message': f'Internal server error: {str(e)}'
                }
            }), 500
