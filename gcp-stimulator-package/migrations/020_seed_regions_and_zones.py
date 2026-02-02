"""
Migration: Seed GCP Regions and Zones

This migration adds standard GCP regions and zones to the database
to enable subnet and VM creation operations.

Fixes: Blocker #2 - Missing regions/zones (29% of test failures)
"""

import psycopg2
import os
from datetime import datetime

# Database connection parameters
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'gcs_emulator')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')

# Standard GCP Regions and Zones
REGIONS_AND_ZONES = {
    'us-central1': {
        'description': 'Council Bluffs, Iowa, North America',
        'zones': ['a', 'b', 'c', 'f']
    },
    'us-east1': {
        'description': 'Moncks Corner, South Carolina, North America',
        'zones': ['b', 'c', 'd']
    },
    'us-east4': {
        'description': 'Ashburn, Northern Virginia, North America',
        'zones': ['a', 'b', 'c']
    },
    'us-west1': {
        'description': 'The Dalles, Oregon, North America',
        'zones': ['a', 'b', 'c']
    },
    'us-west2': {
        'description': 'Los Angeles, California, North America',
        'zones': ['a', 'b', 'c']
    },
    'us-west3': {
        'description': 'Salt Lake City, Utah, North America',
        'zones': ['a', 'b', 'c']
    },
    'us-west4': {
        'description': 'Las Vegas, Nevada, North America',
        'zones': ['a', 'b', 'c']
    },
    'europe-west1': {
        'description': 'St. Ghislain, Belgium, Europe',
        'zones': ['b', 'c', 'd']
    },
    'europe-west2': {
        'description': 'London, England, Europe',
        'zones': ['a', 'b', 'c']
    },
    'europe-west3': {
        'description': 'Frankfurt, Germany, Europe',
        'zones': ['a', 'b', 'c']
    },
    'europe-west4': {
        'description': 'Eemshaven, Netherlands, Europe',
        'zones': ['a', 'b', 'c']
    },
    'asia-east1': {
        'description': 'Changhua County, Taiwan',
        'zones': ['a', 'b', 'c']
    },
    'asia-east2': {
        'description': 'Hong Kong',
        'zones': ['a', 'b', 'c']
    },
    'asia-southeast1': {
        'description': 'Jurong West, Singapore',
        'zones': ['a', 'b', 'c']
    },
    'australia-southeast1': {
        'description': 'Sydney, Australia',
        'zones': ['a', 'b', 'c']
    }
}


def seed_regions_and_zones():
    """Seed regions and zones into the database"""
    try:
        # Connect to database
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        conn.autocommit = False
        cur = conn.cursor()
        
        print("Starting migration: Seed regions and zones")
        print("=" * 60)
        
        # Check if tables exist
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'regions'
            )
        """)
        regions_table_exists = cur.fetchone()[0]
        
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'zones'
            )
        """)
        zones_table_exists = cur.fetchone()[0]
        
        if not regions_table_exists or not zones_table_exists:
            print("ERROR: Required tables do not exist!")
            print(f"Regions table exists: {regions_table_exists}")
            print(f"Zones table exists: {zones_table_exists}")
            return False
        
        # Check current counts
        cur.execute("SELECT COUNT(*) FROM regions")
        existing_regions = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM zones")
        existing_zones = cur.fetchone()[0]
        
        print(f"Existing regions: {existing_regions}")
        print(f"Existing zones: {existing_zones}")
        print()
        
        regions_added = 0
        zones_added = 0
        
        # Insert regions and zones
        for region_name, region_data in REGIONS_AND_ZONES.items():
            # Check if region exists
            cur.execute("SELECT name FROM regions WHERE name = %s", (region_name,))
            existing_region = cur.fetchone()
            
            if not existing_region:
                # Insert region
                cur.execute("""
                    INSERT INTO regions (name, description, status, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    region_name,
                    region_data['description'],
                    'UP',
                    datetime.utcnow(),
                    datetime.utcnow()
                ))
                regions_added += 1
                print(f"✓ Added region: {region_name}")
            else:
                print(f"- Region already exists: {region_name}")
            
            # Insert zones for this region
            for zone_letter in region_data['zones']:
                zone_name = f"{region_name}-{zone_letter}"
                
                # Check if zone exists
                cur.execute("SELECT name FROM zones WHERE name = %s", (zone_name,))
                existing_zone = cur.fetchone()
                
                if not existing_zone:
                    cur.execute("""
                        INSERT INTO zones (name, region, description, status, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        zone_name,
                        region_name,
                        f"{region_data['description']} - Zone {zone_letter.upper()}",
                        'UP',
                        datetime.utcnow(),
                        datetime.utcnow()
                    ))
                    zones_added += 1
                    print(f"  ✓ Added zone: {zone_name}")
        
        # Commit transaction
        conn.commit()
        
        print()
        print("=" * 60)
        print("Migration completed successfully!")
        print(f"Regions added: {regions_added}")
        print(f"Zones added: {zones_added}")
        print()
        
        # Verify final counts
        cur.execute("SELECT COUNT(*) FROM regions")
        total_regions = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM zones")
        total_zones = cur.fetchone()[0]
        
        print(f"Total regions in database: {total_regions}")
        print(f"Total zones in database: {total_zones}")
        
        cur.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"ERROR during migration: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False


if __name__ == '__main__':
    success = seed_regions_and_zones()
    exit(0 if success else 1)
