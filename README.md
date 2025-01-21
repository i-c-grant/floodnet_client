# FloodNet Client

A simple Python client for the NYC FloodNet sensor network.

## Installation

Basic installation:
```pip install floodnet-client```

With spatial features:
```pip install floodnet-client[spatial]```

## Usage

```python
from floodnet_client import FloodNetClient

# Create client
client = FloodNetClient()

# Get all deployments
deployments = client.get_deployments()

# Get depth data for a time range
from datetime import datetime, timedelta
end = datetime.now()
start = end - timedelta(days=1)
depth_data = client.get_depth_data(start, end)

# Using spatial features
from floodnet_client import SpatialFloodNetClient
spatial_client = SpatialFloodNetClient(client)
gdf = spatial_client.get_deployments()  # Returns GeoDataFrame
```

## Development

1. Clone the repository
2. Install development dependencies: `pip install -e ".[spatial]"`
3. Run tests: `pytest`

## License

MIT License
