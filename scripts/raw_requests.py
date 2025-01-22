"""Simple script to make raw requests to the FloodNet API and print responses."""
import requests
from datetime import datetime, timedelta
import json

API_BASE = "https://api.dev.floodlabs.nyc/api/rest/"

# Get deployments
print("\n=== Raw Deployments Response ===")
response = requests.get(f"{API_BASE}deployments/flood")
print(json.dumps(response.json(), indent=2))

# Get depth data for the last hour from first deployment
print("\n=== Raw Depth Data Response ===")
end = datetime.now()
start = end - timedelta(hours=1)

params = {
    "start_time": start.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
    "end_time": end.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
}

# Get first deployment ID
first_deployment = response.json()['deployments'][0]['deployment_id']
depth_response = requests.get(
    f"{API_BASE}deployments/flood/{first_deployment}/depth",
    params=params
)
print(json.dumps(depth_response.json(), indent=2))
