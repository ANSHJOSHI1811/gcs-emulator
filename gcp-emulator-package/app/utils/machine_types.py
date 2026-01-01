"""
GCP Compute Engine Machine Types Catalog
Static catalog of machine types with their specifications
https://cloud.google.com/compute/docs/machine-types
"""

# Machine type specifications: (CPUs, Memory in MB)
MACHINE_TYPES = {
    # E2 series (cost-optimized)
    'e2-micro': {'cpus': 2, 'memory_mb': 1024, 'shared_cpu': True},
    'e2-small': {'cpus': 2, 'memory_mb': 2048, 'shared_cpu': True},
    'e2-medium': {'cpus': 2, 'memory_mb': 4096, 'shared_cpu': True},
    'e2-standard-2': {'cpus': 2, 'memory_mb': 8192, 'shared_cpu': False},
    'e2-standard-4': {'cpus': 4, 'memory_mb': 16384, 'shared_cpu': False},
    'e2-standard-8': {'cpus': 8, 'memory_mb': 32768, 'shared_cpu': False},
    'e2-standard-16': {'cpus': 16, 'memory_mb': 65536, 'shared_cpu': False},
    
    # N1 series (general purpose)
    'n1-standard-1': {'cpus': 1, 'memory_mb': 3840, 'shared_cpu': False},
    'n1-standard-2': {'cpus': 2, 'memory_mb': 7680, 'shared_cpu': False},
    'n1-standard-4': {'cpus': 4, 'memory_mb': 15360, 'shared_cpu': False},
    'n1-standard-8': {'cpus': 8, 'memory_mb': 30720, 'shared_cpu': False},
    'n1-standard-16': {'cpus': 16, 'memory_mb': 61440, 'shared_cpu': False},
    'n1-standard-32': {'cpus': 32, 'memory_mb': 122880, 'shared_cpu': False},
    
    # N1 high-memory
    'n1-highmem-2': {'cpus': 2, 'memory_mb': 13312, 'shared_cpu': False},
    'n1-highmem-4': {'cpus': 4, 'memory_mb': 26624, 'shared_cpu': False},
    'n1-highmem-8': {'cpus': 8, 'memory_mb': 53248, 'shared_cpu': False},
    'n1-highmem-16': {'cpus': 16, 'memory_mb': 106496, 'shared_cpu': False},
    
    # N1 high-cpu
    'n1-highcpu-2': {'cpus': 2, 'memory_mb': 1843, 'shared_cpu': False},
    'n1-highcpu-4': {'cpus': 4, 'memory_mb': 3686, 'shared_cpu': False},
    'n1-highcpu-8': {'cpus': 8, 'memory_mb': 7373, 'shared_cpu': False},
    'n1-highcpu-16': {'cpus': 16, 'memory_mb': 14746, 'shared_cpu': False},
    
    # N2 series (balanced price/performance)
    'n2-standard-2': {'cpus': 2, 'memory_mb': 8192, 'shared_cpu': False},
    'n2-standard-4': {'cpus': 4, 'memory_mb': 16384, 'shared_cpu': False},
    'n2-standard-8': {'cpus': 8, 'memory_mb': 32768, 'shared_cpu': False},
    'n2-standard-16': {'cpus': 16, 'memory_mb': 65536, 'shared_cpu': False},
    'n2-standard-32': {'cpus': 32, 'memory_mb': 131072, 'shared_cpu': False},
    
    # N2D series (AMD)
    'n2d-standard-2': {'cpus': 2, 'memory_mb': 8192, 'shared_cpu': False},
    'n2d-standard-4': {'cpus': 4, 'memory_mb': 16384, 'shared_cpu': False},
    'n2d-standard-8': {'cpus': 8, 'memory_mb': 32768, 'shared_cpu': False},
    'n2d-standard-16': {'cpus': 16, 'memory_mb': 65536, 'shared_cpu': False},
    
    # C2 series (compute-optimized)
    'c2-standard-4': {'cpus': 4, 'memory_mb': 16384, 'shared_cpu': False},
    'c2-standard-8': {'cpus': 8, 'memory_mb': 32768, 'shared_cpu': False},
    'c2-standard-16': {'cpus': 16, 'memory_mb': 65536, 'shared_cpu': False},
    'c2-standard-30': {'cpus': 30, 'memory_mb': 122880, 'shared_cpu': False},
}


def get_machine_type_specs(machine_type: str) -> dict:
    """
    Get specifications for a machine type
    
    Args:
        machine_type: Machine type name (e.g., 'e2-micro')
        
    Returns:
        Dict with cpus, memory_mb, shared_cpu keys
        
    Raises:
        ValueError: If machine type is invalid
    """
    if machine_type not in MACHINE_TYPES:
        raise ValueError(f"Invalid machine type: {machine_type}")
    
    return MACHINE_TYPES[machine_type].copy()


def is_valid_machine_type(machine_type: str) -> bool:
    """Check if machine type is valid"""
    return machine_type in MACHINE_TYPES


def list_machine_types() -> list:
    """Get list of all supported machine types"""
    return list(MACHINE_TYPES.keys())


def get_machine_type_series(machine_type: str) -> str:
    """Get the series name for a machine type (e.g., 'e2', 'n1')"""
    if '-' in machine_type:
        return machine_type.split('-')[0]
    return 'unknown'
