"""
Flask API server for Grid Real-Time Rating Analysis System
"""

def load_required_data():
    """
    Load required data files and verify they are accessible
    Returns True if successful, False if data loading failed
    """
    try:
        # Verify GeoJSON files are loaded
        if not data_loader.lines_geojson:
            logger.info("Loading line GeoJSON data...")
            data_loader.reload_data()
            if not data_loader.lines_geojson:
                logger.error("Failed to load line GeoJSON data")
                return False
        else:
            logger.debug("Line GeoJSON data already loaded")

        if not data_loader.buses_geojson:
            logger.info("Loading bus GeoJSON data...")
            data_loader.reload_data()
            if not data_loader.buses_geojson:
                logger.error("Failed to load bus GeoJSON data")
                return False
        else:
            logger.debug("Bus GeoJSON data already loaded")

        # Verify map generator has data
        if not map_generator.lines_geojson:
            logger.info("Reloading map generator data...")
            map_generator.lines_geojson = data_loader.get_lines_geojson()
            if not map_generator.lines_geojson:
                logger.error("Failed to load map generator GeoJSON data")
                return False
        else:
            logger.debug("Map generator data already loaded")

        return True

    except Exception as e:
        logger.error(f"Error loading required data: {str(e)}")
        return False
from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import numpy as np
import json
import logging
import os

# Configure logging
# Default to DEBUG to assist interactive troubleshooting during development
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

from rating_calculator import RatingCalculator
from data_loader import DataLoader
from map_generator import GridMapGenerator
from chatbot_service import GridChatbotService

# Custom JSON encoder to handle NaN values
class NanSafeJSONEncoder(json.JSONEncoder):
    """JSON encoder that converts NaN to null"""
    def default(self, obj):
        if isinstance(obj, float):
            if np.isnan(obj) or np.isinf(obj):
                return None
        return super().default(obj)

