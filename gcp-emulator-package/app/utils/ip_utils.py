"""
IP Address and CIDR Utilities for VPC

Provides:
- CIDR validation (RFC 1918 private ranges)
- IP allocation from subnet ranges
- Gateway address calculation
- Overlap detection
- IP address validation
"""

import ipaddress
from typing import List, Optional, Tuple


# RFC 1918 Private IP Ranges
RFC_1918_RANGES = [
    ipaddress.ip_network('10.0.0.0/8'),
    ipaddress.ip_network('172.16.0.0/12'),
    ipaddress.ip_network('192.168.0.0/16'),
]


def validate_cidr(cidr: str) -> Tuple[bool, Optional[str]]:
    """
    Validate CIDR notation
    
    Args:
        cidr: CIDR string (e.g., "10.128.0.0/20")
        
    Returns:
        (is_valid, error_message)
    """
    try:
        network = ipaddress.ip_network(cidr, strict=False)
        
        # Check if it's IPv4
        if not isinstance(network, ipaddress.IPv4Network):
            return False, "Only IPv4 networks are supported"
        
        # Check prefix length (must be between 8 and 29 for GCP)
        if network.prefixlen < 8 or network.prefixlen > 29:
            return False, f"Prefix length must be between /8 and /29, got /{network.prefixlen}"
        
        return True, None
        
    except ValueError as e:
        return False, f"Invalid CIDR notation: {str(e)}"


def is_private_range(cidr: str) -> bool:
    """Check if CIDR is in RFC 1918 private range"""
    try:
        network = ipaddress.ip_network(cidr, strict=False)
        return any(network.subnet_of(private) for private in RFC_1918_RANGES)
    except ValueError:
        return False


def calculate_gateway(cidr: str) -> Optional[str]:
    """
    Calculate gateway address (first usable IP in range)
    
    Args:
        cidr: CIDR string
        
    Returns:
        Gateway IP address or None if invalid
    """
    try:
        network = ipaddress.ip_network(cidr, strict=False)
        # Gateway is first IP + 1 (network address + 1)
        gateway = network.network_address + 1
        return str(gateway)
    except (ValueError, IndexError):
        return None


def get_usable_ip_count(cidr: str) -> int:
    """
    Get count of usable IPs in CIDR range
    
    Args:
        cidr: CIDR string
        
    Returns:
        Number of usable IPs (excluding network, gateway, broadcast, GCP reserved)
    """
    try:
        network = ipaddress.ip_network(cidr, strict=False)
        # GCP reserves: network address, 3 IPs (gateway + 2 reserved), broadcast
        # Total reserved = 5 IPs
        total_ips = network.num_addresses
        reserved = 5
        return max(0, total_ips - reserved)
    except ValueError:
        return 0


def cidr_overlaps(cidr1: str, cidr2: str) -> bool:
    """
    Check if two CIDR ranges overlap
    
    Args:
        cidr1: First CIDR string
        cidr2: Second CIDR string
        
    Returns:
        True if ranges overlap
    """
    try:
        net1 = ipaddress.ip_network(cidr1, strict=False)
        net2 = ipaddress.ip_network(cidr2, strict=False)
        return net1.overlaps(net2)
    except ValueError:
        return False


def allocate_ip_from_range(cidr: str, used_ips: List[str]) -> Optional[str]:
    """
    Allocate next available IP from CIDR range
    
    Args:
        cidr: CIDR string
        used_ips: List of already allocated IPs
        
    Returns:
        Next available IP or None if range exhausted
    """
    try:
        network = ipaddress.ip_network(cidr, strict=False)
        used_set = {ipaddress.ip_address(ip) for ip in used_ips}
        
        # Skip first 4 IPs (network, gateway, 2 reserved)
        for ip in list(network.hosts())[3:]:
            if ip not in used_set and ip != network.broadcast_address:
                return str(ip)
        
        return None
    except (ValueError, IndexError):
        return None


