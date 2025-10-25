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
from chatbot_service import GridChatbotService

app = Flask(__name__)
CORS(app)

# Initialize data loader and calculator
data_loader = DataLoader()
calculator = RatingCalculator(data_loader)

# Initialize AI chatbot service
try:
    chatbot_service = GridChatbotService()
    CHATBOT_ENABLED = True
except ValueError as e:
    print(f"Warning: AI chatbot disabled - {e}")
    CHATBOT_ENABLED = False
except Exception as e:
    print(f"Warning: AI chatbot initialization failed - {e}")
    CHATBOT_ENABLED = False

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
    AI-powered chatbot endpoint with data explanation and impact analysis

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
        user_message = data.get('message', '')
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

        # Use AI chatbot if enabled, otherwise fall back to rule-based
        if CHATBOT_ENABLED:
            ai_response = chatbot_service.get_response(
                user_message=user_message,
                grid_data=results,
                weather=weather_params
            )

            return jsonify({
                "response": ai_response['response'],
                "query_type": ai_response.get('query_type', 'general'),
                "ai_powered": True,
                "context_used": ai_response.get('context_used', {}),
                "model": ai_response.get('model_used', 'N/A'),
                "tokens": ai_response.get('tokens_used', 0),
                "summary": results['summary'],
                "timestamp": pd.Timestamp.now().isoformat()
            })
        else:
            # Fallback to simple rule-based responses
            return jsonify({
                "response": "AI chatbot is not configured. Please set ANTHROPIC_API_KEY in backend/.env file. Using basic responses for now.",
                "ai_powered": False,
                "summary": results['summary'],
                "timestamp": pd.Timestamp.now().isoformat()
            })

    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500

@app.route('/api/chatbot/analyze-impact', methods=['POST'])
def analyze_impact():
    """
    Specialized endpoint for variable impact analysis

    Expected JSON body:
    {
        "variable": "temperature",
        "change": {"from": 25, "to": 35},
        "weather": {...},
    }
    """
    try:
        if not CHATBOT_ENABLED:
            return jsonify({
                "error": "AI chatbot not configured. Please set ANTHROPIC_API_KEY."
            }), 503

        data = request.json
        variable = data.get('variable')
        change = data.get('change')
        weather = data.get('weather', {})

        # Set weather parameters
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

        # Get current grid data
        results = calculator.calculate_all_line_ratings(weather_params)

        # Analyze impact
        analysis = chatbot_service.analyze_variable_impact(
            variable=variable,
            change=change,
            current_weather=weather_params,
            grid_data=results
        )

        return jsonify({
            "analysis": analysis['impact_analysis'],
            "variable": variable,
            "change": change,
            "timestamp": pd.Timestamp.now().isoformat()
        })

    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
