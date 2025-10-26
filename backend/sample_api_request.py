
"""
Sample code to send contingency analysis results to the frontend
"""

import requests
import json

# API endpoint (adjust based on your frontend URL)
API_URL = "http://localhost:5000/api/outage/simulate"

# Payload to send
payload = {
    "outage_lines": ["L0"],  # List of lines to outage
    "use_lpf": False         # Use nonlinear power flow
}

# Send POST request
response = requests.post(
    API_URL,
    headers={"Content-Type": "application/json"},
    json=payload
)

# Check response
if response.status_code == 200:
    result = response.json()
    print("Contingency analysis successful!")
    print(f"Outaged lines: {result['outage_lines']}")
    print(f"Overloaded lines: {len(result['overloaded_lines'])}")
    print(f"Max loading: {result['metrics']['max_loading_pct']:.2f}%")
else:
    print(f"Error: {response.status_code}")
    print(response.text)
