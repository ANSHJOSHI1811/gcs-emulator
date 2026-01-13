"""
VPC Validators

Validation functions for:
- Network names and configurations
- Subnet configurations
- Firewall rules
- Routes
"""

import re
from typing import Tuple, Optional, List
from app.utils.ip_utils import validate_cidr, validate_firewall_cidr, cidr_overlaps, validate_ip_in_range


# GCP Resource naming pattern (RFC 1035)
NAME_PATTERN = re.compile(r'^[a-z]([-a-z0-9]*[a-z0-9])?$')
MAX_NAME_LENGTH = 63


def validate_resource_name(name: str, resource_type: str = "resource") -> Tuple[bool, Optional[str]]:
    """
    Validate GCP resource name (RFC 1035)
    
    Args:
        name: Resource name
        resource_type: Type of resource (for error messages)
        
    Returns:
        (is_valid, error_message)
    """
    if not name:
        return False, f"{resource_type} name is required"
    
    if len(name) > MAX_NAME_LENGTH:
        return False, f"{resource_type} name must be {MAX_NAME_LENGTH} characters or less"
    
    if not NAME_PATTERN.match(name):
        return False, (
            f"{resource_type} name must start with a lowercase letter, "
            "contain only lowercase letters, numbers, and hyphens, "
            "and end with a letter or number"
        )
    
    return True, None


def validate_network_config(name: str, routing_mode: str, mtu: int, 
                            auto_create: bool) -> Tuple[bool, Optional[str]]:
    """
    Validate network configuration
    
    Args:
        name: Network name
        routing_mode: REGIONAL or GLOBAL
        mtu: Maximum Transmission Unit
        auto_create: Auto-create subnetworks flag
        
    Returns:
        (is_valid, error_message)
    """
    # Validate name
    is_valid, error = validate_resource_name(name, "Network")
    if not is_valid:
        return False, error
    
    # Validate routing mode
    if routing_mode not in ['REGIONAL', 'GLOBAL']:
        return False, "Routing mode must be 'REGIONAL' or 'GLOBAL'"
    
    # Validate MTU
    if mtu not in [1460, 1500]:
        return False, "MTU must be 1460 (default) or 1500 (jumbo frames)"
    
    return True, None


def validate_subnet_config(name: str, cidr: str, region: str, 
                          existing_cidrs: List[str] = None) -> Tuple[bool, Optional[str]]:
    """
    Validate subnet configuration
    
    Args:
        name: Subnet name
        cidr: CIDR range
        region: GCP region
        existing_cidrs: List of existing CIDR ranges in same network
        
    Returns:
        (is_valid, error_message)
    """
    # Validate name
    is_valid, error = validate_resource_name(name, "Subnet")
    if not is_valid:
        return False, error
    
    # Validate CIDR
    is_valid, error = validate_cidr(cidr)
    if not is_valid:
        return False, error
    
    # Validate region format
    if not re.match(r'^[a-z]+-[a-z]+[0-9]+$', region):
        return False, f"Invalid region format: {region}"
    
    # Check for overlaps with existing subnets
    if existing_cidrs:
        for existing_cidr in existing_cidrs:
            if cidr_overlaps(cidr, existing_cidr):
                return False, f"CIDR range {cidr} overlaps with existing range {existing_cidr}"
    
    return True, None


