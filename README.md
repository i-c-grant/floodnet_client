# FloodNet Client

A simple Python client for the NYC FloodNet sensor network. Access flood sensor data with optional spatial querying capabilities.

## Installation

### Using pip

Basic installation with core features:
```bash
pip install git+https://github.com/i-c-grant/floodnet-client.git
```

With spatial features (includes geopandas and shapely):
```bash
pip install "git+https://github.com/i-c-grant/floodnet-client.git#egg=floodnet-client[spatial]"
```

### Using conda

We provide a conda environment with all dependencies:
```bash
conda env create -f environment.yaml
conda activate floodnet
```

## Usage

### Basic Usage

```python
from datetime import datetime, timedelta
from floodnet_client import FloodNetClient

# Initialize client
client = FloodNetClient()

# Get all sensor deployments
deployments = client.get_deployments()
print(f"Found {len(deployments)} deployments")

# Get depth data for last hour
end = datetime.now()
start = end - timedelta(hours=1)
depth_data = client.get_depth_data(start, end)
print(f"Got {len(depth_data)} readings")

# Get data for specific deployments
specific_data = client.get_depth_data(
    start_time=start,
    end_time=end,
    deployment_ids=['daily_new_falcon', 'weekly_poetic_guinea']
)
```

The client automatically caches deployment data for 24 hours to improve performance. You can:
- Force a refresh with `get_deployments(force_refresh=True)`
- Clear the cache with `refresh_deployments_cache()`

### Spatial Features

```python
from floodnet_client import SpatialFloodNetClient
from shapely.geometry import box

# Create spatial client
spatial_client = SpatialFloodNetClient(FloodNetClient())

# Get deployments as GeoDataFrame
gdf = spatial_client.get_deployments()

# Query deployments within a bounding box
bbox = box(
    minx=-74.0, 
    miny=40.7, 
    maxx=-73.9, 
    maxy=40.8
)
deployments_in_area = spatial_client.get_deployments_within(bbox)

# Get depth data for sensors in area
depth_data = spatial_client.get_depth_data_within(
    start_time=start,
    end_time=end,
    geometry=bbox
)
```

## Client Architecture

The package provides two client classes:

1. **FloodNetClient** - Core client with no spatial dependencies
   - Lightweight with only `requests` and `pydantic` requirements
   - Ideal for containerized environments or when spatial operations aren't needed
   - Provides basic API access and caching

2. **SpatialFloodNetClient** - Extends the base client with spatial capabilities
   - Requires `geopandas` and `shapely`
   - Adds GeoDataFrame conversions and spatial queries
   - Useful for GIS analysis and visualization

This separation allows you to use the core API functionality without installing spatial dependencies when they're not needed.

## License

MIT License
