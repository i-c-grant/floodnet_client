import pytest
from datetime import datetime, timedelta
from floodnet_client import FloodNetClient

@pytest.fixture
def client():
    return FloodNetClient()

def test_get_deployments(client):
    deployments = client.get_deployments()
    assert len(deployments) > 0
    assert all(d.deployment_id for d in deployments)

def test_get_depth_data(client):
    end = datetime.now()
    start = end - timedelta(hours=1)
    data = client.get_depth_data(start, end)
    assert isinstance(data, list)
