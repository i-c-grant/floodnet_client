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

# Get depth data for last 24 hours
end = datetime.now()
start = end - timedelta(days=1)
depth_data = client.get_depth_data(start, end)

# Get data for specific deployments
deployment_ids = ['BKLN_001', 'BKLN_002']
specific_data = client.get_depth_data(
    start_time=start,
    end_time=end,
    deployment_ids=deployment_ids
)
```

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
depth_data = spatial_client.get_depth_data(
    start_time=start,
    end_time=end,
    geometry=bbox
)
```

## Development

1. Clone the repository:
```bash
git clone https://github.com/i-c-grant/floodnet-client.git
cd floodnet-client
```

2. Create development environment:
```bash
conda env create -f environment.yaml
conda activate floodnet
```

3. Install in editable mode:
```bash
pip install -e ".[spatial]"
```

4. Run tests:
```bash
pytest
```

## License

MIT License