def clean_nan_values(obj):
    """
    Recursively replace NaN values with None in nested dictionaries/lists
    Also converts numpy types to native Python types for JSON serialization

    Args:
        obj: Object to clean (dict, list, or primitive)

    Returns:
        Cleaned object with NaN replaced by None and numpy types converted
    """
    if isinstance(obj, dict):
        return {k: clean_nan_values(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_nan_values(item) for item in obj]
    elif isinstance(obj, np.bool_):
        # Convert numpy boolean to Python boolean
        return bool(obj)
    elif isinstance(obj, (np.integer, np.int64, np.int32)):
        # Convert numpy integers to Python int
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        # Convert numpy floats to Python float, handling NaN/inf
        if pd.isna(obj) or np.isnan(obj) or np.isinf(obj):
            return None
        return float(obj)
    elif isinstance(obj, float):
        if pd.isna(obj) or np.isnan(obj) or np.isinf(obj):
            return None
        return obj
    else:
        return obj

app = Flask(__name__)
app.json_encoder = NanSafeJSONEncoder
CORS(app)

# Initialize data loader and calculator
data_loader = DataLoader()
calculator = RatingCalculator(data_loader)
map_generator = GridMapGenerator(data_loader)

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

# Initialize autonomous grid monitoring agent
AGENT_ENABLED = os.getenv('AGENT_ENABLED', 'true').lower() == 'true'
grid_agent = None

if AGENT_ENABLED:
    try:
        from agent import GridMonitorAgent, AgentState

        # Load or create agent state
        agent_state_path = os.getenv('AGENT_STATE_PATH', 'backend/data/agent_state.json')
        agent_state = AgentState.load(agent_state_path)

        # Initialize agent
        grid_agent = GridMonitorAgent(
            calculator=calculator,
            state=agent_state,
            config={
                'decision_log_path': os.getenv('AGENT_LOG_PATH', 'backend/data/agent_decisions.log'),
                'state_path': agent_state_path,
                'persistence_enabled': os.getenv('AGENT_PERSISTENCE', 'true').lower() == 'true'
            }
        )
        print("✓ Autonomous Grid Monitor Agent initialized successfully")
    except Exception as e:
        print(f"Warning: Grid Monitor Agent initialization failed - {e}")
        AGENT_ENABLED = False
        grid_agent = None

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

        # Clean NaN values before sending to frontend
        response_data = {
            "weather": weather_params,
            "lines": clean_nan_values(results['lines']),
            "summary": clean_nan_values(results['summary'])
        }

        return jsonify(response_data)

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

@app.route('/api/outage/available-lines', methods=['GET'])
def get_available_lines():
    """
    Get list of all transmission lines available for outage simulation

    Returns:
        JSON with list of lines and their properties
    """
    try:
        from outage_simulator import OutageSimulator

        simulator = OutageSimulator()
        lines = simulator.get_available_lines()

        return jsonify({
            'success': True,
            'lines': lines,
            'total_count': len(lines)
        })

    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500


@app.route('/api/outage/simulate', methods=['POST'])
def simulate_outage():
    """
    Simulate transmission line outage(s) and analyze impacts

    Expected JSON body:
    {
        "outage_lines": ["L48", "L49"],  # List of line names to remove (or single string)
        "use_lpf": false                  # Optional: use linear power flow (faster but less accurate)
    }

    Returns:
        Comprehensive analysis including:
        - Overloaded lines
        - High stress lines
        - Islanded buses
        - Loading changes for all lines
        - Summary metrics
    """
    try:
        params = request.json
        outage_lines = params.get('outage_lines', [])
        use_lpf = params.get('use_lpf', False)

        # Convert single line to list
        if isinstance(outage_lines, str):
            outage_lines = [outage_lines]

        if not outage_lines:
            return jsonify({
                "success": False,
                "error": "No outage lines specified"
            }), 400

        # Run contingency analysis
        result = calculator.analyze_contingency(outage_lines)

        # Clean NaN values
        result_clean = clean_nan_values(result)

        return jsonify(result_clean)

    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500


@app.route('/api/contingency/n1', methods=['POST'])
def analyze_contingency():
    """
    Legacy endpoint - Perform N-1 contingency analysis

    Expected JSON body:
    {
        "outage_line": "L0",           # Line to remove (or list of lines)
        "ambient_temp": 25,            # Currently not used (static flows)
        "wind_speed": 2.0              # Currently not used (static flows)
    }
    """
    try:
        params = request.json
        outage_line = params.get('outage_line')

        if not outage_line:
            return jsonify({
                "success": False,
                "error": "No outage line specified"
            }), 400

        result = calculator.analyze_contingency(outage_line)

        # Clean NaN values
        result_clean = clean_nan_values(result)

        return jsonify(result_clean)

    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500

@app.route('/api/agent/status', methods=['GET'])
def agent_status():
    """
    Get current agent state and status

    Returns:
        agent_enabled: bool
        last_run: ISO8601 timestamp
        summary: open_issues_count, last_issues
        version: state schema version
    """
    try:
        if not AGENT_ENABLED or grid_agent is None:
            return jsonify({
                "agent_enabled": False,
                "message": "Agent is disabled. Set AGENT_ENABLED=true in environment."
            })

        # Get agent heartbeat
        status = grid_agent.heartbeat_loop()

        # Get recent issues from history if available
        last_issues = []
        if len(grid_agent.state.history) > 0:
            # Note: Issues are not stored in history, this is a simplified response
            last_issues = []

        return jsonify({
            "agent_enabled": True,
            "last_run": status['timestamp'],
            "summary": {
                "open_issues_count": 0,  # Would need to track open issues separately
                "last_issues": last_issues
            },
            "version": status['state_version'],
            "state_info": {
                "history_size": status['history_size'],
                "action_history_size": status['action_history_size'],
                "thresholds": status['thresholds']
            }
        })

    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500


@app.route('/api/agent/predict', methods=['POST'])
def agent_predict():
    """
    Predict future grid states using weather forecast

    Request body:
        weather_forecast: List of forecast dicts with timestamp, Ta, WindVelocity, etc.

    Returns:
        predictions: List of prediction dicts
        model: "ieee738"
        generated_at: ISO timestamp
    """
    try:
        if not AGENT_ENABLED or grid_agent is None:
            return jsonify({
                "error": "Agent is disabled. Set AGENT_ENABLED=true in environment."
            }), 503

        data = request.json
        weather_forecast = data.get('weather_forecast', [])

        if not weather_forecast:
            return jsonify({"error": "weather_forecast is required"}), 400

        # Generate predictions
        predictions = grid_agent.predict_future_states(weather_forecast)

        # Clean NaN values
        predictions_clean = clean_nan_values(predictions)

        # Persist state if enabled
        if grid_agent.config.get('persistence_enabled', True):
            grid_agent.state.save(grid_agent.config.get('state_path', 'backend/data/agent_state.json'))

        return jsonify(predictions_clean)

    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500


@app.route('/api/agent/recommendations', methods=['POST'])
def agent_recommendations():
    """
    Generate prioritized recommendations

    Request body:
        scope: "line" | "area" | "grid" (optional, default "grid")
        limit: max recommendations (optional, default 5)
        weather: current weather params (optional, will monitor if provided)

    Returns:
        recommendations: List of recommendation dicts
    """
    try:
        if not AGENT_ENABLED or grid_agent is None:
            return jsonify({
                "error": "Agent is disabled. Set AGENT_ENABLED=true in environment."
            }), 503

        data = request.json or {}
        scope = data.get('scope', 'grid')
        limit = data.get('limit', 5)
        weather = data.get('weather')

        # If weather provided, run monitoring first to get issues
        issues = []
        if weather:
            # Build weather params
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

            # Get current ratings
            current_data = calculator.calculate_all_line_ratings(weather_params)

            # Monitor for issues
            issues = grid_agent.monitor_grid_state(current_data)

        # Generate recommendations
        recommendations = grid_agent.generate_recommendations(issues, scope=scope, limit=limit)

        # Clean and return
        recommendations_clean = clean_nan_values({
            "recommendations": recommendations
        })

        # Persist state if enabled
        if grid_agent.config.get('persistence_enabled', True):
            grid_agent.state.save(grid_agent.config.get('state_path', 'backend/data/agent_state.json'))

        return jsonify(recommendations_clean)

    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500


@app.route('/api/agent/feedback', methods=['POST'])
def agent_feedback():
    """
    Submit operator feedback on agent recommendations

    Request body:
        action_id: ID of the action
        result: Dict with success, metrics, notes

    Returns:
        status: "ok"
    """
    try:
        if not AGENT_ENABLED or grid_agent is None:
            return jsonify({
                "error": "Agent is disabled. Set AGENT_ENABLED=true in environment."
            }), 503

        data = request.json
        action_id = data.get('action_id')
        result = data.get('result', {})

        if not action_id:
            return jsonify({"error": "action_id is required"}), 400

        # Learn from feedback
        grid_agent.learn_from_outcomes(action_id, result)

        # Persist state if enabled
        if grid_agent.config.get('persistence_enabled', True):
            grid_agent.state.save(grid_agent.config.get('state_path', 'backend/data/agent_state.json'))

        return jsonify({"status": "ok"})

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

        # Get autonomous insights from agent if enabled
        agent_insights = None
        if AGENT_ENABLED and grid_agent is not None:
            try:
                # Run autonomous monitoring to detect issues
                detected_issues = grid_agent.monitor_grid_state(results)

                # Generate a short summary for chatbot context
                if detected_issues:
                    critical_count = sum(1 for i in detected_issues if i.get('severity') == 'critical')
                    high_count = sum(1 for i in detected_issues if i.get('severity') == 'high')

                    summary_text = f"Agent detected {len(detected_issues)} issue(s)"
                    if critical_count > 0:
                        summary_text += f" ({critical_count} critical)"

                    agent_insights = {
                        'summary': summary_text,
                        'issues_count': len(detected_issues),
                        'critical_count': critical_count,
                        'high_count': high_count,
                        'issues': detected_issues[:3]  # Top 3 issues
                    }
            except Exception as e:
                logger.warning(f"Failed to get agent insights: {e}")
                agent_insights = None

        # Use AI chatbot if enabled, otherwise fall back to rule-based
        if CHATBOT_ENABLED:
            ai_response = chatbot_service.get_response(
                user_message=user_message,
                grid_data=results,
                weather=weather_params
            )

            response_data = {
                "response": ai_response['response'],
                "query_type": ai_response.get('query_type', 'general'),
                "ai_powered": True,
                "context_used": ai_response.get('context_used', {}),
                "model": ai_response.get('model_used', 'N/A'),
                "tokens": ai_response.get('tokens_used', 0),
                "summary": results['summary'],
                "timestamp": pd.Timestamp.now().isoformat()
            }

            # Add agent insights if available
            if agent_insights:
                response_data['agent_insights'] = agent_insights

            return jsonify(response_data)
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

@app.route('/api/map/generate', methods=['POST'])
def generate_map():
    """
    Generate interactive network map with real-time data

    Expected JSON body:
    {
        "ambient_temp": 25,
        "wind_speed": 2.0,
        "wind_angle": 90,
        "sun_time": 12,
        "date": "12 Jun"
    }
    """
    try:
        weather = request.json

        # Build weather parameters
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

        # Get line ratings
        results = calculator.calculate_all_line_ratings(weather_params)

        # Generate map HTML
        map_html = map_generator.generate_interactive_map(weather_params, results)

        # Clean NaN values before sending to frontend
        response_data = {
            "map_html": map_html,
            "summary": clean_nan_values(results['summary']),
            "weather": weather_params
        }

        return jsonify(response_data)

    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500

@app.route('/api/map/line/<line_id>', methods=['POST'])
def get_line_map_details(line_id):
    """
    Get detailed information for a specific line (for map clicks)

    Expected JSON body:
    {
        "ambient_temp": 25,
        "wind_speed": 2.0
    }
    """
    try:
        weather = request.json

        weather_params = {
            'Ta': weather.get('ambient_temp', 25),
            'WindVelocity': weather.get('wind_speed', 2.0),
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

        # Get line details for chatbot/side panel
        details = map_generator.get_line_details_for_chat(line_id, weather_params)

        return jsonify(details)

    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500

@app.route('/api/map/outage', methods=['POST'])
def generate_outage_map():
    """
    Generate interactive map with outage simulation visualization

    Expected JSON body:
    {
        "outage_result": {
            "outage_lines": ["L48", "L49"],
            "loading_changes": [...],
            "overloaded_lines": [...],
            ...
        }
    }
    """
    logger.info("Processing outage map request...")

    try:
        # Pre-flight check to ensure data is loaded
        if not load_required_data():
            logger.error("Required data files are not accessible")
            return jsonify({
                "error": "Required map data is unavailable",
                "details": "Could not load GeoJSON files"
            }), 500

        data = request.json
        # Log incoming request for debugging
        try:
            logger.debug(f"Incoming outage map request keys: {list(data.keys()) if isinstance(data, dict) else 'non-dict'}")
        except Exception:
            logger.debug("Incoming outage map request - could not list keys")

        outage_result = None
        if isinstance(data, dict):
            outage_result = data.get('outage_result')
        else:
            # If request.json returned a string or other type, try to coerce
            outage_result = data

        # If outage_result is a JSON string (double-serialized), try to parse it
        if isinstance(outage_result, str):
            try:
                outage_result = json.loads(outage_result)
                logger.debug("Parsed outage_result string into dict")
            except Exception:
                logger.warning("outage_result appears to be a string but could not parse as JSON")

        if not outage_result or not isinstance(outage_result, dict):
            logger.warning(f"No valid outage result provided in request - type={type(outage_result)}")
            return jsonify({"error": "No outage result provided or invalid format", "type": str(type(outage_result))}), 400

        try:
            # Generate outage map visualization
            map_html = map_generator.generate_outage_map(outage_result)

            # Build response
            response = {
                "map_html": map_html,
                "outage_lines": outage_result.get('outage_lines', []),
                "metrics": clean_nan_values(outage_result.get('metrics', {}))
            }

            logger.info(f"Successfully generated outage map for {len(outage_result.get('outage_lines', []))} lines")
            return jsonify(response)

        except Exception as e:
            logger.error(f"Failed to generate outage map: {str(e)}")
            return jsonify({
                "error": "Map generation failed",
                "details": str(e)
            }), 500

    except Exception as e:
        import traceback
        trace = traceback.format_exc()
        logger.error(f"Unexpected error in outage map endpoint: {str(e)}\n{trace}")
        return jsonify({
            "error": str(e),
            "trace": trace,
            "tip": "Server encountered an error processing the request"
        }), 500

@app.route('/api/load-scaling/daily', methods=['GET'])
def analyze_daily_load_scaling():
    """
    Analyze transmission system stress throughout a 24-hour period
    with varying load/generation levels.

    Query parameters:
        hours: Number of hours to analyze (default 24)

    Returns:
        JSON with hourly analysis results and summary
    """
    try:
        from load_scaling_analyzer import LoadScalingAnalyzer

        hours = request.args.get('hours', 24, type=int)

        if hours < 1 or hours > 48:
            return jsonify({
                "success": False,
                "error": "Hours must be between 1 and 48"
            }), 400

        logger.info(f"Analyzing daily load scaling for {hours} hours...")

        # Initialize analyzer
        analyzer = LoadScalingAnalyzer()

        # Run daily analysis
        result = analyzer.analyze_daily_profile(hours)

        # Clean NaN values
        result_clean = clean_nan_values(result)

        logger.info(f"Daily load scaling analysis complete: {result_clean['summary']['hours_converged']}/{hours} hours converged")

        return jsonify(result_clean)

    except Exception as e:
        import traceback
        return jsonify({
            "success": False,
            "error": str(e),
            "trace": traceback.format_exc()
        }), 500


@app.route('/api/load-scaling/hour/<int:hour>', methods=['GET'])
def analyze_single_hour_loading(hour):
    """
    Analyze transmission system at a specific hour of the day.

    Path parameter:
        hour: Hour of day (0-23)

    Returns:
        JSON with analysis results for the specified hour
    """
    try:
        from load_scaling_analyzer import LoadScalingAnalyzer

        if hour < 0 or hour >= 24:
            return jsonify({
                "success": False,
                "error": f"Invalid hour: {hour}. Must be 0-23."
            }), 400

        logger.info(f"Analyzing load scaling for hour {hour}...")

        # Initialize analyzer
        analyzer = LoadScalingAnalyzer()

        # Analyze single hour
        result = analyzer.analyze_single_hour(hour)

        # Clean NaN values
        result_clean = clean_nan_values(result)

        return jsonify(result_clean)

    except Exception as e:
        import traceback
        return jsonify({
            "success": False,
            "error": str(e),
            "trace": traceback.format_exc()
        }), 500


@app.route('/api/load-scaling/profile', methods=['GET'])
def get_load_profile():
    """
    Get the daily load profile without running full analysis.

    Query parameters:
        hours: Number of hours (default 24)

    Returns:
        JSON with load profile data points
    """
    try:
        from load_scaling_analyzer import LoadScalingAnalyzer

        hours = request.args.get('hours', 24, type=int)

        if hours < 1 or hours > 48:
            return jsonify({
                "success": False,
                "error": "Hours must be between 1 and 48"
            }), 400

        # Initialize analyzer
        analyzer = LoadScalingAnalyzer()

        # Get profile
        profile = analyzer.get_load_profile(hours)

        return jsonify({
            "success": True,
            "hours": hours,
            "profile": profile
        })

    except Exception as e:
        import traceback
        return jsonify({
            "success": False,
            "error": str(e),
            "trace": traceback.format_exc()
        }), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
