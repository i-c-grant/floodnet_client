"""Pydantic models for FloodNet API data structures."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

class CRSProperties(BaseModel):
    name: str

class CRS(BaseModel):
    type: str
    properties: CRSProperties

class Location(BaseModel):
    type: str
    crs: CRS
    coordinates: List[float] = Field(..., min_items=2, max_items=2)

class Deployment(BaseModel):
    deployment_id: str
    name: str
    date_deployed: datetime
    date_down: datetime | None
    deploy_type: str
    location: Location
    image: str | None = None
    sensor_mount: str
    mounted_over: str
    sensor_status: str
    longitude: Optional[float] = None  # Added after processing
    latitude: Optional[float] = None   # Added after processing

class DepthReading(BaseModel):
    deployment_id: str
    time: datetime  # Pydantic will convert string to datetime
    depth_proc_mm: float

class DepthResponse(BaseModel):
    depth_data: List[DepthReading]

class DeploymentResponse(BaseModel):
    deployments: List[Deployment]
