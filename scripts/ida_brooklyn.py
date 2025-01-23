"""Query FloodNet sensor data from Brooklyn during Hurricane Ida."""
import logging
from datetime import datetime
import geopandas as gpd
from floodnet_client import SpatialFloodNetClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def main():
    # Initialize spatial client
    client = SpatialFloodNetClient()

    # Load Brooklyn boundary from geopackage
    brooklyn = gpd.read_file("tests/data/test_data.gpkg", layer="brooklyn")
    brooklyn_geom = brooklyn.geometry.iloc[0]

    # Define Ida time period (Sep 1-2, 2021)
    ida_start = datetime(2021, 9, 1, 0, 0)
    ida_end = datetime(2021, 9, 2, 23, 59)

    logger.info("Querying depth data during Hurricane Ida...")
    depth_data = client.get_depth_data_within_geometry(
        start_time=ida_start,
        end_time=ida_end,
        geometry=brooklyn_geom
    )

    if len(depth_data) > 0:
        logger.info("Found %d depth readings", len(depth_data))
        output_file = "ida_brooklyn_readings.gpkg"
        depth_data.to_file(output_file, driver="GPKG")
        logger.info("Saved results to %s", output_file)
    else:
        logger.info("No depth readings found for this time period")

if __name__ == "__main__":
    main()
