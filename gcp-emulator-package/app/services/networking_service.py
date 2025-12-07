"""
Networking service for Compute Engine (Phase 5)
Handles IP allocation and network configuration
Metadata-only, no real packet forwarding
"""

from app.factory import db
from app.models.compute import NetworkAllocation, Instance, FirewallRule
from app.logging import log_formatter_stage
import time


class NetworkingService:
    """
    Service for managing instance networking (Phase 5)
    Handles internal/external IP allocation
    """
    
    @staticmethod
    def ensure_network_allocation(project_id: str) -> NetworkAllocation:
        """
        Ensure NetworkAllocation record exists for project
        Creates if missing
        """
        allocation = NetworkAllocation.query.filter_by(project_id=project_id).first()
        
        if not allocation:
            try:
                allocation = NetworkAllocation(
                    project_id=project_id,
                    internal_counter=1,
                    external_counter=10,
                    allocated_internal_ips=[],
                    allocated_external_ips=[]
                )
                db.session.add(allocation)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                raise Exception(f"Failed to create network allocation: {str(e)}")
        
        return allocation
    
    @staticmethod
    def allocate_internal_ip(project_id: str) -> str:
        """
        Allocate internal IP for new instance
        Format: 10.0.X.Y
        
        Args:
            project_id: Project identifier
            
        Returns:
            Allocated internal IP address
        """
        start_time = time.time()
        
        log_formatter_stage(
            message="Allocating internal IP",
            details={"project_id": project_id}
        )
        
        try:
            allocation = NetworkingService.ensure_network_allocation(project_id)
            internal_ip = allocation.allocate_internal_ip()
            
            db.session.commit()
            
            duration_ms = (time.time() - start_time) * 1000
            log_formatter_stage(
                message="Internal IP allocated",
                duration_ms=duration_ms,
                details={
                    "project_id": project_id,
                    "internal_ip": internal_ip,
                    "counter": allocation.internal_counter
                }
            )
            
            return internal_ip
        except Exception as e:
            db.session.rollback()
            log_formatter_stage(
                message="Internal IP allocation failed",
                details={"project_id": project_id, "error": str(e)},
                level="ERROR"
            )
            raise
    
    @staticmethod
    def allocate_external_ip(project_id: str) -> str:
        """
        Allocate external IP for instance
        Format: 203.0.113.X (TEST-NET-3 range)
        
        Args:
            project_id: Project identifier
            
        Returns:
            Allocated external IP address
        """
        start_time = time.time()
        
        log_formatter_stage(
            message="Allocating external IP",
            details={"project_id": project_id}
        )
        
        try:
            allocation = NetworkingService.ensure_network_allocation(project_id)
            external_ip = allocation.allocate_external_ip()
            
            db.session.commit()
            
            duration_ms = (time.time() - start_time) * 1000
            log_formatter_stage(
                message="External IP allocated",
                duration_ms=duration_ms,
                details={
                    "project_id": project_id,
                    "external_ip": external_ip,
                    "counter": allocation.external_counter
                }
            )
            
            return external_ip
        except Exception as e:
            db.session.rollback()
            log_formatter_stage(
                message="External IP allocation failed",
                details={"project_id": project_id, "error": str(e)},
                level="ERROR"
            )
            raise
    
    @staticmethod
    def configure_instance_networking(instance: Instance, allocate_external: bool = True):
        """
        Configure networking for instance
        Called during instance creation
        
        Args:
            instance: Instance model
            allocate_external: Whether to allocate external IP immediately
        """
        start_time = time.time()
        
        log_formatter_stage(
            message="Configuring instance networking",
            details={
                "instance_id": instance.id,
                "instance_name": instance.name,
                "allocate_external": allocate_external
            }
        )
        
        try:
            # Allocate internal IP (always done on creation)
            if not instance.internal_ip:
                instance.internal_ip = NetworkingService.allocate_internal_ip(instance.project_id)
            
            # Optionally allocate external IP
            if allocate_external and not instance.external_ip:
                instance.external_ip = NetworkingService.allocate_external_ip(instance.project_id)
            
            db.session.commit()
            
            duration_ms = (time.time() - start_time) * 1000
            log_formatter_stage(
                message="Instance networking configured",
                duration_ms=duration_ms,
                details={
                    "instance_id": instance.id,
                    "internal_ip": instance.internal_ip,
                    "external_ip": instance.external_ip
                }
            )
        except Exception as e:
            db.session.rollback()
            log_formatter_stage(
                message="Instance networking configuration failed",
                details={"instance_id": instance.id, "error": str(e)},
                level="ERROR"
            )
            raise
    
    @staticmethod
    def attach_external_ip_on_start(instance: Instance):
        """
        Attach external IP when instance starts
        Only allocates if not already present
        
        Args:
            instance: Instance model
        """
        if not instance.external_ip:
            log_formatter_stage(
                message="Allocating external IP on instance start",
                details={
                    "instance_id": instance.id,
                    "instance_name": instance.name
                }
            )
            
            instance.external_ip = NetworkingService.allocate_external_ip(instance.project_id)
            db.session.commit()
    
    @staticmethod
    def get_matching_firewall_rules(instance: Instance) -> list:
        """
        Get firewall rules that apply to this instance
        Based on target tags
        
        Args:
            instance: Instance model
            
        Returns:
            List of matching FirewallRule objects
        """
        # Get all rules for project
        all_rules = FirewallRule.query.filter_by(project_id=instance.project_id).all()
        
        matching_rules = []
        instance_tags = set(instance.tags or [])
        
        for rule in all_rules:
            # If rule has no target tags, it applies to all instances
            if not rule.target_tags or len(rule.target_tags) == 0:
                matching_rules.append(rule)
            # If rule has target tags, check for intersection
            elif instance_tags and any(tag in instance_tags for tag in rule.target_tags):
                matching_rules.append(rule)
        
        return matching_rules
    
    @staticmethod
    def get_firewall_rules_for_response(instance: Instance) -> list:
        """
        Get firewall rules in API response format
        
        Args:
            instance: Instance model
            
        Returns:
            List of firewall rule dicts
        """
        rules = NetworkingService.get_matching_firewall_rules(instance)
        return [rule.to_dict() for rule in rules]
