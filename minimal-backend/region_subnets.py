"""
Auto-mode VPC subnet generation for GCP regions
"""

# Standard GCP regions with auto-mode CIDR allocations
# In auto-mode, each region gets a /20 subnet from 10.128.0.0/9 block
GCP_REGIONS = [
    {"name": "us-central1", "cidr": "10.128.0.0/20"},
    {"name": "us-east1", "cidr": "10.142.0.0/20"},
    {"name": "us-west1", "cidr": "10.138.0.0/20"},
    {"name": "us-west2", "cidr": "10.168.0.0/20"},
    {"name": "us-west3", "cidr": "10.180.0.0/20"},
    {"name": "us-west4", "cidr": "10.182.0.0/20"},
    {"name": "us-east4", "cidr": "10.150.0.0/20"},
    {"name": "europe-west1", "cidr": "10.132.0.0/20"},
    {"name": "europe-west2", "cidr": "10.154.0.0/20"},
    {"name": "europe-west3", "cidr": "10.156.0.0/20"},
    {"name": "europe-west4", "cidr": "10.164.0.0/20"},
    {"name": "europe-north1", "cidr": "10.166.0.0/20"},
    {"name": "asia-east1", "cidr": "10.140.0.0/20"},
    {"name": "asia-southeast1", "cidr": "10.148.0.0/20"},
    {"name": "asia-northeast1", "cidr": "10.146.0.0/20"},
    {"name": "asia-south1", "cidr": "10.160.0.0/20"},
]

def get_auto_mode_subnets():
    """
    Returns list of subnets that should be auto-created in auto-mode VPCs
    """
    return GCP_REGIONS

def is_auto_mode_cidr(cidr: str) -> bool:
    """
    Check if CIDR is the auto-mode range (10.128.0.0/9)
    """
    return cidr == "10.128.0.0/9"