def validate_firewall_rule(name: str, priority: int, direction: str, 
                          action: str, protocols: List[dict],
                          source_ranges: List[str] = None,
                          destination_ranges: List[str] = None) -> Tuple[bool, Optional[str]]:
    """
    Validate firewall rule configuration
    
    Args:
        name: Rule name
        priority: Priority (0-65535)
        direction: INGRESS or EGRESS
        action: ALLOW or DENY
        protocols: List of protocol dicts with IPProtocol and ports
        source_ranges: Source CIDR ranges (for INGRESS)
        destination_ranges: Destination CIDR ranges (for EGRESS)
        
    Returns:
        (is_valid, error_message)
    """
    # Validate name
    is_valid, error = validate_resource_name(name, "Firewall rule")
    if not is_valid:
        return False, error
    
    # Validate priority
    if not isinstance(priority, int) or priority < 0 or priority > 65535:
        return False, "Priority must be between 0 and 65535"
    
    # Validate direction
    if direction not in ['INGRESS', 'EGRESS']:
        return False, "Direction must be 'INGRESS' or 'EGRESS'"
    
    # Validate action
    if action not in ['ALLOW', 'DENY']:
        return False, "Action must be 'ALLOW' or 'DENY'"
    
    # Validate protocols
    if not protocols or len(protocols) == 0:
        return False, "At least one protocol must be specified"
    
    valid_protocols = ['tcp', 'udp', 'icmp', 'esp', 'ah', 'sctp', 'ipip', 'all']
    for proto in protocols:
        if 'IPProtocol' not in proto:
            return False, "Each protocol must have 'IPProtocol' field"
        
        if proto['IPProtocol'].lower() not in valid_protocols:
            return False, f"Invalid protocol: {proto['IPProtocol']}"
        
        # Validate ports if present
        if 'ports' in proto:
            for port_spec in proto['ports']:
                if not validate_port_spec(port_spec):
                    return False, f"Invalid port specification: {port_spec}"
    
    # Validate source ranges (for INGRESS)
    if direction == 'INGRESS' and source_ranges:
        for cidr in source_ranges:
            is_valid, error = validate_firewall_cidr(cidr)
            if not is_valid:
                return False, f"Invalid source range: {error}"
    
    # Validate destination ranges (for EGRESS)
    if direction == 'EGRESS' and destination_ranges:
        for cidr in destination_ranges:
            is_valid, error = validate_firewall_cidr(cidr)
            if not is_valid:
                return False, f"Invalid destination range: {error}"
    
    return True, None


def validate_port_spec(port_spec: str) -> bool:
    """
    Validate port specification (single port or range)
    
    Args:
        port_spec: Port string (e.g., "80", "8000-9000")
        
    Returns:
        True if valid
    """
    if '-' in port_spec:
        # Port range
        try:
            start, end = port_spec.split('-')
            start_port = int(start)
            end_port = int(end)
            
            if start_port < 0 or start_port > 65535:
                return False
            if end_port < 0 or end_port > 65535:
                return False
            if start_port > end_port:
                return False
            
            return True
        except (ValueError, AttributeError):
            return False
    else:
        # Single port
        try:
            port = int(port_spec)
            return 0 <= port <= 65535
        except (ValueError, AttributeError):
            return False


def validate_route_config(name: str, dest_range: str, priority: int,
                         next_hop_type: str, next_hop_value: str = None) -> Tuple[bool, Optional[str]]:
    """
    Validate route configuration
    
    Args:
        name: Route name
        dest_range: Destination CIDR
        priority: Priority (0-65535)
        next_hop_type: Type of next hop
        next_hop_value: Next hop value (optional for gateway)
        
    Returns:
        (is_valid, error_message)
    """
    # Validate name
    is_valid, error = validate_resource_name(name, "Route")
    if not is_valid:
        return False, error
    
    # Validate destination range
    is_valid, error = validate_cidr(dest_range)
    if not is_valid:
        return False, f"Invalid destination range: {error}"
    
    # Validate priority
    if not isinstance(priority, int) or priority < 0 or priority > 65535:
        return False, "Priority must be between 0 and 65535"
    
    # Validate next hop type
    valid_types = ['gateway', 'instance', 'ip', 'vpn_tunnel', 'interconnect']
    if next_hop_type not in valid_types:
        return False, f"Next hop type must be one of: {', '.join(valid_types)}"
    
    # Validate next hop value based on type
    if next_hop_type == 'ip' and next_hop_value:
        try:
            import ipaddress
            ipaddress.ip_address(next_hop_value)
        except ValueError:
            return False, f"Invalid IP address for next hop: {next_hop_value}"
    
    return True, None


def validate_network_tags(tags: List[str]) -> Tuple[bool, Optional[str]]:
    """
    Validate network tags
    
    Args:
        tags: List of tag strings
        
    Returns:
        (is_valid, error_message)
    """
    if not tags:
        return True, None
    
    for tag in tags:
        if not tag or len(tag) > 63:
            return False, "Tags must be 1-63 characters"
        
        # Tags can contain lowercase letters, numbers, and hyphens
        if not re.match(r'^[a-z0-9]([-a-z0-9]*[a-z0-9])?$', tag):
            return False, (
                f"Tag '{tag}' must contain only lowercase letters, "
                "numbers, and hyphens"
            )
    
    return True, None
