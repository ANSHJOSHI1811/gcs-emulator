"""PHASE 1: Compute Handler - Handles HTTP requests for Compute Service endpoints"""
from flask import jsonify, request
import logging

logger = logging.getLogger(__name__)


class ComputeHandler:
    """Handler for PHASE 1 Compute Engine API endpoints"""
    
    def __init__(self, compute_service):
        """Initialize handler with compute service"""
        self.compute_service = compute_service
    
    def run_instance(self):
        """Handle POST /compute/instances - Create and launch a new instance"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Request body required'}), 400
            
            name = data.get('name')
            image = data.get('image')
            
            if not all([name, image]):
                return jsonify({'error': 'Missing required fields: name, image'}), 400
            
            cpu = data.get('cpu', 1)
            memory = data.get('memory', 512)
            
            if not isinstance(cpu, int) or cpu < 1 or cpu > 8:
                return jsonify({'error': 'cpu must be an integer between 1 and 8'}), 400
            
            if not isinstance(memory, int) or memory < 128 or memory > 8192:
                return jsonify({'error': 'memory must be an integer between 128 and 8192 MB'}), 400
            
            instance = self.compute_service.run_instance(
                name=name,
                image=image,
                cpu=cpu,
                memory=memory
            )
            
            if not instance:
                return jsonify({'error': 'Failed to create instance'}), 500
            
            return jsonify(instance.to_dict()), 201
            
        except Exception as e:
            logger.error(f"Error in run_instance: {e}", exc_info=True)
            return jsonify({'error': 'Internal server error'}), 500
    
    def describe_instances(self):
        """Handle GET /compute/instances - List instances with filters"""
        try:
            instance_ids_str = request.args.get('instance_ids')
            states_str = request.args.get('states')
            
            instance_ids = None
            if instance_ids_str:
                instance_ids = [id.strip() for id in instance_ids_str.split(',')]
            
            states = None
            if states_str:
                states = [state.strip() for state in states_str.split(',')]
            
            instances = self.compute_service.describe_instances(
                instance_ids=instance_ids,
                states=states
            )
            
            return jsonify({
                'count': len(instances),
                'instances': [instance.to_dict() for instance in instances]
            }), 200
            
        except Exception as e:
            logger.error(f"Error in describe_instances: {e}", exc_info=True)
            return jsonify({'error': 'Internal server error'}), 500
    
    def get_instance(self, instance_id):
        """Handle GET /compute/instances/<instance_id> - Get single instance"""
        try:
            instance = self.compute_service.get_instance(instance_id)
            
            if not instance:
                return jsonify({'error': 'Instance not found'}), 404
            
            return jsonify(instance.to_dict()), 200
            
        except Exception as e:
            logger.error(f"Error in get_instance: {e}", exc_info=True)
            return jsonify({'error': 'Internal server error'}), 500
    
    def stop_instance(self, instance_id):
        """Handle POST /compute/instances/<instance_id>/stop - Stop instance"""
        try:
            success = self.compute_service.stop_instance(instance_id)
            
            if success:
                instance = self.compute_service.get_instance(instance_id)
                return jsonify({
                    'message': 'Instance stopped successfully',
                    'instance': instance.to_dict() if instance else None
                }), 200
            else:
                return jsonify({'error': 'Failed to stop instance'}), 400
            
        except Exception as e:
            logger.error(f"Error in stop_instance: {e}", exc_info=True)
            return jsonify({'error': 'Internal server error'}), 500
    
    def terminate_instance(self, instance_id):
        """Handle POST /compute/instances/<instance_id>/terminate - Terminate instance"""
        try:
            success = self.compute_service.terminate_instance(instance_id)
            
            if success:
                return jsonify({
                    'message': 'Instance terminated successfully',
                    'instance_id': instance_id
                }), 200
            else:
                return jsonify({'error': 'Failed to terminate instance'}), 400
            
        except Exception as e:
            logger.error(f"Error in terminate_instance: {e}", exc_info=True)
            return jsonify({'error': 'Internal server error'}), 500
