"""Simple client for interacting with the FloodNet API.

A lightweight client that uses Pydantic for validation and requests for HTTP.
Provides core functionality for:
- Fetching deployment locations 
- Retrieving time-series depth measurements
- Basic temporal filtering
- Caching of deployment data
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

import requests

from .schemas import Deployment, DeploymentResponse, DepthReading, DepthResponse

logger = logging.getLogger(__name__)

API_BASE: str = "https://api.dev.floodlabs.nyc/api/rest/"
CACHE_EXPIRY = timedelta(days=1)

class FloodNetClient:
    """Lightweight client for fetching FloodNet sensor data"""
    
    def __init__(self):
        self.base_url = API_BASE
        self._deployments_cache: Optional[Tuple[datetime, List[Deployment]]] = None
        
    def get_deployments(self, force_refresh: bool = False) -> List[Deployment]:
        """Get all deployment locations and metadata.
        
        Args:
            force_refresh: If True, bypass cache and fetch fresh data
            
        Returns:
            List of validated Deployment models with processed coordinates
        """
        # Check cache first
        if not force_refresh and self._deployments_cache:
            cache_time, deployments = self._deployments_cache
            if datetime.now() - cache_time < CACHE_EXPIRY:
                logger.debug("Returning cached deployments from %s", cache_time)
                return deployments

        logger.info("Fetching deployment data from API")
        try:
            response = requests.get(f"{self.base_url}deployments/flood")
            response.raise_for_status()
            
            # Parse and validate response directly from JSON
            try:
                data = DeploymentResponse.model_validate_json(response.text)
            except ValueError as e:
                logger.error("Invalid JSON response: %s", str(e))
                raise
            
            # Process coordinates for each deployment
            for deployment in data.deployments:
                deployment.longitude = deployment.location.coordinates[0]
                deployment.latitude = deployment.location.coordinates[1]
                
            logger.info("Processed %d deployment records", len(data.deployments))
            
            # Update cache
            self._deployments_cache = (datetime.now(), data.deployments)
            return data.deployments
            
        except Exception as e:
            logger.error("Error fetching deployments: %s", str(e))
            raise

    def refresh_deployments_cache(self) -> None:
        """Force refresh of the deployments cache."""
        logger.info("Refreshing deployments cache")
        self._deployments_cache = None

    def get_deployment_ids(self) -> List[str]:
        """Get a list of all deployment IDs.
        
        Returns:
            List of deployment IDs
        """
        deployments = self.get_deployments()
        return [d["deployment_id"] for d in deployments]

    def get_depth_data(
        self,
        start_time: datetime,
        end_time: datetime,
        deployment_ids: Optional[List[str]] = None
    ) -> List[DepthReading]:
        """Fetch depth data for specified deployments.
        
        Args:
            start_time: Start of time range
            end_time: End of time range
            deployment_ids: Optional list of specific deployment IDs to query.
                          If None, queries all deployments.
                          
        Returns:
            List of validated DepthReading models
            
        Raises:
            ValueError: If time range is invalid
        """
        # Validate time range
        if start_time >= end_time:
            raise ValueError("start_time must be before end_time")
        
        max_duration = timedelta(days=7)
        if (end_time - start_time) > max_duration: 
            raise ValueError(f"Time range cannot exceed {max_duration}")

        # If no deployment IDs provided, get all deployments
        if deployment_ids is None:
            deployments = self.get_deployments()
            deployment_ids = [d.deployment_id for d in deployments]
            
        logger.info("Fetching depth data for %d deployments", len(deployment_ids))
        
        params = {
            "start_time": start_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "end_time": end_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        }
        
        all_readings = []
        for dep_id in deployment_ids:
            try:
                response = requests.get(
                    f"{self.base_url}deployments/flood/{dep_id}/depth",
                    params=params
                )
                response.raise_for_status()
                
                # Parse raw JSON and filter valid readings
                try:
                    raw_data = response.json()
                    valid_readings = []
                    for reading in raw_data.get("depth_data", []):
                        try:
                            valid_reading = DepthReading.model_validate(reading)
                            valid_readings.append(valid_reading)
                        except ValueError as e:
                            logger.debug("Skipping invalid reading: %s", str(e))
                            continue
                    
                    if len(valid_readings) > 0:
                        logger.info("Got %d valid readings for deployment %s", 
                                  len(valid_readings), dep_id)
                    else:
                        logger.debug("No valid readings for deployment %s", dep_id)
                    all_readings.extend(valid_readings)
                    
                except ValueError as e:
                    logger.error("Invalid JSON response for deployment %s: %s", dep_id, str(e))
                    continue
                
            except Exception as e:
                logger.error("Error querying deployment %s: %s", dep_id, str(e))
                continue
            
        logger.info("Retrieved %d total depth readings from %d deployments", 
                   len(all_readings), len(deployment_ids))
        return all_readings
