"""
Firewall handlers for Compute Engine (Phase 5)
Request/response handling for firewall rules
"""

from flask import jsonify, request
from app.services.firewall_service import (
    FirewallService,
    FirewallRuleNotFoundError,
    FirewallRuleAlreadyExistsError
)
from app.logging import log_handler_stage
import time


class FirewallHandler:
    """Handlers for firewall rule operations (Phase 5)"""
    
    @staticmethod
    def create_firewall_rule(project_id: str):
        """
        Handle POST /compute/v1/projects/{project}/global/firewalls
        
        Request body:
        {
            "name": "allow-ssh",
            "direction": "INGRESS",
            "allowed": [{"IPProtocol": "tcp", "ports": ["22"]}],
            "targetTags": ["ssh-server"],
            "sourceRanges": ["0.0.0.0/0"]
        }
        """
        start_time = time.time()
        
        log_handler_stage(
            message="Firewall rule creation request",
            details={"project_id": project_id}
        )
        
        data = request.get_json()
        
        # Extract fields from GCE-style request
        name = data.get("name")
        direction = data.get("direction", "INGRESS")
        description = data.get("description", "")
        priority = data.get("priority", 1000)
        target_tags = data.get("targetTags", [])
        source_ranges = data.get("sourceRanges", ["0.0.0.0/0"])
        destination_ranges = data.get("destinationRanges", ["0.0.0.0/0"])
        
        # Parse allowed/denied rules
        action = "ALLOW"
        protocol = "tcp"
        port = None
        
        if "allowed" in data and len(data["allowed"]) > 0:
            action = "ALLOW"
            rule = data["allowed"][0]
            protocol = rule.get("IPProtocol", "tcp")
            ports = rule.get("ports", [])
            if ports:
                port = int(ports[0]) if isinstance(ports[0], str) else ports[0]
        elif "denied" in data and len(data["denied"]) > 0:
            action = "DENY"
            rule = data["denied"][0]
            protocol = rule.get("IPProtocol", "tcp")
            ports = rule.get("ports", [])
            if ports:
                port = int(ports[0]) if isinstance(ports[0], str) else ports[0]
        
        # Validate required fields
        if not name:
            return jsonify({
                "error": {
                    "code": 400,
                    "message": "Field 'name' is required"
                }
            }), 400
        
        try:
            # Create firewall rule
            rule = FirewallService.create_firewall_rule(
                project_id=project_id,
                name=name,
                direction=direction,
                protocol=protocol,
                port=port,
                action=action,
                priority=priority,
                source_ranges=source_ranges,
                destination_ranges=destination_ranges,
                target_tags=target_tags,
                description=description
            )
            
            response = {
                "kind": "compute#operation",
                "id": rule.id,
                "name": f"insert-firewall-{rule.name}",
                "operationType": "insert",
                "targetLink": f"projects/{project_id}/global/firewalls/{rule.name}",
                "status": "DONE",
                "progress": 100
            }
            
            log_handler_stage(
                message="Firewall rule created",
                duration_ms=(time.time() - start_time) * 1000,
                details={"rule_id": rule.id, "rule_name": rule.name}
            )
            
            return jsonify(response), 200
            
        except FirewallRuleAlreadyExistsError as e:
            return jsonify({
                "error": {
                    "code": 409,
                    "message": str(e)
                }
            }), 409
        except ValueError as e:
            return jsonify({
                "error": {
                    "code": 400,
                    "message": str(e)
                }
            }), 400
        except Exception as e:
            log_handler_stage(
                message="Firewall rule creation failed",
                details={"error": str(e)},
                level="ERROR"
            )
            return jsonify({
                "error": {
                    "code": 500,
                    "message": f"Internal server error: {str(e)}"
                }
            }), 500
    
    @staticmethod
    def list_firewall_rules(project_id: str):
        """
        Handle GET /compute/v1/projects/{project}/global/firewalls
        """
        start_time = time.time()
        
        log_handler_stage(
            message="List firewall rules request",
            details={"project_id": project_id}
        )
        
        try:
            rules = FirewallService.list_firewall_rules(project_id)
            
            response = {
                "kind": "compute#firewallList",
                "id": f"projects/{project_id}/global/firewalls",
                "items": [rule.to_dict() for rule in rules],
                "selfLink": f"https://www.googleapis.com/compute/v1/projects/{project_id}/global/firewalls"
            }
            
            log_handler_stage(
                message="Firewall rules listed",
                duration_ms=(time.time() - start_time) * 1000,
                details={"count": len(rules)}
            )
            
            return jsonify(response), 200
            
        except Exception as e:
            log_handler_stage(
                message="List firewall rules failed",
                details={"error": str(e)},
                level="ERROR"
            )
            return jsonify({
                "error": {
                    "code": 500,
                    "message": f"Internal server error: {str(e)}"
                }
            }), 500
    
    @staticmethod
    def get_firewall_rule(project_id: str, firewall_name: str):
        """
        Handle GET /compute/v1/projects/{project}/global/firewalls/{firewall}
        """
        start_time = time.time()
        
        log_handler_stage(
            message="Get firewall rule request",
            details={"project_id": project_id, "firewall_name": firewall_name}
        )
        
        try:
            rule = FirewallService.get_firewall_rule(project_id, firewall_name)
            
            log_handler_stage(
                message="Firewall rule retrieved",
                duration_ms=(time.time() - start_time) * 1000,
                details={"rule_id": rule.id}
            )
            
            return jsonify(rule.to_dict()), 200
            
        except FirewallRuleNotFoundError as e:
            return jsonify({
                "error": {
                    "code": 404,
                    "message": str(e)
                }
            }), 404
        except Exception as e:
            log_handler_stage(
                message="Get firewall rule failed",
                details={"error": str(e)},
                level="ERROR"
            )
            return jsonify({
                "error": {
                    "code": 500,
                    "message": f"Internal server error: {str(e)}"
                }
            }), 500
    
    @staticmethod
    def delete_firewall_rule(project_id: str, firewall_name: str):
        """
        Handle DELETE /compute/v1/projects/{project}/global/firewalls/{firewall}
        """
        start_time = time.time()
        
        log_handler_stage(
            message="Delete firewall rule request",
            details={"project_id": project_id, "firewall_name": firewall_name}
        )
        
        try:
            FirewallService.delete_firewall_rule(project_id, firewall_name)
            
            response = {
                "kind": "compute#operation",
                "id": f"delete-firewall-{firewall_name}",
                "name": f"delete-firewall-{firewall_name}",
                "operationType": "delete",
                "targetLink": f"projects/{project_id}/global/firewalls/{firewall_name}",
                "status": "DONE",
                "progress": 100
            }
            
            log_handler_stage(
                message="Firewall rule deleted",
                duration_ms=(time.time() - start_time) * 1000,
                details={"firewall_name": firewall_name}
            )
            
            return jsonify(response), 200
            
        except FirewallRuleNotFoundError as e:
            return jsonify({
                "error": {
                    "code": 404,
                    "message": str(e)
                }
            }), 404
        except Exception as e:
            log_handler_stage(
                message="Delete firewall rule failed",
                details={"error": str(e)},
                level="ERROR"
            )
            return jsonify({
                "error": {
                    "code": 500,
                    "message": f"Internal server error: {str(e)}"
                }
            }), 500
