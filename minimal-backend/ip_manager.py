"""IP address management utilities for CIDR/subnet operations"""
import ipaddress
from typing import Optional, List

def validate_cidr(cidr: str) -> bool:
    """Validate CIDR format (e.g., 10.0.0.0/24)"""
    try:
        ipaddress.ip_network(cidr, strict=False)
        return True
    except ValueError:
        return False

def subnet_within_vpc(vpc_cidr: str, subnet_cidr: str) -> bool:
    """Check if subnet CIDR is within VPC CIDR"""
    try:
        vpc = ipaddress.ip_network(vpc_cidr, strict=False)
        subnet = ipaddress.ip_network(subnet_cidr, strict=False)
        return subnet.subnet_of(vpc)
    except ValueError:
        return False

def get_gateway_ip(cidr: str) -> str:
    """Get first usable IP (gateway) from CIDR"""
    network = ipaddress.ip_network(cidr, strict=False)
    return str(list(network.hosts())[0])

def get_ip_at_offset(cidr: str, offset: int) -> Optional[str]:
    """Get IP at specific offset in CIDR range
    
    Args:
        cidr: Network CIDR (e.g., "10.0.1.0/24")
        offset: Index in host list (0 = gateway, 1 = first allocatable, etc.)
    
    Returns:
        IP address string or None if offset exceeds range
    """
    try:
        network = ipaddress.ip_network(cidr, strict=False)
        hosts = list(network.hosts())
        if offset < len(hosts):
            return str(hosts[offset])
        return None
    except (ValueError, IndexError):
        return None

def ip_in_range(ip: str, cidr: str) -> bool:
    """Check if IP is in CIDR range"""
    try:
        network = ipaddress.ip_network(cidr, strict=False)
        ip_addr = ipaddress.ip_address(ip)
        return ip_addr in network
    except ValueError:
        return False

def get_usable_ip_count(cidr: str) -> int:
    """Get number of usable host IPs in CIDR range"""
    try:
        network = ipaddress.ip_network(cidr, strict=False)
        return network.num_addresses - 2  # Exclude network and broadcast
    except ValueError:
        return 0

def cidr_to_netmask(cidr: str) -> str:
    """Convert CIDR to netmask (e.g., /24 -> 255.255.255.0)"""
    try:
        network = ipaddress.ip_network(cidr, strict=False)
        return str(network.netmask)
    except ValueError:
        return ""

if __name__ == "__main__":
    # Self-test
    print("Testing IP Manager...")
    
    assert validate_cidr("10.0.0.0/24") == True
    assert validate_cidr("invalid") == False
    print("✓ validate_cidr")
    
    assert get_gateway_ip("10.0.1.0/24") == "10.0.1.1"
    print("✓ get_gateway_ip")
    
    assert get_ip_at_offset("10.0.1.0/24", 0) == "10.0.1.1"
    assert get_ip_at_offset("10.0.1.0/24", 1) == "10.0.1.2"
    assert get_ip_at_offset("10.0.1.0/24", 2) == "10.0.1.3"
    print("✓ get_ip_at_offset")
    
    assert subnet_within_vpc("10.0.0.0/16", "10.0.1.0/24") == True
    assert subnet_within_vpc("10.0.0.0/16", "192.168.0.0/24") == False
    print("✓ subnet_within_vpc")
    
    assert ip_in_range("10.0.1.5", "10.0.1.0/24") == True
    assert ip_in_range("10.0.2.5", "10.0.1.0/24") == False
    print("✓ ip_in_range")
    
    assert get_usable_ip_count("10.0.1.0/24") == 254
    print("✓ get_usable_ip_count")
    
    assert cidr_to_netmask("10.0.1.0/24") == "255.255.255.0"
    print("✓ cidr_to_netmask")
    
    print("\n✅ All IP manager tests passed!")
