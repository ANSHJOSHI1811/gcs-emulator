"""
Firewall service for Compute Engine (Phase 5)
Handles firewall rule management
Metadata-only, no actual packet filtering
"""

import uuid
import time
from typing import List, Optional
from app.factory import db
from app.models.compute import FirewallRule
from app.logging import log_service_stage


class FirewallRuleNotFoundError(Exception):
    """Raised when firewall rule is not found"""
    pass


class FirewallRuleAlreadyExistsError(Exception):
    """Raised when trying to create a rule that already exists"""
    pass


class FirewallService:
    """Service for managing firewall rules (Phase 5)"""
    
    @staticmethod
    def create_firewall_rule(
        project_id: str,
        name: str,
        direction: str,
        protocol: str,
        port: Optional[int] = None,
        action: str = "ALLOW",
        priority: int = 1000,
        source_ranges: List[str] = None,
        destination_ranges: List[str] = None,
        target_tags: List[str] = None,
        description: str = None
    ) -> FirewallRule:
        """
        Create a new firewall rule
        
        Args:
            project_id: Project ID
            name: Rule name
            direction: INGRESS or EGRESS
            protocol: tcp, udp, icmp, etc.
            port: Port number (optional for tcp/udp)
            action: ALLOW or DENY
            priority: Priority (lower = higher priority)
            source_ranges: Source CIDR ranges (for INGRESS)
            destination_ranges: Destination CIDR ranges (for EGRESS)
            target_tags: Tags to apply rule to specific instances
            description: Rule description
            
        Returns:
            Created FirewallRule object
            
        Raises:
            FirewallRuleAlreadyExistsError: If rule with name exists
        """
        start_time = time.time()
        
        log_service_stage(
            message="Creating firewall rule",
            details={
                "project_id": project_id,
                "name": name,
                "direction": direction,
                "protocol": protocol,
                "port": port
            }
        )
        
        # Check if rule already exists
        existing = FirewallRule.query.filter_by(
            project_id=project_id,
            name=name
        ).first()
        
        if existing:
            raise FirewallRuleAlreadyExistsError(
                f"Firewall rule '{name}' already exists in project '{project_id}'"
            )
        
        # Validate direction
        if direction not in ["INGRESS", "EGRESS"]:
            raise ValueError(f"Invalid direction: {direction}. Must be INGRESS or EGRESS")
        
        # Validate action
        if action not in ["ALLOW", "DENY"]:
            raise ValueError(f"Invalid action: {action}. Must be ALLOW or DENY")
        
        try:
            # Create rule
            rule = FirewallRule(
                id=str(uuid.uuid4()),
                name=name,
                project_id=project_id,
                direction=direction,
                protocol=protocol.lower(),
                port=port,
                action=action,
                priority=priority,
                source_ranges=source_ranges or ["0.0.0.0/0"],
                destination_ranges=destination_ranges or ["0.0.0.0/0"],
                target_tags=target_tags or [],
                description=description
            )
            
            db.session.add(rule)
            db.session.commit()
            
            log_service_stage(
                message="Firewall rule created",
                details={
                    "rule_id": rule.id,
                    "rule_name": rule.name,
                    "duration_ms": (time.time() - start_time) * 1000
                }
            )
            
            return rule
        except Exception as e:
            db.session.rollback()
            log_service_stage(
                message="Firewall rule creation failed",
                details={"error": str(e)},
                level="ERROR"
            )
            raise
    
    @staticmethod
    def list_firewall_rules(project_id: str) -> List[FirewallRule]:
        """
        List all firewall rules in a project
        
        Args:
            project_id: Project ID
            
        Returns:
            List of FirewallRule objects
        """
        start_time = time.time()
        
        log_service_stage(
            message="Listing firewall rules",
            details={"project_id": project_id}
        )
        
        rules = FirewallRule.query.filter_by(project_id=project_id).all()
        
        log_service_stage(
            message="Firewall rules listed",
            details={
                "project_id": project_id,
                "count": len(rules),
                "duration_ms": (time.time() - start_time) * 1000
            }
        )
        
        return rules
    
    @staticmethod
    def get_firewall_rule(project_id: str, name: str) -> FirewallRule:
        """
        Get a specific firewall rule
        
        Args:
            project_id: Project ID
            name: Rule name
            
        Returns:
            FirewallRule object
            
        Raises:
            FirewallRuleNotFoundError: If rule not found
        """
        rule = FirewallRule.query.filter_by(
            project_id=project_id,
            name=name
        ).first()
        
        if not rule:
            raise FirewallRuleNotFoundError(
                f"Firewall rule '{name}' not found in project '{project_id}'"
            )
        
        return rule
    
    @staticmethod
    def delete_firewall_rule(project_id: str, name: str) -> bool:
        """
        Delete a firewall rule
        
        Args:
            project_id: Project ID
            name: Rule name
            
        Returns:
            True if deleted
            
        Raises:
            FirewallRuleNotFoundError: If rule not found
        """
        start_time = time.time()
        
        log_service_stage(
            message="Deleting firewall rule",
            details={"project_id": project_id, "name": name}
        )
        
        try:
            rule = FirewallService.get_firewall_rule(project_id, name)
            
            db.session.delete(rule)
            db.session.commit()
            
            log_service_stage(
                message="Firewall rule deleted",
                details={
                    "rule_id": rule.id,
                    "rule_name": rule.name,
                    "duration_ms": (time.time() - start_time) * 1000
                }
            )
            
            return True
        except Exception as e:
            db.session.rollback()
            log_service_stage(
                message="Firewall rule deletion failed",
                details={"error": str(e)},
                level="ERROR"
            )
            raise

