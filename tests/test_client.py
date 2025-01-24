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

@pytest.fixture
def first_deployment_ids(client):
    deps = client.get_deployments()[0:5]
    return [d.deployment_id for d in deps]

@pytest.fixture
def last_deployment_ids(client):
    deps = client.get_deployments()[-5:]
    return [d.deployment_id for d in deps]

@pytest.fixture
def fake_deployment_ids():
    return ["fake1", "fake2", "fake3"]

@pytest.fixture
def queens_boundary():
    """Fixture for Queens boundary geometry"""
    queens = gpd.read_file("tests/data/test_data.gpkg", layer="queens")
    return queens.geometry.iloc[0]

@pytest.fixture 
def nyc_boundary():
    """Fixture for NYC boundary geometry"""
    nyc = gpd.read_file("tests/data/test_data.gpkg", layer="nyc")
    return nyc.geometry.iloc[0]

def test_get_deployments(client):
    # First call should fetch fresh data
    deployments = client.get_deployments()
    assert len(deployments) > 0
    assert all(d.deployment_id for d in deployments)
    assert all(hasattr(d, 'latitude') for d in deployments)
    assert all(hasattr(d, 'longitude') for d in deployments)

def test_deployments_cache(client):
    # First call should cache
    deployments1 = client.get_deployments()
    
    # Second call should use cache
    deployments2 = client.get_deployments()
    assert deployments1 == deployments2
    
    # Force refresh should get fresh data
    deployments3 = client.get_deployments(force_refresh=True)
    assert deployments1 == deployments3  # Content should match, but fresh fetch
    
    # Clear cache and verify fresh fetch
    client.refresh_deployments_cache()
    deployments4 = client.get_deployments()
    assert deployments1 == deployments4  # Content should match, but fresh fetch

def test_cache_expiry(client, monkeypatch):
    from floodnet_client.client import CACHE_EXPIRY
    
    # Get initial data
    deployments1 = client.get_deployments()
    
    # Mock time to be just before expiry
    class MockDatetime:
        @classmethod
        def now(cls):
            return datetime.now() + CACHE_EXPIRY - timedelta(seconds=1)
    
    monkeypatch.setattr('floodnet_client.client.datetime', MockDatetime)
    deployments2 = client.get_deployments()
    assert deployments1 == deployments2  # Cache should still be valid
    
    # Mock time to be after expiry
    class MockExpiredDatetime:
        @classmethod
        def now(cls):
            return datetime.now() + CACHE_EXPIRY + timedelta(seconds=1)
    
    monkeypatch.setattr('floodnet_client.client.datetime', MockExpiredDatetime)
    deployments3 = client.get_deployments()
    assert deployments1 == deployments3  # Content should match, but fresh fetch
        
def test_get_depth_data(client):
    end = datetime.now()
    start = end - timedelta(hours=.1)
    data = client.get_depth_data(start, end)
    assert isinstance(data, list)
    if data:  # Only check contents if we got data
        for reading in data:
            assert isinstance(reading.depth_proc_mm, float)

def test_get_depth_data_first_deployments(client, first_deployment_ids):
    end = datetime.now()
    start = end - timedelta(hours=.1)
    data = client.get_depth_data(start, end, first_deployment_ids)
    assert isinstance(data, list)
    if data:
        for reading in data:
            assert isinstance(reading.depth_proc_mm, float)
            assert reading.deployment_id in first_deployment_ids

def test_get_depth_data_last_deployments(client, last_deployment_ids):
    end = datetime.now()
    start = end - timedelta(hours=.1)
    data = client.get_depth_data(start, end, last_deployment_ids)
    assert isinstance(data, list)
    if data:
        for reading in data:
            assert isinstance(reading.depth_proc_mm, float)
            assert reading.deployment_id in last_deployment_ids
    
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
    start = end - timedelta(hours=.1)
    data = spatial_client.get_depth_data_within_geometry(start, end, bbox)
    assert isinstance(data, gpd.geodataframe.GeoDataFrame)

