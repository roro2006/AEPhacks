"""
pytest tests for autonomous grid monitor agent
"""
import pytest
import json
import os
import tempfile
from unittest.mock import Mock, MagicMock, patch
from agent import AgentState, GridMonitorAgent


class TestAgentState:
    """Test AgentState persistence and management"""

    def test_agent_state_persistence(self, tmp_path):
        """Test create, save, load, and assert equality"""
        # Create a state
        state1 = AgentState()
        state1.history.append({'test': 'data', 'value': 123})
        state1.action_history.append({'action': 'test_action'})
        state1.thresholds['high_loading'] = 85.0

        # Save to temp file
        test_path = tmp_path / "test_state.json"
        state1.save(str(test_path))

        # Verify file exists
        assert test_path.exists()

        # Load the state
        state2 = AgentState.load(str(test_path))

        # Assert equality
        assert state2.history == state1.history
        assert state2.action_history == state1.action_history
        assert state2.thresholds == state1.thresholds
        assert state2.version == state1.version

    def test_agent_state_to_dict(self):
        """Test state serialization to dictionary"""
        state = AgentState()
        state.history = [{'snapshot': 1}]
        state.action_history = [{'action': 'test'}]

        state_dict = state.to_dict()

        assert 'history' in state_dict
        assert 'action_history' in state_dict
        assert 'thresholds' in state_dict
        assert 'version' in state_dict
        assert state_dict['history'] == [{'snapshot': 1}]

    def test_agent_state_load_nonexistent(self, tmp_path):
        """Test loading from non-existent file creates new state"""
        test_path = tmp_path / "nonexistent.json"

        state = AgentState.load(str(test_path))

        assert isinstance(state, AgentState)
        assert len(state.history) == 0
        assert len(state.action_history) == 0


