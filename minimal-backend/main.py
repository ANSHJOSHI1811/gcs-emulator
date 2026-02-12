"""Main FastAPI application"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import compute, projects, vpc, storage, iam, firewall, routes, peering
import os

app = FastAPI(
    title="GCP Stimulator",
    description="Minimal GCP API simulator with Docker integration",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "GCP Stimulator API", "version": "1.0.0"}

@app.get("/health")
def health():
    return {"status": "healthy"}

# Register routers with GCP API paths
app.include_router(compute.router, prefix="/compute/v1", tags=["Compute Engine"])
app.include_router(vpc.router, prefix="/compute/v1", tags=["VPC Networks"])
app.include_router(firewall.router, prefix="/compute/v1", tags=["Firewall Rules"])
app.include_router(peering.router, prefix="", tags=["VPC Peering"])
app.include_router(routes.router, tags=["VPC Routes"])
app.include_router(projects.router, prefix="/cloudresourcemanager/v1", tags=["Projects"])
app.include_router(iam.router, prefix="/v1", tags=["IAM & Admin"])

# Cloud Storage (in-memory implementation)
app.include_router(storage.router, tags=["Cloud Storage"])


def init_zones_and_machine_types(db):
    """Initialize zones and machine types if they don't exist"""
    from database import Zone, MachineType
    
    # Check if zones already exist
    if db.query(Zone).count() > 0:
        return
    
    # Define zones
    zones_data = [
        {"id": "us-central1-a", "name": "us-central1-a", "region": "us-central1", "status": "UP", "description": "us-central1-a"},
        {"id": "us-central1-b", "name": "us-central1-b", "region": "us-central1", "status": "UP", "description": "us-central1-b"},
        {"id": "us-central1-c", "name": "us-central1-c", "region": "us-central1", "status": "UP", "description": "us-central1-c"},
        {"id": "us-east1-b", "name": "us-east1-b", "region": "us-east1", "status": "UP", "description": "us-east1-b"},
        {"id": "us-east1-c", "name": "us-east1-c", "region": "us-east1", "status": "UP", "description": "us-east1-c"},
        {"id": "us-west1-a", "name": "us-west1-a", "region": "us-west1", "status": "UP", "description": "us-west1-a"},
        {"id": "us-west1-b", "name": "us-west1-b", "region": "us-west1", "status": "UP", "description": "us-west1-b"},
    ]
    
    # Define machine types (common types across zones)
    machine_types_data = [
        {"id": "e2-micro", "name": "e2-micro", "guest_cpus": 2, "memory_mb": 1024, "description": "2 vCPU, 1 GB RAM"},
        {"id": "e2-small", "name": "e2-small", "guest_cpus": 2, "memory_mb": 2048, "description": "2 vCPU, 2 GB RAM"},
        {"id": "e2-medium", "name": "e2-medium", "guest_cpus": 2, "memory_mb": 4096, "description": "2 vCPU, 4 GB RAM"},
        {"id": "n1-standard-1", "name": "n1-standard-1", "guest_cpus": 1, "memory_mb": 3840, "description": "1 vCPU, 3.75 GB RAM"},
        {"id": "n1-standard-2", "name": "n1-standard-2", "guest_cpus": 2, "memory_mb": 7680, "description": "2 vCPU, 7.5 GB RAM"},
        {"id": "n1-standard-4", "name": "n1-standard-4", "guest_cpus": 4, "memory_mb": 15360, "description": "4 vCPU, 15 GB RAM"},
    ]
    
    # Add zones
    for zone_data in zones_data:
        zone = Zone(**zone_data)
        db.add(zone)
    
    # Add machine types for each zone
    for zone_data in zones_data:
        for mt_data in machine_types_data:
            mt = MachineType(
                id=f"{zone_data['name']}-{mt_data['name']}",
                name=mt_data['name'],
                zone=zone_data['name'],
                guest_cpus=mt_data['guest_cpus'],
                memory_mb=mt_data['memory_mb'],
                description=mt_data.get('description')
            )
            db.add(mt)
    
    db.commit()
    print(f"✅ Initialized {len(zones_data)} zones and {len(zones_data) * len(machine_types_data)} machine types")


@app.on_event("startup")
async def startup_event():
    """Initialize database tables and default networks"""
    from database import SessionLocal, Project, Base, engine
    from api.vpc import ensure_default_network
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Initialize zones and machine types
        init_zones_and_machine_types(db)
        
        # Initialize default networks for projects
        projects = db.query(Project).all()
        for project in projects:
            ensure_default_network(db, project.id)
        print(f"✅ Initialized default networks for {len(projects)} projects")
    except Exception as e:
        print(f"⚠️  Error initializing: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    print(f"""
    ╔══════════════════════════════════════════════════════╗
    ║  🚀 GCP STIMULATOR BACKEND                          ║
    ║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
    ║  📍 http://0.0.0.0:{port}                           ║
    ║  📖 Docs: http://0.0.0.0:{port}/docs                ║
    ║  💾 Database: SQLite Local                          ║
    ║  🐳 Docker: Local daemon                            ║
    ╚══════════════════════════════════════════════════════╝
    """)
    uvicorn.run(app, host="0.0.0.0", port=port)
