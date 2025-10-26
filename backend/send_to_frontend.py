"""
Demonstration script showing how to send contingency analysis data to the frontend

This script shows multiple ways to integrate the PyPSA network analysis results
with the frontend application.
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))


def example_1_direct_simulation():
    """
    Example 1: Direct simulation and JSON export
    Use case: Generating static reports or saving results to disk
    """
    print("\n" + "="*70)
    print("Example 1: Direct Simulation and JSON Export")
    print("="*70)

    from outage_simulator import OutageSimulator

    # Initialize simulator
    simulator = OutageSimulator()

    # Run N-1 contingency for line L0
    print("\n[1] Running N-1 contingency for line L0...")
    result = simulator.simulate_outage(['L0'])

    # Save to JSON file
    output_file = backend_dir / "contingency_L0_result.json"
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"    [OK] Results saved to: {output_file}")
    print(f"    Success: {result['success']}")
    print(f"    Overloaded lines: {result['metrics']['overloaded_count']}")
    print(f"    Max loading: {result['metrics']['max_loading_pct']:.2f}%")

    return result


def example_2_api_request():
    """
    Example 2: Send HTTP request to backend API
    Use case: Frontend application requesting analysis
    """
    print("\n" + "="*70)
    print("Example 2: HTTP API Request")
    print("="*70)

    import requests

    API_BASE = "http://localhost:5000/api"

    # Prepare request payload
    payload = {
        "outage_lines": ["L4"],
        "use_lpf": False
    }

    print(f"\n[1] Sending POST request to {API_BASE}/outage/simulate")
    print(f"    Payload: {json.dumps(payload, indent=2)}")

    try:
        # Send request
        response = requests.post(
            f"{API_BASE}/outage/simulate",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            print(f"\n    [OK] Request successful!")
            print(f"    Outaged: {result['outage_lines']}")
            print(f"    Overloaded: {result['metrics']['overloaded_count']} lines")
            print(f"    Max loading: {result['metrics']['max_loading_pct']:.2f}%")

            # Show most affected lines
            if result['affected_lines']:
                print(f"\n    Most affected lines:")
                for line in result['affected_lines'][:3]:
                    print(f"      {line['name']}: {line['loading_change_pct']:+.2f}% change")

            return result

        else:
            print(f"\n    [X] Request failed with status {response.status_code}")
            print(f"    Error: {response.text}")
            return None

    except requests.exceptions.ConnectionError:
        print(f"\n    [X] Connection failed. Is the Flask server running?")
        print(f"    Start server with: python app.py")
        return None
    except Exception as e:
        print(f"\n    [X] Error: {e}")
        return None


def example_3_batch_analysis():
    """
    Example 3: Batch analysis of multiple contingencies
    Use case: Analyzing all N-1 contingencies for the system
    """
    print("\n" + "="*70)
    print("Example 3: Batch N-1 Contingency Analysis")
    print("="*70)

    from outage_simulator import OutageSimulator

    # Initialize simulator
    simulator = OutageSimulator()

    # Get all available lines
    available_lines = simulator.get_available_lines()
    print(f"\n[1] Found {len(available_lines)} lines in the system")

    # Select first 5 lines for demo (in practice, analyze all)
    lines_to_test = [line['name'] for line in available_lines[:5]]
    print(f"    Testing: {lines_to_test}")

    # Prepare scenarios (each scenario is a list of lines to outage)
    scenarios = [[line] for line in lines_to_test]

    # Run batch analysis
    print(f"\n[2] Running {len(scenarios)} N-1 contingency scenarios...")
    results = simulator.run_multiple_contingency_scenarios(scenarios)

    # Analyze results
    print(f"\n[3] Analysis complete!")

    # Find most severe contingencies
    severity_scores = []
    for result in results:
        if result.get('success'):
            score = (
                result['metrics']['overloaded_count'] * 100 +
                result['metrics']['max_loading_pct']
            )
            severity_scores.append({
                'outage': result['outage_lines'][0],
                'score': score,
                'overloaded': result['metrics']['overloaded_count'],
                'max_loading': result['metrics']['max_loading_pct']
            })

    # Sort by severity
    severity_scores.sort(key=lambda x: x['score'], reverse=True)

    print(f"\n    Top 3 most severe contingencies:")
    for i, scenario in enumerate(severity_scores[:3], 1):
        print(f"      {i}. Line {scenario['outage']}: "
              f"{scenario['overloaded']} overloaded, "
              f"max loading {scenario['max_loading']:.2f}%")

    # Save batch results
    output_file = backend_dir / "batch_contingency_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n    [OK] Batch results saved to: {output_file}")

    return results


def example_4_visualization_data():
    """
    Example 4: Prepare data specifically for frontend visualization
    Use case: Sending optimized data for charts and graphs
    """
    print("\n" + "="*70)
    print("Example 4: Prepare Visualization Data")
    print("="*70)

    from outage_simulator import OutageSimulator

    # Initialize and run simulation
    simulator = OutageSimulator()
    result = simulator.simulate_outage(['L0'])

    if not result['success']:
        print("    [X] Simulation failed")
        return None

    # Prepare data for different chart types
    visualization_data = {
        # 1. Bar chart: Top 10 most affected lines
        'bar_chart_loading_changes': [
            {
                'line': line['name'],
                'before': line['baseline_loading_pct'],
                'after': line['loading_pct'],
                'change': line['loading_change_pct']
            }
            for line in sorted(
                result['loading_changes'],
                key=lambda x: abs(x['loading_change_pct']),
                reverse=True
            )[:10]
            if not line['is_outaged']
        ],

        # 2. Pie chart: Distribution of line status
        'pie_chart_status': {
            'normal': sum(1 for l in result['loading_changes']
                         if l['status'] == 'normal'),
            'caution': sum(1 for l in result['loading_changes']
                          if l['status'] == 'caution'),
            'high_stress': sum(1 for l in result['loading_changes']
                              if l['status'] == 'high_stress'),
            'overloaded': sum(1 for l in result['loading_changes']
                             if l['status'] == 'overloaded'),
            'outaged': sum(1 for l in result['loading_changes']
                          if l['status'] == 'outaged')
        },

        # 3. Line graph: Loading distribution
        'histogram_loading': [
            line['loading_pct']
            for line in result['loading_changes']
            if line['is_active'] and not line['is_outaged']
        ],

        # 4. Network graph: Flow changes
        'network_graph': {
            'nodes': list(set(
                [line['bus0'] for line in result['loading_changes']] +
                [line['bus1'] for line in result['loading_changes']]
            )),
            'edges': [
                {
                    'source': line['bus0'],
                    'target': line['bus1'],
                    'flow': line['flow_mw'],
                    'loading': line['loading_pct'],
                    'status': line['status'],
                    'width': min(abs(line['flow_mw']) / 50, 10)  # Scale for visualization
                }
                for line in result['loading_changes']
            ]
        },

        # 5. Metrics summary (for dashboard cards)
        'dashboard_metrics': {
            'total_lines': result['metrics']['total_lines'],
            'outaged': result['metrics']['outaged_lines_count'],
            'overloaded': result['metrics']['overloaded_count'],
            'high_stress': result['metrics']['high_stress_count'],
            'islanded_buses': result['metrics']['islanded_buses_count'],
            'max_loading': round(result['metrics']['max_loading_pct'], 2),
            'avg_loading': round(result['metrics']['avg_loading_pct'], 2),
            'max_increase': round(result['metrics']['max_loading_increase'], 2)
        }
    }

    # Save visualization data
    output_file = backend_dir / "visualization_data.json"
    with open(output_file, 'w') as f:
        json.dump(visualization_data, f, indent=2)

    print(f"\n[1] Prepared visualization data:")
    print(f"    Bar chart: {len(visualization_data['bar_chart_loading_changes'])} data points")
    print(f"    Pie chart: {sum(visualization_data['pie_chart_status'].values())} total")
    print(f"    Network graph: {len(visualization_data['network_graph']['nodes'])} nodes, "
          f"{len(visualization_data['network_graph']['edges'])} edges")
    print(f"\n    [OK] Saved to: {output_file}")

    # Print sample for bar chart
    print(f"\n[2] Sample bar chart data (top 3 changes):")
    for item in visualization_data['bar_chart_loading_changes'][:3]:
        print(f"    {item['line']}: {item['before']:.1f}% -> {item['after']:.1f}% "
              f"({item['change']:+.1f}%)")

    return visualization_data


def example_5_websocket_stream():
    """
    Example 5: Stream results in real-time (conceptual)
    Use case: Real-time updates during long-running analysis
    """
    print("\n" + "="*70)
    print("Example 5: Real-time Streaming (Conceptual)")
    print("="*70)

    print("\n[1] WebSocket streaming structure:")
    print("""
    # Backend (Flask-SocketIO)
    from flask_socketio import SocketIO, emit

    socketio = SocketIO(app, cors_allowed_origins="*")

    @socketio.on('run_contingency')
    def handle_contingency(data):
        outage_lines = data['outage_lines']

        # Send progress updates
        emit('progress', {'status': 'starting', 'progress': 0})

        # Initialize simulator
        simulator = OutageSimulator()
        emit('progress', {'status': 'initialized', 'progress': 20})

        # Run simulation
        result = simulator.simulate_outage(outage_lines)
        emit('progress', {'status': 'solving', 'progress': 80})

        # Send final results
        emit('result', result)
        emit('progress', {'status': 'complete', 'progress': 100})

    # Frontend (Socket.IO client)
    import { io } from 'socket.io-client';

    const socket = io('http://localhost:5000');

    socket.on('progress', (data) => {
        console.log(`Progress: ${data.progress}% - ${data.status}`);
        updateProgressBar(data.progress);
    });

    socket.on('result', (data) => {
        console.log('Analysis complete!', data);
        displayResults(data);
    });

    // Trigger analysis
    socket.emit('run_contingency', { outage_lines: ['L0'] });
    """)

    print("\n    [NOTE] This is a conceptual example showing how to implement")
    print("    real-time streaming for long-running analyses.")


def main():
    """Run all examples"""
    print("\n" + "="*70)
    print("CONTINGENCY ANALYSIS - FRONTEND INTEGRATION EXAMPLES")
    print("="*70)

    # Example 1: Direct simulation
    result1 = example_1_direct_simulation()

    # Example 2: API request (requires Flask server running)
    result2 = example_2_api_request()

    # Example 3: Batch analysis
    result3 = example_3_batch_analysis()

    # Example 4: Visualization data
    result4 = example_4_visualization_data()

    # Example 5: WebSocket streaming (conceptual)
    example_5_websocket_stream()

    print("\n" + "="*70)
    print("ALL EXAMPLES COMPLETE")
    print("="*70)
    print("\nGenerated files:")
    print("  - contingency_L0_result.json")
    print("  - batch_contingency_results.json")
    print("  - visualization_data.json")
    print("  - sample_contingency_payload.json")
    print("\nSee CONTINGENCY_API_INTEGRATION.md for full documentation")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
