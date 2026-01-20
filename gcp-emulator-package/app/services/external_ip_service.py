"""
External IP Pool Service

Manages the pool of external IP addresses for instances.
Handles allocation of ephemeral and static external IPs.
"""

import random
import ipaddress
from app.factory import db
from app.models.vpc import Address


class ExternalIPPoolService:
    """
    Service for managing external IP addresses.
    
    Uses a fake GCP IP range (34.0.0.0 - 34.255.255.255) for emulator purposes.
    In real GCP, external IPs come from Google's public IP pools.
    """
    
    # Fake GCP external IP range for emulator
    EXTERNAL_IP_RANGE_START = "34.0.0.0"
    EXTERNAL_IP_RANGE_END = "34.255.255.255"
    
    @staticmethod
    def generate_random_external_ip():
        """
        Generate a random external IP from the fake GCP range.
        
        Returns:
            str: A random IP address (e.g., "34.123.45.67")
        """
        # Generate random IP in 34.x.x.x range
        octets = [34]  # First octet is always 34
        octets.extend([random.randint(0, 255) for _ in range(3)])
        return '.'.join(map(str, octets))
    
    @staticmethod
    def is_ip_available(ip_address):
        """
        Check if an external IP is available (not allocated).
        
        Args:
            ip_address (str): IP address to check
            
        Returns:
            bool: True if available, False if already allocated
        """
        existing = Address.query.filter_by(address=ip_address).first()
        return existing is None
    
    @staticmethod
    def allocate_ephemeral_ip(project_id, region, network_tier='PREMIUM'):
        """
        Allocate an ephemeral external IP (temporary, auto-assigned).
        
        Ephemeral IPs are not named and are automatically released when
        the instance is stopped or deleted.
        
        Args:
            project_id (str): Project ID
            region (str): Region for the IP
            network_tier (str): PREMIUM or STANDARD
            
        Returns:
            str: The allocated IP address
        """
        max_attempts = 100
        for _ in range(max_attempts):
            ip = ExternalIPPoolService.generate_random_external_ip()
            if ExternalIPPoolService.is_ip_available(ip):
                return ip
        
        raise Exception("Failed to allocate ephemeral IP after 100 attempts")
    
    @staticmethod
    def allocate_static_ip(project_id, region, name, network_tier='PREMIUM', 
                          address=None, description=None):
        """
        Reserve a static external IP address.
        
        Static IPs are named resources that persist until explicitly deleted.
        They can be attached and detached from instances.
        
        Args:
            project_id (str): Project ID
            region (str): Region for the IP
            name (str): Name for the address resource
            network_tier (str): PREMIUM or STANDARD
            address (str, optional): Specific IP to reserve (if available)
            description (str, optional): Description of the address
            
        Returns:
            Address: The created Address model instance
        """
        import uuid
        
        # Check if name already exists in this region
        existing = Address.query.filter_by(
            project_id=project_id,
            region=region,
            name=name
        ).first()
        
        if existing:
            raise ValueError(f"Address '{name}' already exists in region '{region}'")
        
        # Determine IP address
        if address:
            # User specified an IP - check if it's valid and available
            if not ExternalIPPoolService.is_valid_external_ip(address):
                raise ValueError(f"Invalid external IP address: {address}")
            if not ExternalIPPoolService.is_ip_available(address):
                raise ValueError(f"IP address {address} is already in use")
            ip_address = address
        else:
            # Auto-generate available IP
            max_attempts = 100
            for _ in range(max_attempts):
                ip = ExternalIPPoolService.generate_random_external_ip()
                if ExternalIPPoolService.is_ip_available(ip):
                    ip_address = ip
                    break
            else:
                raise Exception("Failed to allocate static IP after 100 attempts")
        
        # Create the Address resource
        address_obj = Address(
            id=uuid.uuid4(),
            name=name,
            project_id=project_id,
            region=region,
            address=ip_address,
            address_type='EXTERNAL',
            status='RESERVED',
            network_tier=network_tier,
            purpose='GCE_ENDPOINT',
            description=description
        )
        
        db.session.add(address_obj)
        db.session.commit()
        
        return address_obj
    
    @staticmethod
    def release_static_ip(address_obj):
        """
        Release a static external IP address.
        
        Args:
            address_obj (Address): The Address model instance to release
            
        Raises:
            ValueError: If the address is currently in use
        """
        if address_obj.status == 'IN_USE':
            raise ValueError(f"Cannot delete address '{address_obj.name}' while it is in use")
        
        db.session.delete(address_obj)
        db.session.commit()
    
    @staticmethod
    def mark_in_use(address_obj, instance_id, network_interface_id):
        """
        Mark an address as IN_USE by an instance.
        
        Args:
            address_obj (Address): The Address to mark
            instance_id (str): ID of the instance using this IP
            network_interface_id (uuid): ID of the network interface
        """
        address_obj.status = 'IN_USE'
        address_obj.user_instance_id = instance_id
        address_obj.user_network_interface_id = network_interface_id
        db.session.commit()
    
    @staticmethod
    def mark_reserved(address_obj):
        """
        Mark an address as RESERVED (not in use).
        
        Args:
            address_obj (Address): The Address to mark
        """
        address_obj.status = 'RESERVED'
        address_obj.user_instance_id = None
        address_obj.user_network_interface_id = None
        db.session.commit()
    
    @staticmethod
    def is_valid_external_ip(ip_address):
        """
        Check if an IP address is valid for external use.
        
        Args:
            ip_address (str): IP address to validate
            
        Returns:
            bool: True if valid external IP format
        """
        try:
            ip = ipaddress.ip_address(ip_address)
            # Check if it's in our emulator range (34.x.x.x)
            return ip_address.startswith('34.')
        except ValueError:
            return False
    
    @staticmethod
    def get_allocated_count(project_id, region=None):
        """
        Get count of allocated IPs for a project/region.
        
        Args:
            project_id (str): Project ID
            region (str, optional): Specific region (None for all regions)
            
        Returns:
            int: Count of allocated addresses
        """
        query = Address.query.filter_by(project_id=project_id)
        if region:
            query = query.filter_by(region=region)
        return query.count()
    
    @staticmethod
    def find_by_ip(ip_address):
        """
        Find an Address by its IP address.
        
        Args:
            ip_address (str): The IP address to find
            
        Returns:
            Address or None: The Address object if found
        """
        return Address.query.filter_by(address=ip_address).first()
