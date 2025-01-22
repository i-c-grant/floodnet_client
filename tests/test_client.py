import pytest
from datetime import datetime, timedelta
from shapely.geometry import box
import geopandas as gpd
from floodnet_client import FloodNetClient, SpatialFloodNetClient

@pytest.fixture
def client():
    return FloodNetClient()

@pytest.fixture
def spatial_client():
    return SpatialFloodNetClient()

def test_get_deployments(client):
    deployments = client.get_deployments()
    assert len(deployments) > 0
    assert all(d.deployment_id for d in deployments)
    assert all(hasattr(d, 'latitude') for d in deployments)
    assert all(hasattr(d, 'longitude') for d in deployments)

def test_get_depth_data(client):
    end = datetime.now()
    start = end - timedelta(hours=1)
    data = client.get_depth_data(start, end)
    assert isinstance(data, list)
    
def test_get_deployments_as_gdf(spatial_client):
    gdf = spatial_client.get_deployments_as_gdf()
    assert isinstance(gdf, gpd.GeoDataFrame)
    assert gdf.crs == "EPSG:4326"
    assert all(gdf.geometry.geom_type == "Point")
    
def test_get_deployments_within_geometry(spatial_client):
    # Create a bounding box around NYC
    bbox = box(-74.5, 40.4, -73.5, 41.0)
    deployments = spatial_client.get_deployments_within_geometry(bbox)
    assert isinstance(deployments, list)
    assert all(d.deployment_id for d in deployments)
    
def test_get_depth_data_within_geometry(spatial_client):
    bbox = box(-74.5, 40.4, -73.5, 41.0)
    end = datetime.now()
    start = end - timedelta(hours=1)
    data = spatial_client.get_depth_data_within_geometry(start, end, bbox)
    assert isinstance(data, list)
