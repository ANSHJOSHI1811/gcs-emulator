"""
Private Google Access Handler

Enables VMs without external IPs to reach Google APIs.
This is a simplified metadata-only implementation for the emulator.
"""

from flask import request, jsonify
from app.models.vpc import Subnetwork
from app.factory import db
from app.utils.operation_utils import create_operation


def enable_private_google_access(project_id: str, region: str, subnetwork_name: str):
    """
    Enable Private Google Access on a subnetwork
    
    Request body:
    {
        "privateIpGoogleAccess": true
    }
    """
    try:
        data = request.get_json()
        
        # Find subnetwork
        subnetwork = Subnetwork.query.filter_by(
            region=region,
            name=subnetwork_name
        ).first()
        
        if not subnetwork:
            return jsonify({
                "error": {"message": f"Subnetwork '{subnetwork_name}' not found in region '{region}'"}
            }), 404
        
        # Get the network to verify project
        if subnetwork.network.project_id != project_id:
            return jsonify({
                "error": {"message": f"Subnetwork '{subnetwork_name}' not found in project '{project_id}'"}
            }), 404
        
        # Check if already enabled/disabled
        requested_state = data.get("privateIpGoogleAccess", True)
        if subnetwork.private_ip_google_access == requested_state:
            # Already in desired state
            operation = create_operation(
                project_id=project_id,
                operation_type='setPrivateIpGoogleAccess',
                target_link=subnetwork.get_self_link(project_id),
                target_id=str(subnetwork.id),
                region=region,
                status='DONE'
            )
            return jsonify(operation.to_dict()), 200
        
        # Update Private Google Access setting
        subnetwork.private_ip_google_access = requested_state
        db.session.commit()
        
        # Return operation
        operation = create_operation(
            project_id=project_id,
            operation_type='setPrivateIpGoogleAccess',
            target_link=subnetwork.get_self_link(project_id),
            target_id=str(subnetwork.id),
            region=region
        )
        return jsonify(operation.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": {"message": f"Failed to set Private Google Access: {str(e)}"}
        }), 500


def get_private_google_access_status(project_id: str, region: str, subnetwork_name: str):
    """Get Private Google Access status for a subnetwork"""
    try:
        # Find subnetwork
        subnetwork = Subnetwork.query.filter_by(
            region=region,
            name=subnetwork_name
        ).first()
        
        if not subnetwork:
            return jsonify({
                "error": {"message": f"Subnetwork '{subnetwork_name}' not found"}
            }), 404
        
        # Verify project
        if subnetwork.network.project_id != project_id:
            return jsonify({
                "error": {"message": f"Subnetwork '{subnetwork_name}' not found in project '{project_id}'"}
            }), 404
        
        response = {
            "kind": "compute#subnetwork",
            "name": subnetwork.name,
            "privateIpGoogleAccess": subnetwork.private_ip_google_access,
            "selfLink": subnetwork.get_self_link(project_id)
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({
            "error": {"message": f"Failed to get Private Google Access status: {str(e)}"}
        }), 500
