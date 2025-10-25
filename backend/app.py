"""
Flask API server for Grid Real-Time Rating Analysis System
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import json
import sys
import os

# Add ieee738 to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'osu_hackathon', 'ieee738'))
import ieee738
from ieee738 import ConductorParams

from rating_calculator import RatingCalculator
from data_loader import DataLoader

app = Flask(__name__)
CORS(app)

# Initialize data loader and calculator
data_loader = DataLoader()
calculator = RatingCalculator(data_loader)

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "message": "Grid Monitor API is running"})

@app.route('/api/grid/topology', methods=['GET'])
def get_topology():
    """Get grid topology including lines and buses"""
    try:
        return jsonify({
            "lines": data_loader.get_lines_geojson(),
            "buses": data_loader.get_buses_geojson() if hasattr(data_loader, 'get_buses_geojson') else []
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/lines/ratings', methods=['POST'])
def calculate_ratings():
    """
    Calculate line ratings for given weather conditions

    Expected JSON body:
    {
        "ambient_temp": 25,      # Celsius
        "wind_speed": 2.0,       # ft/sec
        "wind_angle": 90,        # degrees
        "sun_time": 12,          # hour (0-24)
        "date": "12 Jun"         # date for solar calculations
    }
    """
    try:
        weather = request.json

        # Set defaults
        weather_params = {
            'Ta': weather.get('ambient_temp', 25),
            'WindVelocity': weather.get('wind_speed', 2.0),
            'WindAngleDeg': weather.get('wind_angle', 90),
            'SunTime': weather.get('sun_time', 12),
            'Date': weather.get('date', '12 Jun'),
            'Emissivity': 0.8,
            'Absorptivity': 0.8,
            'Direction': 'EastWest',
            'Atmosphere': 'Clear',
            'Elevation': 1000,
            'Latitude': 27
        }

        # Calculate ratings for all lines
        results = calculator.calculate_all_line_ratings(weather_params)

        return jsonify({
            "weather": weather_params,
            "lines": results['lines'],
            "summary": results['summary']
        })

    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500

@app.route('/api/lines/threshold', methods=['POST'])
def find_threshold():
    """
    Find the ambient temperature threshold where lines start to overload

    Expected JSON body:
    {
        "temp_range": [20, 50],   # Temperature range to search
        "wind_speed": 2.0,
        "step": 1                 # Temperature increment
    }
    """
    try:
        params = request.json
        temp_range = params.get('temp_range', [20, 50])
        wind_speed = params.get('wind_speed', 2.0)
        step = params.get('step', 1)

        results = calculator.find_overload_threshold(
            temp_range[0], temp_range[1], wind_speed, step
        )

        return jsonify(results)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/contingency/n1', methods=['POST'])
def analyze_contingency():
    """
    Perform N-1 contingency analysis

    Expected JSON body:
    {
        "outage_line": "L0",           # Line to remove
        "ambient_temp": 25,
        "wind_speed": 2.0
    }
    """
    try:
        params = request.json
        outage_line = params.get('outage_line')

        weather_params = {
            'Ta': params.get('ambient_temp', 25),
            'WindVelocity': params.get('wind_speed', 2.0),
            'WindAngleDeg': 90,
            'SunTime': 12,
            'Date': '12 Jun',
            'Emissivity': 0.8,
            'Absorptivity': 0.8,
            'Direction': 'EastWest',
            'Atmosphere': 'Clear',
            'Elevation': 1000,
            'Latitude': 27
        }

        result = calculator.analyze_contingency(outage_line, weather_params)

        return jsonify(result)

    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500

@app.route('/api/lines/<line_id>', methods=['GET'])
def get_line_details(line_id):
    """Get detailed information about a specific line"""
    try:
        line_info = data_loader.get_line_info(line_id)
        if line_info is None:
            return jsonify({"error": "Line not found"}), 404

        return jsonify(line_info)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/chatbot', methods=['POST'])
def chatbot():
    """
    Chatbot endpoint to answer questions about the grid

    Expected JSON body:
    {
        "message": "What is the status of line L0?",
        "weather": {
            "ambient_temp": 25,
            "wind_speed": 2.0,
            "wind_angle": 90,
            "sun_time": 12,
            "date": "12 Jun"
        }
    }
    """
    try:
        data = request.json
        user_message = data.get('message', '').lower()
        weather = data.get('weather', {})

        # Set weather parameters with defaults
        weather_params = {
            'Ta': weather.get('ambient_temp', 25),
            'WindVelocity': weather.get('wind_speed', 2.0),
            'WindAngleDeg': weather.get('wind_angle', 90),
            'SunTime': weather.get('sun_time', 12),
            'Date': weather.get('date', '12 Jun'),
            'Emissivity': 0.8,
            'Absorptivity': 0.8,
            'Direction': 'EastWest',
            'Atmosphere': 'Clear',
            'Elevation': 1000,
            'Latitude': 27
        }

        # Calculate current ratings
        results = calculator.calculate_all_line_ratings(weather_params)
        lines = results['lines']
        summary = results['summary']

        # Process user query
        response = ""

        # Check for specific line queries
        if 'line' in user_message or 'l0' in user_message or 'l1' in user_message or 'l2' in user_message:
            # Extract line name
            line_name = None
            for line in lines:
                if line['name'].lower() in user_message:
                    line_name = line['name']
                    break

            if line_name:
                line_data = next((l for l in lines if l['name'] == line_name), None)
                if line_data:
                    response = f"Line {line_name} ({line_data['branch_name']}) is currently at {line_data['loading_pct']:.1f}% loading with a rating of {line_data['rating_mva']:.1f} MVA and flow of {line_data['flow_mva']:.1f} MVA. Status: {line_data['stress_level'].upper()}."
            else:
                response = "I can provide information about specific lines. Please specify a line name (e.g., 'What is the status of line L0?')."

        # Check for overloaded/critical lines
        elif 'overload' in user_message or 'critical' in user_message or 'problem' in user_message or 'issue' in user_message:
            critical_lines = [l for l in lines if l['stress_level'] == 'critical']
            high_stress = [l for l in lines if l['stress_level'] == 'high']

            if critical_lines:
                response = f"There are {len(critical_lines)} critical line(s): "
                response += ", ".join([f"{l['name']} ({l['loading_pct']:.1f}%)" for l in critical_lines])
            elif high_stress:
                response = f"There are {len(high_stress)} line(s) with high stress: "
                response += ", ".join([f"{l['name']} ({l['loading_pct']:.1f}%)" for l in high_stress])
            else:
                response = "All lines are operating within normal parameters. No critical issues detected."

        # Check for summary/status queries
        elif 'summary' in user_message or 'status' in user_message or 'overview' in user_message or 'how' in user_message:
            response = f"Grid Status Summary: {summary['total_lines']} lines monitored. "
            response += f"Critical: {summary['critical_count']}, High Stress: {summary['high_stress_count']}, "
            response += f"Caution: {summary['caution_count']}, Normal: {summary['normal_count']}. "
            if summary['max_loading_line']:
                response += f"Highest loaded line: {summary['max_loading_line']} at {summary['max_loading_pct']:.1f}%."

        # Check for weather impact queries
        elif 'weather' in user_message or 'temperature' in user_message or 'wind' in user_message:
            response = f"Current conditions: Temperature {weather_params['Ta']}°C ({weather_params['Ta'] * 9/5 + 32:.1f}°F), "
            response += f"Wind speed {weather_params['WindVelocity']} ft/s ({weather_params['WindVelocity'] * 0.681818:.1f} mph), "
            response += f"Time: {weather_params['SunTime']}:00. "

            # Check if conditions are affecting ratings
            if summary['critical_count'] > 0:
                response += "These conditions are causing some lines to operate at critical levels."
            else:
                response += "All lines are operating within acceptable limits under these conditions."

        # Check for highest/worst performing line
        elif 'highest' in user_message or 'worst' in user_message or 'most loaded' in user_message:
            if summary['max_loading_line']:
                line_data = next((l for l in lines if l['name'] == summary['max_loading_line']), None)
                if line_data:
                    response = f"The highest loaded line is {summary['max_loading_line']} ({line_data['branch_name']}) at {summary['max_loading_pct']:.1f}% loading. "
                    response += f"Rating: {line_data['rating_mva']:.1f} MVA, Flow: {line_data['flow_mva']:.1f} MVA."

        # Check for best performing line
        elif 'lowest' in user_message or 'best' in user_message or 'least loaded' in user_message:
            min_line = min(lines, key=lambda x: x['loading_pct'])
            response = f"The least loaded line is {min_line['name']} ({min_line['branch_name']}) at {min_line['loading_pct']:.1f}% loading. "
            response += f"Rating: {min_line['rating_mva']:.1f} MVA, Flow: {min_line['flow_mva']:.1f} MVA."

        # Check for help queries
        elif 'help' in user_message or 'what can you' in user_message or 'commands' in user_message:
            response = "I can help you with:\n"
            response += "• Line status (e.g., 'What is the status of line L0?')\n"
            response += "• Grid overview (e.g., 'Give me a summary')\n"
            response += "• Critical issues (e.g., 'Are there any overloaded lines?')\n"
            response += "• Weather impact (e.g., 'How is the weather affecting the grid?')\n"
            response += "• Performance analysis (e.g., 'Which line is most loaded?')"

        # Default response
        else:
            response = f"I'm monitoring {summary['total_lines']} transmission lines. "
            response += "You can ask me about specific lines, grid status, critical issues, or weather impact. "
            response += "Type 'help' for more options."

        return jsonify({
            "response": response,
            "summary": summary,
            "timestamp": pd.Timestamp.now().isoformat()
        })

    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