def validate_ip_in_range(ip: str, cidr: str) -> bool:
    """
    Check if IP address is within CIDR range
    
    Args:
        ip: IP address string
        cidr: CIDR string
        
    Returns:
        True if IP is in range
    """
    try:
        ip_addr = ipaddress.ip_address(ip)
        network = ipaddress.ip_network(cidr, strict=False)
        return ip_addr in network
    except ValueError:
        return False


def expand_cidr_range(original_cidr: str, new_cidr: str) -> Tuple[bool, Optional[str]]:
    """
    Validate if new CIDR is a valid expansion of original
    
    Args:
        original_cidr: Original CIDR range
        new_cidr: New (expanded) CIDR range
        
    Returns:
        (is_valid, error_message)
    """
    try:
        original_net = ipaddress.ip_network(original_cidr, strict=False)
        new_net = ipaddress.ip_network(new_cidr, strict=False)
        
        # New range must contain original range
        if not original_net.subnet_of(new_net):
            return False, "New CIDR range must contain the original range"
        
        # New prefix must be smaller (larger network)
        if new_net.prefixlen >= original_net.prefixlen:
            return False, "New CIDR range must be larger (smaller prefix length)"
        
        return True, None
        
    except ValueError as e:
        return False, f"Invalid CIDR: {str(e)}"


def get_cidr_info(cidr: str) -> dict:
    """
    Get detailed information about CIDR range
    
    Args:
        cidr: CIDR string
        
    Returns:
        Dictionary with CIDR details
    """
    try:
        network = ipaddress.ip_network(cidr, strict=False)
        
        return {
            'cidr': str(network),
            'network_address': str(network.network_address),
            'broadcast_address': str(network.broadcast_address),
            'netmask': str(network.netmask),
            'prefix_length': network.prefixlen,
            'total_addresses': network.num_addresses,
            'usable_addresses': get_usable_ip_count(cidr),
            'gateway': calculate_gateway(cidr),
            'first_usable': str(list(network.hosts())[3]) if network.num_addresses > 5 else None,
            'last_usable': str(network.broadcast_address - 1),
            'is_private': is_private_range(cidr)
        }
    except (ValueError, IndexError):
        return {}


def suggest_non_overlapping_cidr(existing_cidrs: List[str], prefix_length: int = 20) -> Optional[str]:
    """
    Suggest a non-overlapping CIDR range
    
    Args:
        existing_cidrs: List of existing CIDR ranges
        prefix_length: Desired prefix length for new range
        
    Returns:
        Suggested CIDR or None if no space available
    """
    # Start from 10.128.0.0/20 (GCP default pattern)
    base_network = ipaddress.ip_network('10.128.0.0/9')
    
    existing_networks = []
    for cidr in existing_cidrs:
        try:
            existing_networks.append(ipaddress.ip_network(cidr, strict=False))
        except ValueError:
            continue
    
    # Try to find non-overlapping range
    for subnet in base_network.subnets(new_prefix=prefix_length):
        overlaps = any(subnet.overlaps(existing) for existing in existing_networks)
        if not overlaps:
            return str(subnet)
    
    return None


# Auto-create subnetworks default ranges (matching GCP)
AUTO_SUBNET_RANGES = {
    'us-central1': '10.128.0.0/20',
    'europe-west1': '10.132.0.0/20',
    'us-west1': '10.138.0.0/20',
    'asia-east1': '10.140.0.0/20',
    'us-east1': '10.142.0.0/20',
    'asia-northeast1': '10.146.0.0/20',
    'asia-southeast1': '10.148.0.0/20',
    'us-east4': '10.150.0.0/20',
    'australia-southeast1': '10.152.0.0/20',
    'europe-west2': '10.154.0.0/20',
    'europe-west3': '10.156.0.0/20',
    'southamerica-east1': '10.158.0.0/20',
}


def get_auto_subnet_range(region: str) -> Optional[str]:
    """Get default CIDR range for region in auto mode"""
    return AUTO_SUBNET_RANGES.get(region)
