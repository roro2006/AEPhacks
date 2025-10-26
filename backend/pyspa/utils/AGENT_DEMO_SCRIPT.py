"""
Autonomous Grid Monitor Agent - Demo Script
Demonstrates the agentic capabilities of the enhanced Grid Monitor system
"""
import requests
import json
from datetime import datetime

# Base URL for API
BASE_URL = "http://localhost:5000/api"

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def demo_agent_status():
    """Demonstrate agent status endpoint"""
    print_section("1. AGENT STATUS - Getting Agent State")

    response = requests.get(f"{BASE_URL}/agent/status")

    if response.status_code == 200:
        data = response.json()
        print(f"\n✓ Agent Status: {data['agent_status']}")
        print(f"  Uptime: {data['uptime_seconds']:.1f} seconds")
        print(f"\n  State:")
        print(f"    - Grid History: {data['state']['grid_history_count']} snapshots")
        print(f"    - Patterns Learned: {data['state']['patterns_count']}")
        print(f"    - Actions Recorded: {data['state']['action_history_count']}")
        print(f"    - Active Alerts: {data['state']['active_alerts_count']}")
        print(f"    - Active Recommendations: {data['state']['active_recommendations_count']}")
        print(f"\n  Learning Metrics:")
        print(f"    - Patterns Learned: {data['learning_metrics']['patterns_learned']}")
        print(f"    - Prediction Accuracy: {data['learning_metrics']['prediction_accuracy']:.2%}")
    else:
        print(f"✗ Error: {response.status_code}")
        print(f"  {response.json()}")

def demo_monitoring():
    """Demonstrate grid monitoring with issue detection"""
    print_section("2. GRID MONITORING - Detecting Issues")

    # Simulate hot, calm weather conditions (worst case)
    weather = {
        "ambient_temp": 40,  # Very hot
        "wind_speed": 1.0,   # Low wind
        "wind_angle": 90,
        "sun_time": 14,      # Afternoon
        "date": "12 Jun"
    }

    print("\n  Simulating adverse conditions:")
    print(f"    Temperature: {weather['ambient_temp']}°C")
    print(f"    Wind Speed: {weather['wind_speed']} ft/sec")
    print(f"    Time: {weather['sun_time']}:00")

    response = requests.post(f"{BASE_URL}/agent/monitor", json={"weather": weather})

    if response.status_code == 200:
        data = response.json()
        print(f"\n✓ Analysis complete")
        print(f"  Grid Status: {data['grid_status']}")
        print(f"  Issues Detected: {data['issues_detected']}")

        if data['issues']:
            print("\n  Detected Issues:")
            for i, issue in enumerate(data['issues'], 1):
                print(f"\n    [{i}] {issue['type'].upper()} - Severity: {issue['severity']}")
                print(f"        {issue['description']}")
                if issue.get('affected_lines'):
                    print(f"        Affected: {', '.join(issue['affected_lines'][:5])}")

        if data.get('recommendations'):
            print("\n  Immediate Recommendations:")
            for i, rec in enumerate(data['recommendations'][:3], 1):
                print(f"\n    [{i}] Priority {rec['priority']}: {rec['action']}")
                print(f"        {rec['justification']}")
    else:
        print(f"✗ Error: {response.status_code}")

