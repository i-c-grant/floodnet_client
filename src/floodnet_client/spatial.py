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
    
    @staticmethod
    def _deployments_to_gdf(deployments: List[Deployment]) -> gpd.GeoDataFrame:
        """Convert a list of Deployment objects to a GeoDataFrame."""
        return gpd.GeoDataFrame(
            [d.model_dump() for d in deployments],
            geometry=[Point(d.longitude, d.latitude) for d in deployments],
            crs="EPSG:4326"
        )

    def get_deployments_as_gdf(self) -> gpd.GeoDataFrame:
        """Get all deployments as a GeoDataFrame."""
        deployments = super().get_deployments()
        return self._deployments_to_gdf(deployments)

    def _validate_geometry(self, geometry: Union[Polygon, MultiPolygon, gpd.GeoSeries]) -> gpd.GeoSeries:
        """Validate and normalize input geometry.
        
        Args:
            geometry: Input geometry to validate
            
        Returns:
            GeoSeries with valid, simple geometry in EPSG:4326
            
        Raises:
            ValueError: If geometry is invalid type or cannot be made valid
        """
        # Convert to GeoSeries if needed
        if isinstance(geometry, (Polygon, MultiPolygon)):
            geometry = gpd.GeoSeries([geometry], crs="EPSG:4326")
        elif isinstance(geometry, gpd.GeoSeries):
            if len(geometry) == 0:
                raise ValueError("GeoSeries must contain at least one geometry")
        else:
            raise ValueError("geometry must be Polygon, MultiPolygon or GeoSeries")
            
        # Ensure geometry is valid and simple
        valid_geom = make_valid(geometry.iloc[0])
        if not valid_geom.is_valid or not valid_geom.is_simple:
            raise ValueError("Could not create valid, simple geometry")
            
        # Create new GeoSeries and transform to 4326 if needed
        result = gpd.GeoSeries([valid_geom], crs=geometry.crs)
        if result.crs != "EPSG:4326":
            result = result.to_crs("EPSG:4326")
            
        return result

    def get_deployments_within_geometry(
        self, 
        geometry: Union[Polygon, MultiPolygon, gpd.GeoSeries]
    ) -> List[Deployment]:
        """Get deployments within a geometry."""
        bounds = self._validate_geometry(geometry)
            
        # Get deployments and convert to GeoDataFrame
        deployments = super().get_deployments()
        deployments_gdf = self._deployments_to_gdf(deployments)
        
        # Spatial filter
        filtered = deployments_gdf[deployments_gdf.within(bounds.union_all())]
        
        # Get the deployment_ids that fall within the geometry
        deployment_ids = filtered.deployment_id.tolist()
        
        # Return the original Deployment objects that match these IDs
        all_deployments = super().get_deployments()
        return [d for d in all_deployments if d.deployment_id in deployment_ids]
        
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
