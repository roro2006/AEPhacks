"""
Test script to examine PyPSA network output structure
and generate sample JSON payload for the website
"""

import json
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def examine_network_output():
    """Examine the PyPSA network.lines_t['p0'] structure and generate JSON"""
    print("\n" + "="*70)
    print("Examining PyPSA Network Output Structure")
    print("="*70)

    try:
        from outage_simulator import OutageSimulator
        import pandas as pd
        import numpy as np

        print("\n[1] Initializing OutageSimulator...")
        simulator = OutageSimulator()
        print("    [OK] Simulator initialized")

        # Examine the network structure
        print("\n[2] Examining network.lines_t['p0'] structure...")
        p0_data = simulator.network.lines_t['p0']
        print(f"    Type: {type(p0_data)}")
        print(f"    Shape: {p0_data.shape}")
        print(f"    Columns (line names): {list(p0_data.columns[:5])}... ({len(p0_data.columns)} total)")
        print(f"    Index (snapshots): {p0_data.index.tolist()}")

        print(f"\n    Sample data (first 5 lines at 'now' snapshot):")
        for line_name in list(p0_data.columns[:5]):
            flow = p0_data.loc['now', line_name]
            print(f"      {line_name}: {flow:.4f} MW")

        # Examine lines DataFrame
        print("\n[3] Examining network.lines DataFrame...")
        print(f"    Columns: {list(simulator.network.lines.columns)}")
        print(f"    Total lines: {len(simulator.network.lines)}")

        # Sample line data
        sample_line = simulator.network.lines.iloc[0]
        print(f"\n    Sample line data (first line: {sample_line.name}):")
        for col in ['bus0', 'bus1', 's_nom', 'x', 'r', 'active']:
            if col in sample_line.index:
                print(f"      {col}: {sample_line[col]}")

        # Now run a contingency analysis and examine the full output
        print("\n[4] Running contingency analysis for line L0...")
        result = simulator.simulate_outage(['L0'])

        print(f"    Success: {result.get('success')}")
        print(f"\n    Result structure:")
        print(f"      - outage_lines: {result.get('outage_lines')}")
        print(f"      - overloaded_lines: {len(result.get('overloaded_lines', []))} lines")
        print(f"      - high_stress_lines: {len(result.get('high_stress_lines', []))} lines")
        print(f"      - loading_changes: {len(result.get('loading_changes', []))} lines")
        print(f"      - islanded_buses: {len(result.get('islanded_buses', []))} buses")
        print(f"      - affected_lines: {len(result.get('affected_lines', []))} lines")

        # Show sample loading change data
        if result.get('loading_changes'):
            print(f"\n    Sample loading_changes entry (first line):")
            sample = result['loading_changes'][0]
            for key, value in sample.items():
                print(f"      {key}: {value}")

        # Show metrics
        if result.get('metrics'):
            print(f"\n    Metrics:")
            for key, value in result['metrics'].items():
                print(f"      {key}: {value}")

        # Generate complete JSON payload
        print("\n[5] Generating complete JSON payload...")

        # Convert to JSON string with pretty printing
        json_payload = json.dumps(result, indent=2)

        # Save to file for inspection
        output_file = backend_dir / "sample_contingency_payload.json"
        with open(output_file, 'w') as f:
            f.write(json_payload)

        print(f"    [OK] JSON payload saved to: {output_file}")
        print(f"    Payload size: {len(json_payload)} bytes")

        # Show a truncated version
        lines = json_payload.split('\n')
        print(f"\n    First 50 lines of JSON payload:")
        print('\n'.join(lines[:50]))
        if len(lines) > 50:
            print(f"    ... ({len(lines) - 50} more lines)")

        # Generate sample API request code
        print("\n[6] Generating sample API request code...")

        api_code = '''
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
'''

        code_file = backend_dir / "sample_api_request.py"
        with open(code_file, 'w') as f:
            f.write(api_code)

        print(f"    [OK] Sample API request code saved to: {code_file}")

        print("\n" + "="*70)
        print("SUCCESS: Network structure examined and JSON generated!")
        print("="*70)
        return True

    except Exception as e:
        print(f"\n[X] Error: {e}")
        import traceback
        print(f"\nTraceback:")
        print(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = examine_network_output()
    sys.exit(0 if success else 1)