def demo_predictions():
    """Demonstrate predictive analysis"""
    print_section("3. PREDICTIVE ANALYSIS - Future State Forecasting")

    # Create a weather forecast showing worsening conditions
    forecast = [
        {"ambient_temp": 38, "wind_speed": 1.5, "sun_time": 15, "date": "12 Jun"},
        {"ambient_temp": 40, "wind_speed": 1.2, "sun_time": 16, "date": "12 Jun"},
        {"ambient_temp": 42, "wind_speed": 1.0, "sun_time": 17, "date": "12 Jun"}
    ]

    print("\n  Weather Forecast (next 3 hours):")
    for i, w in enumerate(forecast, 1):
        print(f"    Hour {i}: {w['ambient_temp']}°C, {w['wind_speed']} ft/s wind")

    response = requests.post(f"{BASE_URL}/agent/predictions", json={"weather_forecast": forecast})

    if response.status_code == 200:
        data = response.json()
        print(f"\n✓ Predictions generated")
        print(f"  Forecast Horizon: {data['forecast_horizon_hours']} hours")

        if data.get('predictions'):
            print("\n  Predicted Conditions:")
            for i, pred in enumerate(data['predictions'], 1):
                metrics = pred['predicted_metrics']
                print(f"\n    Hour {i}:")
                print(f"      Average Loading: {metrics['avg_loading']:.1f}%")
                print(f"      Critical Lines: {metrics['critical_count']}")
                print(f"      High Stress Lines: {metrics['high_stress_count']}")
                print(f"      Confidence: {pred['confidence']:.2%}")

                if pred.get('risk_factors'):
                    print(f"      Risk Factors:")
                    for risk in pred['risk_factors']:
                        print(f"        - {risk}")

        if data.get('alerts'):
            print(f"\n  Predictive Alerts Generated: {len(data['alerts'])}")
            for alert in data['alerts']:
                print(f"\n    [{alert['severity'].upper()}] {alert['title']}")
                print(f"      {alert['description']}")
                print(f"      Recommended Actions:")
                for action in alert.get('recommended_actions', [])[:3]:
                    print(f"        • {action}")
    else:
        print(f"✗ Error: {response.status_code}")

def demo_recommendations():
    """Demonstrate AI-powered recommendation generation"""
    print_section("4. RECOMMENDATIONS - AI-Powered Action Items")

    # Use current conditions
    weather = {
        "ambient_temp": 35,
        "wind_speed": 1.5,
        "wind_angle": 90,
        "sun_time": 14,
        "date": "12 Jun"
    }

    response = requests.post(f"{BASE_URL}/agent/recommendations", json={"weather": weather})

    if response.status_code == 200:
        data = response.json()
        print(f"\n✓ Generated {data['recommendations_count']} recommendation(s)")

        if data.get('recommendations'):
            for i, rec in enumerate(data['recommendations'], 1):
                print(f"\n  [{i}] Priority {rec['priority']} - {rec['title']}")
                print(f"      Confidence: {rec['confidence']:.2%}")
                print(f"\n      Description:")
                print(f"        {rec['description']}")
                print(f"\n      Justification:")
                print(f"        {rec['justification']}")
                print(f"\n      Expected Impact:")
                for key, value in rec.get('expected_impact', {}).items():
                    print(f"        - {key}: {value}")
                print(f"\n      Actionable Steps:")
                for step in rec.get('actionable_steps', []):
                    print(f"        • {step}")
    else:
        print(f"✗ Error: {response.status_code}")

def demo_learning():
    """Demonstrate learning from operator actions"""
    print_section("5. LEARNING - Recording Action Outcomes")

    # Simulate an operator taking action
    action_data = {
        "action": {
            "action_type": "load_reduction",
            "description": "Reduced load on line L48 by 15 MW based on agent recommendation",
            "grid_state_before": {
                "avg_loading": 95.0,
                "weather_temp": 38,
                "critical_count": 0,
                "high_stress_count": 2
            }
        },
        "result": {
            "outcome": "successful",
            "impact_score": 0.9,
            "grid_state_after": {
                "avg_loading": 78.0,
                "weather_temp": 38,
                "critical_count": 0,
                "high_stress_count": 0
            }
        }
    }

    print("\n  Recording successful action:")
    print(f"    Action: {action_data['action']['description']}")
    print(f"    Outcome: {action_data['result']['outcome']}")
    print(f"    Impact Score: {action_data['result']['impact_score']}")

    response = requests.post(f"{BASE_URL}/agent/learn", json=action_data)

    if response.status_code == 200:
        data = response.json()
        print(f"\n✓ {data['message']}")
        print(f"  Action ID: {data['action_id']}")
        print(f"  Total Patterns Learned: {data['patterns_learned']}")
        print("\n  The agent will use this pattern to improve future recommendations!")
    else:
        print(f"✗ Error: {response.status_code}")

