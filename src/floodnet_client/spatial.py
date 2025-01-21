"""Spatial extensions for the FloodNet client."""

"""Spatial extensions for the FloodNet client."""
from typing import List, Union, TYPE_CHECKING
from datetime import datetime

try:
    import geopandas as gpd
    from shapely.geometry import Point, Polygon, MultiPolygon
    from shapely.geometry.base import BaseGeometry
    SPATIAL_AVAILABLE = True
except ImportError:
    SPATIAL_AVAILABLE = False

from .client import FloodNetClient
from .schemas import Deployment, DepthReading

if TYPE_CHECKING:
    # Type hints for static type checkers, doesn't affect runtime
    import geopandas as gpd
    from shapely.geometry import Polygon, MultiPolygon

class SpatialFloodNetClient:
    """A spatial-aware decorator for FloodNetClient.
    
    This class wraps a FloodNetClient instance and adds spatial querying capabilities
    while maintaining the same basic interface.
    """
    
    def __init__(self, client: FloodNetClient):
        if not SPATIAL_AVAILABLE:
            raise ImportError(
                "Spatial dependencies not installed. "
                "Please install them with: conda env create -f spatial_env.yml"
            )
        self._client = client
        
    def get_deployments(self) -> gpd.GeoDataFrame:
        """Get deployments as a GeoDataFrame."""
        deployments = self._client.get_deployments()
        return gpd.GeoDataFrame(
            [d.model_dump() for d in deployments],
            geometry=[Point(d.longitude, d.latitude) for d in deployments],
            crs="EPSG:4326"
        )
        
    def get_deployments_within(
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
        deployments_gdf = self.get_deployments()
        
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
        
    def get_depth_data(
        self,
        start_time: datetime,
        end_time: datetime,
        geometry: Union[Polygon, MultiPolygon, gpd.GeoSeries] = None
    ) -> List[DepthReading]:
        """Get depth readings for deployments, optionally filtered by geometry."""
        if geometry is not None:
            # Get spatially filtered deployments
            deployments = self.get_deployments_within(geometry)
            deployment_ids = [d.deployment_id for d in deployments]
        else:
            deployment_ids = None
            
        return self._client.get_depth_data(
            start_time=start_time,
            end_time=end_time,
            deployment_ids=deployment_ids
        )
