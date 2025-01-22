"""Spatial extensions for the FloodNet client."""
from typing import List, Union
from datetime import datetime
import geopandas as gpd
from shapely.geometry import Point, Polygon, MultiPolygon

from .client import FloodNetClient
from .schemas import Deployment, DepthReading

class SpatialFloodNetClient(FloodNetClient):
    """A FloodNet client with spatial querying capabilities.
    
    Extends the base FloodNetClient with methods for spatial operations and GeoDataFrame conversions.
    """
    
    def get_deployments_as_gdf(self) -> gpd.GeoDataFrame:
        """Get deployments as a GeoDataFrame."""
        deployments = super().get_deployments()
        return gpd.GeoDataFrame(
            [d.model_dump() for d in deployments],
            geometry=[Point(d.longitude, d.latitude) for d in deployments],
            crs="EPSG:4326"
        )
        
    def get_deployments_within_geometry(
        self, 
        geometry: Union[Polygon, MultiPolygon, gpd.GeoSeries]
    ) -> List[Deployment]:
        """Get deployments within a geometry."""
        # Convert input geometry to GeoSeries if needed
        if isinstance(geometry, (Polygon, MultiPolygon)):
            bounds = gpd.GeoSeries([geometry], crs="EPSG:4326")
        elif isinstance(geometry, gpd.GeoSeries):
            bounds = geometry
        else:
            raise ValueError("geometry must be Polygon, MultiPolygon or GeoSeries")
            
        # Get all deployments as GeoDataFrame
        deployments_gdf = self.get_deployments_as_gdf()
        
        # Spatial filter
        filtered = deployments_gdf[deployments_gdf.within(bounds.unary_union)]
        
        # Convert back to Deployment models
        return [
            Deployment(
                deployment_id=row.deployment_id,
                name=row.name,
                date_deployed=row.date_deployed,
                date_down=row.date_down,
                deploy_type=row.deploy_type,
                location=row.location,
                image=row.image,
                sensor_mount=row.sensor_mount,
                mounted_over=row.mounted_over,
                sensor_status=row.sensor_status,
                longitude=row.geometry.x,
                latitude=row.geometry.y
            )
            for _, row in filtered.iterrows()
        ]
        
    def get_depth_data_within_geometry(
        self,
        start_time: datetime,
        end_time: datetime,
        geometry: Union[Polygon, MultiPolygon, gpd.GeoSeries]
    ) -> List[DepthReading]:
        """Get depth readings for deployments within a geometry."""
        # Get spatially filtered deployments
        deployments = self.get_deployments_within_geometry(geometry)
        deployment_ids = [d.deployment_id for d in deployments]
            
        return super().get_depth_data(
            start_time=start_time,
            end_time=end_time,
            deployment_ids=deployment_ids
        )
