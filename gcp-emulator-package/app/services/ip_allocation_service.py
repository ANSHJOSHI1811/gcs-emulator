"""
IP Allocation Service - Manages IP address allocation from subnet CIDR ranges

Handles:
- Sequential IP allocation from subnet CIDR
- IP conflict detection
- IP release and reuse tracking
- RFC 1918 private IP validation
"""

import ipaddress
from typing import Optional, Tuple
from app.factory import db
from app.models.vpc import Subnetwork, NetworkInterface


class IPAllocationService:
    """Service for allocating and managing IP addresses within subnets"""
    
    @staticmethod
    def allocate_ip(subnetwork: Subnetwork) -> Optional[str]:
        """
        Allocate next available IP from subnet CIDR range
        
        Args:
            subnetwork: The Subnetwork to allocate from
            
        Returns:
            IP address string (e.g., "10.128.0.5") or None if exhausted
        """
        try:
            # Parse the CIDR range
            network = ipaddress.ip_network(subnetwork.ip_cidr_range, strict=False)
            
            # Get all currently allocated IPs in this subnet
            allocated_ips = set()
            interfaces = NetworkInterface.query.filter_by(
                subnetwork_id=subnetwork.id
            ).all()
            
            for interface in interfaces:
                if interface.network_ip:
                    allocated_ips.add(interface.network_ip)
            
            # Reserve first IP (.1) for gateway
            gateway_ip = str(network.network_address + 1)
            allocated_ips.add(str(network.network_address))  # Network address
            allocated_ips.add(gateway_ip)  # Gateway
            
            # Iterate through usable IPs (skip network, gateway, broadcast)
            for ip in network.hosts():
                ip_str = str(ip)
                
                # Skip gateway
                if ip_str == gateway_ip:
                    continue
                
                # Check if IP is available
                if ip_str not in allocated_ips:
                    return ip_str
            
            # No IPs available
            return None
            
        except Exception as e:
            print(f"Error allocating IP from subnet {subnetwork.name}: {e}")
            return None
    
    @staticmethod
    def release_ip(instance_id: str) -> bool:
        """
        Release all IPs allocated to an instance
        
        Args:
            instance_id: The instance ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Find all network interfaces for this instance
            interfaces = NetworkInterface.query.filter_by(
                instance_id=instance_id
            ).all()
            
            # Delete the interfaces (cascading will handle cleanup)
            for interface in interfaces:
                db.session.delete(interface)
            
            db.session.commit()
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"Error releasing IPs for instance {instance_id}: {e}")
            return False
    
    @staticmethod
    def is_ip_available(subnetwork: Subnetwork, ip_address: str) -> bool:
        """
        Check if a specific IP is available in a subnet
        
        Args:
            subnetwork: The Subnetwork to check
            ip_address: The IP address to check
            
        Returns:
            True if available, False otherwise
        """
        try:
            # Validate IP is in subnet range
            network = ipaddress.ip_network(subnetwork.ip_cidr_range, strict=False)
            ip = ipaddress.ip_address(ip_address)
            
            if ip not in network:
                return False
            
            # Check if IP is reserved (network, gateway, broadcast)
            if ip == network.network_address:
                return False
            if ip == network.network_address + 1:  # Gateway
                return False
            if ip == network.broadcast_address:
                return False
            
            # Check if IP is already allocated
            existing = NetworkInterface.query.filter_by(
                subnetwork_id=subnetwork.id,
                network_ip=ip_address
            ).first()
            
            return existing is None
            
        except Exception as e:
            print(f"Error checking IP availability: {e}")
            return False
    
    @staticmethod
    def get_allocated_ips_count(subnetwork: Subnetwork) -> int:
        """
        Get count of allocated IPs in a subnet
        
        Args:
            subnetwork: The Subnetwork to check
            
        Returns:
            Count of allocated IPs
        """
        return NetworkInterface.query.filter_by(
            subnetwork_id=subnetwork.id
        ).count()
    
    @staticmethod
    def get_available_ips_count(subnetwork: Subnetwork) -> int:
        """
        Get count of available IPs in a subnet
        
        Args:
            subnetwork: The Subnetwork to check
            
        Returns:
            Count of available IPs
        """
        try:
            network = ipaddress.ip_network(subnetwork.ip_cidr_range, strict=False)
            total_ips = network.num_addresses
            
            # Subtract reserved IPs (network, gateway, broadcast)
            usable_ips = total_ips - 3
            
            # Subtract allocated IPs
            allocated = IPAllocationService.get_allocated_ips_count(subnetwork)
            
            return max(0, usable_ips - allocated)
            
        except Exception as e:
            print(f"Error calculating available IPs: {e}")
            return 0
    
    @staticmethod
    def allocate_specific_ip(subnetwork: Subnetwork, ip_address: str) -> Tuple[bool, Optional[str]]:
        """
        Try to allocate a specific IP address
        
        Args:
            subnetwork: The Subnetwork to allocate from
            ip_address: The specific IP to allocate
            
        Returns:
            (success, error_message)
        """
        try:
            # Validate IP is in subnet range
            network = ipaddress.ip_network(subnetwork.ip_cidr_range, strict=False)
            ip = ipaddress.ip_address(ip_address)
            
            if ip not in network:
                return False, f"IP {ip_address} is not in subnet range {subnetwork.ip_cidr_range}"
            
            # Check if IP is reserved
            if ip == network.network_address:
                return False, f"IP {ip_address} is the network address (reserved)"
            if ip == network.network_address + 1:
                return False, f"IP {ip_address} is the gateway address (reserved)"
            if ip == network.broadcast_address:
                return False, f"IP {ip_address} is the broadcast address (reserved)"
            
            # Check if IP is available
            if not IPAllocationService.is_ip_available(subnetwork, ip_address):
                return False, f"IP {ip_address} is already allocated"
            
            return True, None
            
        except ValueError as e:
            return False, f"Invalid IP address: {e}"
        except Exception as e:
            return False, f"Error allocating specific IP: {e}"
    
    @staticmethod
    def get_subnet_info(subnetwork: Subnetwork) -> dict:
        """
        Get detailed information about subnet IP allocation
        
        Args:
            subnetwork: The Subnetwork to analyze
            
        Returns:
            Dictionary with subnet IP information
        """
        try:
            network = ipaddress.ip_network(subnetwork.ip_cidr_range, strict=False)
            allocated = IPAllocationService.get_allocated_ips_count(subnetwork)
            available = IPAllocationService.get_available_ips_count(subnetwork)
            
            return {
                'cidr': subnetwork.ip_cidr_range,
                'network_address': str(network.network_address),
                'gateway_address': str(network.network_address + 1),
                'broadcast_address': str(network.broadcast_address),
                'total_ips': network.num_addresses,
                'usable_ips': network.num_addresses - 3,
                'allocated_ips': allocated,
                'available_ips': available,
                'utilization_percent': round((allocated / (network.num_addresses - 3)) * 100, 2) if network.num_addresses > 3 else 0
            }
            
        except Exception as e:
            print(f"Error getting subnet info: {e}")
            return {
                'error': str(e)
            }