def test_invalid_time_range(client):
    """Test that invalid time ranges raise appropriate errors"""
    now = datetime.now()
    with pytest.raises(ValueError):
        # Start after end
        client.get_depth_data(now, now - timedelta(hours=1))
    with pytest.raises(ValueError):
        # Start equals end
        client.get_depth_data(now, now)
    with pytest.raises(ValueError):
        # Duration too long
        client.get_depth_data(now, now + timedelta(days=2))

def test_empty_results(client):
    """Test handling of time ranges with no data"""
    far_future = datetime.now() + timedelta(days=365)
    data = client.get_depth_data(far_future, far_future + timedelta(hours=1))
    assert isinstance(data, list)
    assert len(data) == 0

def test_fake_deployment_ids(client, fake_deployment_ids):
    """Test handling of fake deployment IDs"""
    end = datetime.now()
    start = end - timedelta(hours=.1)
    data = client.get_depth_data(start, end, fake_deployment_ids)
    assert isinstance(data, list)
    assert len(data) == 0  # Should return empty list rather than error

def test_mixed_deployment_ids(client, first_deployment_ids, fake_deployment_ids):
    """Test handling of mixed valid and invalid deployment IDs"""
    end = datetime.now()
    start = end - timedelta(hours=.1)
    
    # Combine real and fake IDs
    mixed_ids = first_deployment_ids + fake_deployment_ids
    data = client.get_depth_data(start, end, mixed_ids)
    
    assert isinstance(data, list)
    # Should only return data for valid IDs
    if data:
        for reading in data:
            assert reading.deployment_id in first_deployment_ids
            assert reading.deployment_id not in fake_deployment_ids

def test_invalid_geometry_types(spatial_client):
    """Test handling of invalid geometry types"""
    # Test invalid types
    with pytest.raises(ValueError):
        spatial_client.get_deployments_within_geometry("not a geometry")
    with pytest.raises(ValueError):
        spatial_client.get_deployments_within_geometry(123)
        
    # Test empty GeoSeries
    with pytest.raises(ValueError):
        spatial_client.get_deployments_within_geometry(gpd.GeoSeries(crs="EPSG:4326"))

def test_large_geometry_returns_all_data(spatial_client, nyc_boundary):
    """Test that large geometries return all deployments and readings"""
    end = datetime.now()
    start = end - timedelta(hours=.1)
    
    # Should return all deployments
    deployments = spatial_client.get_deployments_within_geometry(nyc_boundary)
    assert isinstance(deployments, list)
    assert len(deployments) > 0
    
    # Should return all depth readings
    data = spatial_client.get_depth_data_within_geometry(start, end, nyc_boundary)
    assert isinstance(data, gpd.GeoDataFrame)
    assert len(data) > 0

def test_queens_boundary(spatial_client, queens_boundary):
    """Test spatial queries with Queens boundary"""
    end = datetime.now()
    start = end - timedelta(hours=.1)
    
    # Get deployments
    deployments = spatial_client.get_deployments_within_geometry(queens_boundary)
    assert isinstance(deployments, list)
    
    # Get depth data
    data = spatial_client.get_depth_data_within_geometry(start, end, queens_boundary)
    assert isinstance(data, gpd.GeoDataFrame)

def test_crs_handling(spatial_client, queens_boundary):
    """Test CRS handling in spatial operations"""
    # Get deployments using WGS84 geometry
    deployments_wgs84 = spatial_client.get_deployments_within_geometry(queens_boundary)
    
    # Transform the same geometry to UTM zone 18N (EPSG:32618)
    bbox_utm = gpd.GeoSeries([queens_boundary], crs="EPSG:4326").to_crs("EPSG:32618").iloc[0]
    
    # Get deployments using UTM geometry
    deployments_utm = spatial_client.get_deployments_within_geometry(
        gpd.GeoSeries([bbox_utm], crs="EPSG:32618")
    )
    
    # Both queries should return the same deployments
    assert len(deployments_wgs84) == len(deployments_utm)
    assert {d.deployment_id for d in deployments_wgs84} == {d.deployment_id for d in deployments_utm}
    
    # Verify the CRS of the returned geometry
    gdf = spatial_client.get_deployments_as_gdf()
    assert gdf.crs == "EPSG:4326"
