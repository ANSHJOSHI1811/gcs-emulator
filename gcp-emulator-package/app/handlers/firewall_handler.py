"""
Firewall Rules Handler - VPC Firewall Management

Handles:
- Create firewall rule (ingress/egress)
- List firewall rules
- Get firewall rule details
- Delete firewall rule
- Update firewall rule
- Priority management
"""

from flask import jsonify, request
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, or_
from app.factory import db
from app.models.vpc import Network, FirewallRule, FirewallAllowedDenied
from app.validators.vpc_validators import validate_firewall_rule, validate_port_spec
from app.utils.operation_utils import create_operation
from datetime import datetime
import uuid


def create_firewall_rule(project_id: str):
    """
    Create a new firewall rule
    
    Request body:
    {
        "name": "allow-ssh",
        "network": "projects/PROJECT/global/networks/NETWORK",
        "direction": "INGRESS",
        "priority": 1000,
        "sourceRanges": ["0.0.0.0/0"],
        "allowed": [
            {"IPProtocol": "tcp", "ports": ["22"]}
        ],
        "targetTags": ["ssh-server"]
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or "name" not in data:
            return jsonify({"error": {"message": "Firewall rule name is required"}}), 400
        
        if "network" not in data:
            return jsonify({"error": {"message": "Network is required"}}), 400
        
        # Extract direction and action
        direction = data.get("direction", "INGRESS")
        
        # Determine action from allowed/denied
        if "allowed" in data:
            action = "ALLOW"
            rules_data = data["allowed"]
        elif "denied" in data:
            action = "DENY"
            rules_data = data["denied"]
        else:
            return jsonify({
                "error": {
                    "message": "Either 'allowed' or 'denied' must be specified"
                }
            }), 400
        
        # Validate firewall rule
        is_valid, error_msg = validate_firewall_rule(
            name=data["name"],
            priority=data.get("priority", 1000),
            direction=direction,
            action=action,
            protocols=rules_data,
            source_ranges=data.get("sourceRanges"),
            destination_ranges=data.get("destinationRanges")
        )
        if not is_valid:
            return jsonify({"error": {"message": error_msg}}), 400
        
        # Extract network name from URL
        network_url_parts = data["network"].split("/")
        if "networks" in network_url_parts:
            network_name = network_url_parts[network_url_parts.index("networks") + 1]
        else:
            network_name = data["network"]
        
        # Get the network
        network = Network.query.filter_by(
            project_id=project_id,
            name=network_name
        ).first()
        
        if not network:
            return jsonify({
                "error": {
                    "message": f"Network '{network_name}' not found in project '{project_id}'"
                }
            }), 404
        
        # Check for duplicate name in network
        existing_rule = FirewallRule.query.filter_by(
            network_id=network.id,
            name=data["name"]
        ).first()
        
        if existing_rule:
            return jsonify({
                "error": {
                    "message": f"Firewall rule '{data['name']}' already exists in network '{network_name}'"
                }
            }), 409
        
        # Create firewall rule
        rule_id = str(uuid.uuid4())
        firewall_rule = FirewallRule(
            id=rule_id,
            network_id=network.id,
            name=data["name"],
            description=data.get("description", ""),
            priority=data.get("priority", 1000),
            direction=direction,
            action=action,
            disabled=data.get("disabled", False),
            source_ranges=data.get("sourceRanges", []),
            destination_ranges=data.get("destinationRanges", []),
            source_tags=data.get("sourceTags", []),
            target_tags=data.get("targetTags", []),
            source_service_accounts=data.get("sourceServiceAccounts", []),
            target_service_accounts=data.get("targetServiceAccounts", [])
        )
        
        db.session.add(firewall_rule)
        db.session.flush()  # Get the ID
        
        # Create allowed/denied rules
        for rule_spec in rules_data:
            protocol = rule_spec.get("IPProtocol", "all")
            ports = rule_spec.get("ports", [])
            
            allowed_denied = FirewallAllowedDenied(
                id=str(uuid.uuid4()),
                firewall_rule_id=firewall_rule.id,
                ip_protocol=protocol,
                ports=ports
            )
            db.session.add(allowed_denied)
        
        db.session.commit()
        
        # Return operation instead of firewall object
        operation = create_operation(
            project_id=project_id,
            operation_type='insert',
            target_link=firewall_rule.get_self_link(project_id),
            target_id=str(firewall_rule.id)
        )
        return jsonify(operation.to_dict()), 200
        
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({
            "error": {
                "message": f"Database constraint violation: {str(e)}"
            }
        }), 409
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": {
                "message": f"Failed to create firewall rule: {str(e)}"
            }
        }), 500


def list_firewall_rules(project_id: str):
    """
    List firewall rules in a project
    
    Query parameters:
    - filter: Optional filter string
    - maxResults: Maximum number of results
    - pageToken: Pagination token
    """
    try:
        # Get all networks in the project
        networks = Network.query.filter_by(project_id=project_id).all()
        network_ids = [n.id for n in networks]
        
        # Build query for firewall rules
        query = FirewallRule.query.filter(FirewallRule.network_id.in_(network_ids))
        
        # Apply filter if provided
        filter_param = request.args.get("filter")
        if filter_param:
            # Simple name filter
            if "name=" in filter_param:
                name_filter = filter_param.split("name=")[1].strip('"')
                query = query.filter(FirewallRule.name.ilike(f"%{name_filter}%"))
        
        # Get results
        rules = query.order_by(FirewallRule.priority).all()
        
        # Build response
        items = [rule.to_dict(project_id=project_id) for rule in rules]
        
        base_url = request.host_url.rstrip("/")
        response = {
            "kind": "compute#firewallList",
            "id": f"projects/{project_id}/global/firewalls",
            "items": items,
            "selfLink": f"{base_url}/compute/v1/projects/{project_id}/global/firewalls"
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({
            "error": {
                "message": f"Failed to list firewall rules: {str(e)}"
            }
        }), 500


def get_firewall_rule(project_id: str, firewall_name: str):
    """Get details of a specific firewall rule"""
    try:
        # Get networks in project
        networks = Network.query.filter_by(project_id=project_id).all()
        network_ids = [n.id for n in networks]
        
        firewall_rule = FirewallRule.query.filter(
            and_(
                FirewallRule.network_id.in_(network_ids),
                FirewallRule.name == firewall_name
            )
        ).first()
        
        if not firewall_rule:
            return jsonify({
                "error": {
                    "message": f"Firewall rule '{firewall_name}' not found"
                }
            }), 404
        
        return jsonify(firewall_rule.to_dict(project_id=project_id)), 200
        
    except Exception as e:
        return jsonify({
            "error": {
                "message": f"Failed to get firewall rule: {str(e)}"
            }
        }), 500


def delete_firewall_rule(project_id: str, firewall_name: str):
    """Delete a firewall rule"""
    try:
        # Get networks in project
        networks = Network.query.filter_by(project_id=project_id).all()
        network_ids = [n.id for n in networks]
        
        firewall_rule = FirewallRule.query.filter(
            and_(
                FirewallRule.network_id.in_(network_ids),
                FirewallRule.name == firewall_name
            )
        ).first()
        
        if not firewall_rule:
            return jsonify({
                "error": {
                    "message": f"Firewall rule '{firewall_name}' not found"
                }
            }), 404
        
        # Delete the firewall rule (cascade will delete allowed/denied rules)
        db.session.delete(firewall_rule)
        db.session.commit()
        
        # Return operation
        operation = create_operation(
            project_id=project_id,
            operation_type='delete',
            target_link=firewall_rule.get_self_link(project_id),
            target_id=str(firewall_rule.id)
        )
        return jsonify(operation.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": {
                "message": f"Failed to delete firewall rule: {str(e)}"
            }
        }), 500


def update_firewall_rule(project_id: str, firewall_name: str):
    """
    Update firewall rule properties
    
    Updatable fields:
    - priority
    - sourceRanges
    - destinationRanges
    - sourceTags
    - targetTags
    - sourceServiceAccounts
    - targetServiceAccounts
    - allowed/denied rules
    - disabled
    - description
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "error": {
                    "message": "Request body is required"
                }
            }), 400
        
        # Get networks in project
        networks = Network.query.filter_by(project_id=project_id).all()
        network_ids = [n.id for n in networks]
        
        firewall_rule = FirewallRule.query.filter(
            and_(
                FirewallRule.network_id.in_(network_ids),
                FirewallRule.name == firewall_name
            )
        ).first()
        
        if not firewall_rule:
            return jsonify({
                "error": {
                    "message": f"Firewall rule '{firewall_name}' not found"
                }
            }), 404
        
        # Update allowed fields
        if "priority" in data:
            priority = data["priority"]
            if not isinstance(priority, int) or priority < 0 or priority > 65535:
                return jsonify({
                    "error": {
                        "message": "Priority must be between 0 and 65535"
                    }
                }), 400
            firewall_rule.priority = priority
        
        if "sourceRanges" in data:
            firewall_rule.source_ranges = data["sourceRanges"]
        
        if "destinationRanges" in data:
            firewall_rule.destination_ranges = data["destinationRanges"]
        
        if "sourceTags" in data:
            firewall_rule.source_tags = data["sourceTags"]
        
        if "targetTags" in data:
            firewall_rule.target_tags = data["targetTags"]
        
        if "sourceServiceAccounts" in data:
            firewall_rule.source_service_accounts = data["sourceServiceAccounts"]
        
        if "targetServiceAccounts" in data:
            firewall_rule.target_service_accounts = data["targetServiceAccounts"]
        
        if "disabled" in data:
            firewall_rule.disabled = data["disabled"]
        
        if "description" in data:
            firewall_rule.description = data["description"]
        
        # Update allowed/denied rules if provided
        if "allowed" in data or "denied" in data:
            # Delete existing rules
            FirewallAllowedDenied.query.filter_by(
                firewall_rule_id=firewall_rule.id
            ).delete()
            
            # Determine action and rules
            if "allowed" in data:
                firewall_rule.action = "ALLOW"
                rules_data = data["allowed"]
            else:
                firewall_rule.action = "DENY"
                rules_data = data["denied"]
            
            # Create new rules
            for rule_spec in rules_data:
                protocol = rule_spec.get("IPProtocol", "all")
                ports = rule_spec.get("ports", [])
                
                allowed_denied = FirewallAllowedDenied(
                    id=str(uuid.uuid4()),
                    firewall_rule_id=firewall_rule.id,
                    ip_protocol=protocol,
                    ports=ports
                )
                db.session.add(allowed_denied)
        
        firewall_rule.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify(firewall_rule.to_dict(project_id=project_id)), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": {
                "message": f"Failed to update firewall rule: {str(e)}"
            }
        }), 500


def patch_firewall_rule(project_id: str, firewall_name: str):
    """
    Patch firewall rule (same as update for now)
    """
    return update_firewall_rule(project_id, firewall_name)
