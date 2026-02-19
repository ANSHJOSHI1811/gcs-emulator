"""Compute Engine — Pydantic request / response models"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class NetworkInterface(BaseModel):
    network: Optional[str] = None
    subnetwork: Optional[str] = None
    networkIP: Optional[str] = None
    accessConfigs: Optional[List[Dict[str, Any]]] = None


class CreateInstanceRequest(BaseModel):
    name: str
    machineType: Optional[str] = "e2-medium"
    zone: Optional[str] = None
    networkInterfaces: Optional[List[Dict[str, Any]]] = None
    disks: Optional[List[Dict[str, Any]]] = None
    tags: Optional[Dict[str, Any]] = None          # {items: [...], fingerprint: "..."}
    metadata: Optional[Dict[str, Any]] = None
    labels: Optional[Dict[str, Any]] = None
    description: Optional[str] = None


class SetTagsRequest(BaseModel):
    items: Optional[List[str]] = []
    fingerprint: Optional[str] = ""


class SetMetadataRequest(BaseModel):
    items: Optional[List[Dict[str, str]]] = []    # [{key, value}, ...]
    fingerprint: Optional[str] = ""


class CreateAddressRequest(BaseModel):
    name: str
    description: Optional[str] = None
    addressType: Optional[str] = "EXTERNAL"       # EXTERNAL | INTERNAL
    address: Optional[str] = None                 # user-specified IP (optional)
    subnetwork: Optional[str] = None


class CreateDiskRequest(BaseModel):
    name: str
    sizeGb: Optional[int] = 10
    type: Optional[str] = "pd-standard"           # pd-standard | pd-ssd | pd-balanced
    sourceImage: Optional[str] = None
    description: Optional[str] = None
    labels: Optional[Dict[str, str]] = None


class AttachDiskRequest(BaseModel):
    source: str                                   # disk selfLink or name
    deviceName: Optional[str] = None
    mode: Optional[str] = "READ_WRITE"            # READ_WRITE | READ_ONLY
    boot: Optional[bool] = False
    autoDelete: Optional[bool] = True