def demo_chatbot_with_insights():
    """Demonstrate enhanced chatbot with autonomous insights"""
    print_section("6. ENHANCED CHATBOT - AI Assistant with Autonomous Insights")

    weather = {
        "ambient_temp": 35,
        "wind_speed": 1.5,
        "wind_angle": 90,
        "sun_time": 14,
        "date": "12 Jun"
    }

    message = "What's the current status of the grid? Should I be concerned?"

    print(f"\n  User Query: \"{message}\"")

    response = requests.post(
        f"{BASE_URL}/chatbot",
        json={"message": message, "weather": weather}
    )

    if response.status_code == 200:
        data = response.json()
        print(f"\n  AI Response:")
        print(f"    {data['response']}")

        if data.get('autonomous_insights'):
            insights = data['autonomous_insights']
            print(f"\n  Autonomous Insights:")
            print(f"    Grid Status: {insights['grid_status']}")
            print(f"    Issues Detected: {insights['issues_detected']}")

            if insights.get('critical_issues'):
                print(f"\n    Critical Issues:")
                for issue in insights['critical_issues']:
                    print(f"      • {issue['description']}")

            if insights.get('top_recommendations'):
                print(f"\n    Top Recommendations:")
                for rec in insights['top_recommendations']:
                    print(f"      • [P{rec['priority']}] {rec['action']}")
    else:
        print(f"✗ Error: {response.status_code}")

def main():
    """Run all demonstrations"""
    print("\n" + "#" * 70)
    print("#" + " " * 68 + "#")
    print("#" + "  AUTONOMOUS GRID MONITOR AGENT - DEMONSTRATION  ".center(68) + "#")
    print("#" + " " * 68 + "#")
    print("#" * 70)

    print("\nThis demo showcases the agentic capabilities of the Grid Monitor:")
    print("  • Real-time grid monitoring with issue detection")
    print("  • Predictive analysis using IEEE 738 calculations")
    print("  • AI-powered recommendations with justifications")
    print("  • Pattern recognition and learning from outcomes")
    print("  • Enhanced chatbot with autonomous insights")

    print("\n⚠ Make sure the Flask server is running on localhost:5000")
    input("\nPress Enter to start the demonstration...")

    try:
        # Run all demos
        demo_agent_status()
        input("\nPress Enter to continue to Grid Monitoring...")

        demo_monitoring()
        input("\nPress Enter to continue to Predictive Analysis...")

        demo_predictions()
        input("\nPress Enter to continue to Recommendations...")

        demo_recommendations()
        input("\nPress Enter to continue to Learning...")

        demo_learning()
        input("\nPress Enter to continue to Enhanced Chatbot...")

        demo_chatbot_with_insights()

        # Final summary
        print_section("DEMONSTRATION COMPLETE")
        print("\n✓ All agentic capabilities demonstrated successfully!")
        print("\n  Key Features Shown:")
        print("    1. Autonomous monitoring and issue detection")
        print("    2. Predictive analysis with confidence levels")
        print("    3. AI-powered prioritized recommendations")
        print("    4. Learning from operator actions")
        print("    5. Pattern recognition and adaptation")
        print("    6. Enhanced chatbot with proactive insights")

        print("\n  Next Steps:")
        print("    • Explore the API documentation in AGENT_SERVICE_DOCUMENTATION.md")
        print("    • Review the comprehensive unit tests in test_agent_service.py")
        print("    • Integrate with your frontend to display agent insights")
        print("    • Monitor the agent's learning progress over time")

        print("\n" + "=" * 70)

    except requests.exceptions.ConnectionError:
        print("\n✗ Error: Could not connect to Flask server")
        print("  Please ensure the server is running:")
        print("    cd backend && python app.py")
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
