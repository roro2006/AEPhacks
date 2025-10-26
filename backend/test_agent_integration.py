"""
Integration test for Agent Service API Endpoints
Tests that the Flask API endpoints work correctly with the agent
"""
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_agent_service_integration():
    """Test that agent service initializes and basic functions work"""
    print("=" * 70)
    print("AUTONOMOUS GRID MONITOR AGENT - INTEGRATION TEST")
    print("=" * 70)

    # Test 1: Import and Initialize
    print("\n[1/6] Testing imports and initialization...")
    try:
        from agent_service import GridMonitorAgent, AgentState
        from rating_calculator import RatingCalculator
        from data_loader import DataLoader

        # Initialize components
        data_loader = DataLoader()
        calculator = RatingCalculator(data_loader)

        # Try to initialize agent (may fail if no API key)
        try:
            agent = GridMonitorAgent(rating_calculator=calculator)
            print("✓ Agent initialized successfully")
        except ValueError as e:
            print(f"⚠ Agent initialization skipped: {e}")
            print("  (This is OK if ANTHROPIC_API_KEY is not set)")
            agent = None

    except Exception as e:
        print(f"✗ Failed to import/initialize: {e}")
        return False

    # Test 2: Data Structures
    print("\n[2/6] Testing data structures...")
    try:
        state = AgentState()
        state_dict = state.to_dict()
        assert 'thresholds' in state_dict
        assert 'grid_history_count' in state_dict
        print("✓ AgentState working correctly")
    except Exception as e:
        print(f"✗ AgentState test failed: {e}")
        return False

    # Test 3: Grid Monitoring (if agent available)
    if agent:
        print("\n[3/6] Testing grid monitoring...")
        try:
            # Create sample grid data
            sample_data = {
                'lines': [
                    {
                        'name': 'L48',
                        'stress_level': 'high',
                        'loading_pct': 95.0,
                        'margin_mva': 2.0
                    }
                ],
                'summary': {
                    'total_lines': 1,
                    'critical_count': 0,
                    'high_stress_count': 1,
                    'caution_count': 0,
                    'normal_count': 0,
                    'avg_loading': 95.0,
                    'max_loading': 95.0,
                    'max_loading_line': 'L48'
                }
            }

            sample_weather = {'Ta': 35, 'WindVelocity': 1.5}

            result = agent.monitor_grid_state(sample_data, sample_weather)

            assert 'issues' in result
            assert 'grid_status' in result
            print(f"✓ Monitoring detected {result['issues_detected']} issue(s)")
            print(f"  Grid status: {result['grid_status']}")

        except Exception as e:
            print(f"✗ Monitoring test failed: {e}")
            return False
    else:
        print("\n[3/6] Skipping grid monitoring test (no agent)")

    # Test 4: Predictions (if agent and calculator available)
    if agent and calculator:
        print("\n[4/6] Testing predictions...")
        try:
            # Use actual calculator to get real predictions
            forecast = [
                {
                    'Ta': 35,
                    'WindVelocity': 1.5,
                    'WindAngleDeg': 90,
                    'SunTime': 13,
                    'Date': '12 Jun',
                    'Emissivity': 0.8,
                    'Absorptivity': 0.8,
                    'Direction': 'EastWest',
                    'Atmosphere': 'Clear',
                    'Elevation': 1000,
                    'Latitude': 27
                }
            ]

            result = agent.predict_future_states(forecast)

            assert 'predictions' in result
            assert 'forecast_horizon_hours' in result
            print(f"✓ Generated {len(result['predictions'])} prediction(s)")
            if result.get('alerts'):
                print(f"  Alerts generated: {len(result['alerts'])}")

        except Exception as e:
            print(f"✗ Prediction test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    else:
        print("\n[4/6] Skipping prediction test (no agent/calculator)")

    # Test 5: Recommendations (if agent available)
    if agent:
        print("\n[5/6] Testing recommendations...")
        try:
            sample_issues = [
                {
                    'severity': 'critical',
                    'type': 'high_stress',
                    'description': 'Line L48 under high stress',
                    'affected_lines': ['L48']
                }
            ]

            result = agent.generate_recommendations(sample_issues)

            assert 'recommendations' in result
            assert 'recommendations_count' in result
            print(f"✓ Generated {result['recommendations_count']} recommendation(s)")

            if result['recommendations_count'] > 0:
                rec = result['recommendations'][0]
                print(f"  Top recommendation: {rec['title']}")
                print(f"  Priority: {rec['priority']}, Confidence: {rec['confidence']}")

        except Exception as e:
            print(f"✗ Recommendation test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    else:
        print("\n[5/6] Skipping recommendation test (no agent)")

    # Test 6: Learning (if agent available)
    if agent:
        print("\n[6/6] Testing learning mechanism...")
        try:
            from agent_service import ActionRecord
            from datetime import datetime

            action = ActionRecord(
                action_id='test_integration_1',
                timestamp=datetime.now().isoformat(),
                action_type='test',
                description='Integration test action',
                grid_state_before={'avg_loading': 95.0}
            )

            result = {
                'outcome': 'successful',
                'impact_score': 0.9,
                'grid_state_after': {'avg_loading': 75.0}
            }

            initial_patterns = len(agent.state.recognized_patterns)
            agent.learn_from_outcomes(action, result)

            assert len(agent.state.action_history) >= 1
            print("✓ Learning mechanism working")
            print(f"  Action history size: {len(agent.state.action_history)}")
            print(f"  Patterns learned: {len(agent.state.recognized_patterns)}")

        except Exception as e:
            print(f"✗ Learning test failed: {e}")
            return False
    else:
        print("\n[6/6] Skipping learning test (no agent)")

    # Summary
    print("\n" + "=" * 70)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 70)

    if agent:
        status = agent.get_agent_status()
        print(f"Agent Status: {status['agent_status']}")
        print(f"Grid History: {status['state']['grid_history_count']} snapshots")
        print(f"Patterns: {status['state']['patterns_count']} patterns")
        print(f"Actions: {status['state']['action_history_count']} recorded")
        print(f"Active Alerts: {status['state']['active_alerts_count']}")
        print(f"Active Recommendations: {status['state']['active_recommendations_count']}")
        print("\n✓ ALL INTEGRATION TESTS PASSED!")
    else:
        print("⚠ Limited testing (agent not initialized)")
        print("  Set ANTHROPIC_API_KEY in .env for full testing")
        print("\n✓ BASIC INTEGRATION TESTS PASSED!")

    return True


if __name__ == '__main__':
    success = test_agent_service_integration()
    sys.exit(0 if success else 1)
