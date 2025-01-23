"""Spatial extension for the FloodNet client."""
import logging
from typing import List, Union, Optional
from datetime import datetime, timedelta
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, Polygon, MultiPolygon
from shapely.validation import make_valid

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
        
        # Return the Deployment objects that match these IDs
        return [d for d in deployments if d.deployment_id in deployment_ids]
        
    def get_depth_data_within_geometry(
        self,
        start_time: datetime,
        end_time: datetime,
        geometry: Union[Polygon, MultiPolygon, gpd.GeoSeries]
    ) -> gpd.GeoDataFrame:
        """Get depth readings as a GeoDataFrame for deployments within a geometry."""
        logger = logging.getLogger(__name__)
        
        # Validate geometry first
        bounds = self._validate_geometry(geometry)
        logger.debug("Validated geometry bounds: %s", bounds.total_bounds)
        
        # Get spatially filtered deployments
        deployments = self.get_deployments_within_geometry(bounds)
        deployment_ids = [d.deployment_id for d in deployments]
        logger.info("Found %d deployments within geometry", len(deployment_ids))
        
        # Get depth readings
        logger.info("Querying depth data from %s to %s", start_time, end_time)
        readings = super().get_depth_data(
            start_time=start_time,
            end_time=end_time,
            deployment_ids=deployment_ids
        )
        
        # Convert deployments to GeoDataFrame
        gdf = self._deployments_to_gdf(deployments)

        # Create pandas DataFrame for readings
        readings_data = [{
            'deployment_id': r.deployment_id,
            'time': r.time,
            'depth_mm': r.depth_proc_mm
        } for r in readings]
        
        readings_df = pd.DataFrame(readings_data)
        logger.debug("Processed %d total readings", len(readings_df))

        # Merge readings with deployment locations GeoDataFrame
        result = gdf[['deployment_id', 'geometry']].merge(
            readings_df,
            on='deployment_id', 
            how='right' # to drop deployments with no readings in time window
        )
        
        logger.info("Returning %d readings from %d deployments", 
                   len(result), result.deployment_id.nunique())
        return result
