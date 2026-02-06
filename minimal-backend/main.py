"""Main FastAPI application"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import compute, projects, vpc, storage, iam, firewall
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
app.include_router(projects.router, prefix="/cloudresourcemanager/v1", tags=["Projects"])
app.include_router(iam.router, prefix="/v1", tags=["IAM & Admin"])

# Cloud Storage (in-memory implementation)
app.include_router(storage.router, tags=["Cloud Storage"])

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    print(f"""
    ╔══════════════════════════════════════════════════════╗
    ║  🚀 GCP STIMULATOR BACKEND                          ║
    ║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
    ║  📍 http://0.0.0.0:{port}                           ║
    ║  📖 Docs: http://0.0.0.0:{port}/docs                ║
    ║  💾 Database: RDS PostgreSQL                        ║
    ║  🐳 Docker: Local daemon                            ║
    ╚══════════════════════════════════════════════════════╝
    """)
    uvicorn.run(app, host="0.0.0.0", port=port)
