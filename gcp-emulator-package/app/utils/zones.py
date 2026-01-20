"""
GCP Compute Engine Zones Catalog
Static catalog of available zones
https://cloud.google.com/compute/docs/regions-zones
"""

# Zones organized by region
ZONES = {
    # US regions
    'us-central1-a': {'region': 'us-central1', 'location': 'Iowa, USA'},
    'us-central1-b': {'region': 'us-central1', 'location': 'Iowa, USA'},
    'us-central1-c': {'region': 'us-central1', 'location': 'Iowa, USA'},
    'us-central1-f': {'region': 'us-central1', 'location': 'Iowa, USA'},
    
    'us-east1-b': {'region': 'us-east1', 'location': 'South Carolina, USA'},
    'us-east1-c': {'region': 'us-east1', 'location': 'South Carolina, USA'},
    'us-east1-d': {'region': 'us-east1', 'location': 'South Carolina, USA'},
    
    'us-east4-a': {'region': 'us-east4', 'location': 'Virginia, USA'},
    'us-east4-b': {'region': 'us-east4', 'location': 'Virginia, USA'},
    'us-east4-c': {'region': 'us-east4', 'location': 'Virginia, USA'},
    
    'us-west1-a': {'region': 'us-west1', 'location': 'Oregon, USA'},
    'us-west1-b': {'region': 'us-west1', 'location': 'Oregon, USA'},
    'us-west1-c': {'region': 'us-west1', 'location': 'Oregon, USA'},
    
    'us-west2-a': {'region': 'us-west2', 'location': 'Los Angeles, USA'},
    'us-west2-b': {'region': 'us-west2', 'location': 'Los Angeles, USA'},
    'us-west2-c': {'region': 'us-west2', 'location': 'Los Angeles, USA'},
    
    'us-west3-a': {'region': 'us-west3', 'location': 'Salt Lake City, USA'},
    'us-west3-b': {'region': 'us-west3', 'location': 'Salt Lake City, USA'},
    'us-west3-c': {'region': 'us-west3', 'location': 'Salt Lake City, USA'},
    
    'us-west4-a': {'region': 'us-west4', 'location': 'Las Vegas, USA'},
    'us-west4-b': {'region': 'us-west4', 'location': 'Las Vegas, USA'},
    'us-west4-c': {'region': 'us-west4', 'location': 'Las Vegas, USA'},
    
    # Europe regions
    'europe-west1-b': {'region': 'europe-west1', 'location': 'Belgium'},
    'europe-west1-c': {'region': 'europe-west1', 'location': 'Belgium'},
    'europe-west1-d': {'region': 'europe-west1', 'location': 'Belgium'},
    
    'europe-west2-a': {'region': 'europe-west2', 'location': 'London, UK'},
    'europe-west2-b': {'region': 'europe-west2', 'location': 'London, UK'},
    'europe-west2-c': {'region': 'europe-west2', 'location': 'London, UK'},
    
    'europe-west3-a': {'region': 'europe-west3', 'location': 'Frankfurt, Germany'},
    'europe-west3-b': {'region': 'europe-west3', 'location': 'Frankfurt, Germany'},
    'europe-west3-c': {'region': 'europe-west3', 'location': 'Frankfurt, Germany'},
    
    'europe-west4-a': {'region': 'europe-west4', 'location': 'Netherlands'},
    'europe-west4-b': {'region': 'europe-west4', 'location': 'Netherlands'},
    'europe-west4-c': {'region': 'europe-west4', 'location': 'Netherlands'},
    
    'europe-north1-a': {'region': 'europe-north1', 'location': 'Finland'},
    'europe-north1-b': {'region': 'europe-north1', 'location': 'Finland'},
    'europe-north1-c': {'region': 'europe-north1', 'location': 'Finland'},
    
    # Asia-Pacific regions
    'asia-east1-a': {'region': 'asia-east1', 'location': 'Taiwan'},
    'asia-east1-b': {'region': 'asia-east1', 'location': 'Taiwan'},
    'asia-east1-c': {'region': 'asia-east1', 'location': 'Taiwan'},
    
    'asia-east2-a': {'region': 'asia-east2', 'location': 'Hong Kong'},
    'asia-east2-b': {'region': 'asia-east2', 'location': 'Hong Kong'},
    'asia-east2-c': {'region': 'asia-east2', 'location': 'Hong Kong'},
    
    'asia-northeast1-a': {'region': 'asia-northeast1', 'location': 'Tokyo, Japan'},
    'asia-northeast1-b': {'region': 'asia-northeast1', 'location': 'Tokyo, Japan'},
    'asia-northeast1-c': {'region': 'asia-northeast1', 'location': 'Tokyo, Japan'},
    
    'asia-northeast2-a': {'region': 'asia-northeast2', 'location': 'Osaka, Japan'},
    'asia-northeast2-b': {'region': 'asia-northeast2', 'location': 'Osaka, Japan'},
    'asia-northeast2-c': {'region': 'asia-northeast2', 'location': 'Osaka, Japan'},
    
    'asia-south1-a': {'region': 'asia-south1', 'location': 'Mumbai, India'},
    'asia-south1-b': {'region': 'asia-south1', 'location': 'Mumbai, India'},
    'asia-south1-c': {'region': 'asia-south1', 'location': 'Mumbai, India'},
    
    'asia-southeast1-a': {'region': 'asia-southeast1', 'location': 'Singapore'},
    'asia-southeast1-b': {'region': 'asia-southeast1', 'location': 'Singapore'},
    'asia-southeast1-c': {'region': 'asia-southeast1', 'location': 'Singapore'},
    
    'asia-southeast2-a': {'region': 'asia-southeast2', 'location': 'Jakarta, Indonesia'},
    'asia-southeast2-b': {'region': 'asia-southeast2', 'location': 'Jakarta, Indonesia'},
    'asia-southeast2-c': {'region': 'asia-southeast2', 'location': 'Jakarta, Indonesia'},
    
    # Australia
    'australia-southeast1-a': {'region': 'australia-southeast1', 'location': 'Sydney, Australia'},
    'australia-southeast1-b': {'region': 'australia-southeast1', 'location': 'Sydney, Australia'},
    'australia-southeast1-c': {'region': 'australia-southeast1', 'location': 'Sydney, Australia'},
    
    # South America
    'southamerica-east1-a': {'region': 'southamerica-east1', 'location': 'São Paulo, Brazil'},
    'southamerica-east1-b': {'region': 'southamerica-east1', 'location': 'São Paulo, Brazil'},
    'southamerica-east1-c': {'region': 'southamerica-east1', 'location': 'São Paulo, Brazil'},
    
    # Canada
    'northamerica-northeast1-a': {'region': 'northamerica-northeast1', 'location': 'Montreal, Canada'},
    'northamerica-northeast1-b': {'region': 'northamerica-northeast1', 'location': 'Montreal, Canada'},
    'northamerica-northeast1-c': {'region': 'northamerica-northeast1', 'location': 'Montreal, Canada'},
}


def get_zone_info(zone: str) -> dict:
    """
    Get information for a zone
    
    Args:
        zone: Zone name (e.g., 'us-central1-a')
        
    Returns:
        Dict with region and location keys
        
    Raises:
        ValueError: If zone is invalid
    """
    if zone not in ZONES:
        raise ValueError(f"Invalid zone: {zone}")
    
    return ZONES[zone].copy()


def is_valid_zone(zone: str) -> bool:
    """Check if zone is valid"""
    return zone in ZONES


def list_zones() -> list:
    """Get list of all supported zones"""
    return list(ZONES.keys())


def get_zones_by_region(region: str) -> list:
    """Get all zones in a specific region"""
    return [zone for zone, info in ZONES.items() if info['region'] == region]


def list_regions() -> list:
    """Get list of all unique regions"""
    return sorted(list(set(info['region'] for info in ZONES.values())))


def get_region_from_zone(zone: str) -> str:
    """Extract region from zone name"""
    if zone in ZONES:
        return ZONES[zone]['region']
    # Fallback: extract from zone name pattern
    if '-' in zone:
        parts = zone.rsplit('-', 1)
        return parts[0]
    return 'unknown'