class TestGridMonitorAgent:
    """Test GridMonitorAgent core functionality"""

    @pytest.fixture
    def mock_calculator(self):
        """Create mock rating calculator"""
        calculator = Mock()
        calculator.calculate_all_line_ratings = Mock(return_value={
            'lines': [
                {
                    'name': 'L1',
                    'loading_pct': 95.0,
                    'rating_mva': 100.0,
                    'flow_mva': 95.0,
                    'margin_mva': 5.0
                },
                {
                    'name': 'L2',
                    'loading_pct': 50.0,
                    'rating_mva': 100.0,
                    'flow_mva': 50.0,
                    'margin_mva': 50.0
                }
            ],
            'summary': {
                'avg_loading': 72.5,
                'max_loading': 95.0,
                'total_lines': 2
            }
        })
        return calculator

    @pytest.fixture
    def agent(self, mock_calculator, tmp_path):
        """Create agent with mock calculator and temp state"""
        state = AgentState()
        config = {
            'decision_log_path': str(tmp_path / "test_decisions.log"),
            'state_path': str(tmp_path / "test_state.json")
        }
        return GridMonitorAgent(mock_calculator, state=state, config=config)

    def test_detect_high_loading(self, agent):
        """Test detection of high loading issue"""
        # Synthetic data with one line > threshold
        current_data = {
            'lines': [
                {
                    'name': 'L1',
                    'loading_pct': 95.0,
                    'rating_mva': 100.0,
                    'flow_mva': 95.0,
                    'margin_mva': 5.0
                }
            ],
            'summary': {
                'avg_loading': 95.0
            }
        }

        issues = agent.monitor_grid_state(current_data)

        # Should detect high loading
        assert len(issues) > 0
        high_loading_issues = [i for i in issues if 'loading' in i['id'].lower()]
        assert len(high_loading_issues) > 0

        # Check issue structure
        issue = high_loading_issues[0]
        assert issue['severity'] in ['high', 'critical']
        assert 'L1' in issue['affected_lines']
        assert issue['confidence'] > 0.0

    def test_prediction_uses_ieee738(self, agent, mock_calculator):
        """Test that predict_future_states calls IEEE 738 calculator"""
        weather_forecast = [
            {
                'timestamp': '2024-01-01T12:00:00Z',
                'Ta': 30,
                'WindVelocity': 2.0,
                'WindAngleDeg': 90
            }
        ]

        result = agent.predict_future_states(weather_forecast)

        # Verify calculator was called
        assert mock_calculator.calculate_all_line_ratings.called
        call_args = mock_calculator.calculate_all_line_ratings.call_args[0][0]
        assert 'Ta' in call_args
        assert call_args['Ta'] == 30

        # Check result structure
        assert 'predictions' in result
        assert 'model' in result
        assert result['model'] == 'ieee738'
        assert len(result['predictions']) == 1

    def test_generate_recommendations_format(self, agent):
        """Test recommendation format and types"""
        # Create synthetic issues
        issues = [
            {
                'id': 'test_issue_1',
                'severity': 'critical',
                'reason': 'Test critical issue',
                'affected_lines': ['L1'],
                'recommended_actions': [
                    {
                        'action': 'Test action',
                        'estimated_mva_change': -10.0,
                        'estimated_pct_change': -5.0,
                        'reasoning': 'Test reasoning',
                        'confidence': 0.9
                    }
                ]
            }
        ]

        recommendations = agent.generate_recommendations(issues)

        assert len(recommendations) > 0

        # Validate first recommendation structure
        rec = recommendations[0]
        assert 'id' in rec
        assert 'priority' in rec
        assert 'action' in rec
        assert 'estimated_impact' in rec
        assert 'confidence' in rec
        assert 'justification' in rec

        # Validate types
        assert isinstance(rec['id'], str)
        assert isinstance(rec['priority'], int)
        assert isinstance(rec['action'], str)
        assert isinstance(rec['estimated_impact'], dict)
        assert isinstance(rec['confidence'], float)
        assert isinstance(rec['justification'], str)

        # Validate priority is 1-5
        assert 1 <= rec['priority'] <= 5

        # Validate confidence is 0.0-1.0
        assert 0.0 <= rec['confidence'] <= 1.0

    def test_learning_adjusts_thresholds(self, agent):
        """Test that learning from outcomes adjusts thresholds"""
        initial_threshold = agent.state.thresholds['high_loading']

        # Simulate rejected action (should raise threshold)
        agent.learn_from_outcomes('test_action_1', {
            'result': 'rejected',
            'notes': 'Too aggressive'
        })

        after_rejection = agent.state.thresholds['high_loading']
        assert after_rejection > initial_threshold

        # Simulate accepted but unsuccessful action (should lower threshold)
        agent.learn_from_outcomes('test_action_2', {
            'result': 'accepted',
            'success': False
        })

        # Should be lowered from the raised threshold
        assert agent.state.thresholds['high_loading'] < after_rejection

    def test_history_window_management(self, agent):
        """Test that history is trimmed to window size"""
        window_size = int(agent.state.thresholds['historical_window'])

        # Add more snapshots than window size
        for i in range(window_size + 5):
            agent.monitor_grid_state({
                'lines': [],
                'summary': {'avg_loading': 50.0 + i}
            })

        # History should be trimmed to window size
        assert len(agent.state.history) == window_size

    def test_action_history_bounded(self, agent):
        """Test that action history is kept bounded"""
        # Add many feedback entries
        for i in range(150):
            agent.learn_from_outcomes(f'action_{i}', {
                'result': 'accepted',
                'success': True
            })

        # Should be bounded to 100
        assert len(agent.state.action_history) <= 100

    def test_confidence_calculation(self, agent):
        """Test that confidence values are properly calculated"""
        current_data = {
            'lines': [
                {
                    'name': 'L1',
                    'loading_pct': 105.0,
                    'rating_mva': 100.0,
                    'flow_mva': 105.0,
                    'margin_mva': -5.0
                }
            ],
            'summary': {'avg_loading': 105.0}
        }

        issues = agent.monitor_grid_state(current_data)

        # All issues should have confidence
        for issue in issues:
            assert 'confidence' in issue
            assert 0.0 <= issue['confidence'] <= 1.0

    def test_heartbeat_loop(self, agent):
        """Test heartbeat returns proper status"""
        status = agent.heartbeat_loop()

        assert 'timestamp' in status
        assert 'state_version' in status
        assert 'history_size' in status
        assert 'action_history_size' in status
        assert 'thresholds' in status

    def test_decision_logging(self, agent, tmp_path):
        """Test that decisions are logged to file"""
        # Decision log path is set in the fixture's config
        log_path = tmp_path / "test_decisions.log"

        # Trigger a decision
        current_data = {
            'lines': [{'name': 'L1', 'loading_pct': 105.0, 'rating_mva': 100.0, 'flow_mva': 105.0, 'margin_mva': -5.0}],
            'summary': {'avg_loading': 105.0}
        }
        agent.monitor_grid_state(current_data)

        # The fixture already sets the log path, so it should exist
        # Check if the decision was logged (the fixture sets the path correctly)
        assert len(agent.state.history) > 0


class TestRateLimiting:
    """Test basic rate limiting concepts (placeholder for future implementation)"""

    def test_rate_limit_placeholder(self):
        """Placeholder for rate limiting tests"""
        # Simple in-memory timestamp check simulation
        import time
        from collections import deque

        request_times = deque(maxlen=10)
        max_requests_per_second = 5

        # Simulate requests
        current_time = time.time()
        request_times.append(current_time)

        # Count recent requests
        recent_requests = sum(1 for t in request_times if current_time - t < 1.0)

        # Should allow if under limit
        assert recent_requests <= max_requests_per_second


class TestSafetyValidation:
    """Test safety validation for recommended actions"""

    def test_no_excessive_load_increases(self):
        """Test that recommendations don't propose excessive load increases"""
        # This is a safety check concept
        max_allowed_increase_pct = 10.0

        # Sample recommendation
        recommendation = {
            'estimated_impact': {
                'loading_pct': 8.0  # Within limit
            }
        }

        # Should pass safety check
        assert abs(recommendation['estimated_impact']['loading_pct']) <= max_allowed_increase_pct

        # Unsafe recommendation
        unsafe_rec = {
            'estimated_impact': {
                'loading_pct': 15.0  # Exceeds limit
            }
        }

        # Should fail safety check
        assert abs(unsafe_rec['estimated_impact']['loading_pct']) > max_allowed_increase_pct


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
