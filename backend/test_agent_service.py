"""
Comprehensive Unit Tests for Autonomous Grid Monitor Agent Service
"""
import unittest
from unittest.mock import Mock, MagicMock, patch
import json
from datetime import datetime, timedelta
from agent_service import (
    GridMonitorAgent,
    AgentState,
    GridMetrics,
    PatternData,
    ActionRecord,
    Alert,
    Recommendation,
    Prediction
)


class TestAgentState(unittest.TestCase):
    """Test AgentState class"""

    def test_agent_state_initialization(self):
        """Test that AgentState initializes with correct defaults"""
        state = AgentState()

        self.assertEqual(len(state.grid_history), 0)
        self.assertEqual(len(state.recognized_patterns), 0)
        self.assertEqual(len(state.action_history), 0)
        self.assertEqual(state.thresholds['loading']['normal'], 60.0)
        self.assertEqual(state.thresholds['loading']['caution'], 90.0)
        self.assertEqual(state.total_actions, 0)
        self.assertEqual(state.successful_predictions, 0)

    def test_agent_state_to_dict(self):
        """Test state serialization to dictionary"""
        state = AgentState()
        state.total_actions = 5
        state.successful_predictions = 3
        state.total_predictions = 5

        state_dict = state.to_dict()

        self.assertIn('grid_history_count', state_dict)
        self.assertIn('patterns_count', state_dict)
        self.assertIn('thresholds', state_dict)
        self.assertIn('prediction_accuracy', state_dict)
        self.assertEqual(state_dict['prediction_accuracy'], 0.6)


class TestGridMetrics(unittest.TestCase):
    """Test GridMetrics model"""

    def test_grid_metrics_creation(self):
        """Test creating a grid metrics snapshot"""
        metrics = GridMetrics(
            timestamp=datetime.now().isoformat(),
            total_lines=77,
            critical_count=2,
            high_stress_count=5,
            caution_count=10,
            normal_count=60,
            avg_loading=45.5,
            max_loading=95.2,
            max_loading_line="L48",
            weather_temp=35.0,
            weather_wind_speed=1.5,
            weather_wind_angle=90,
            weather_sun_time=14
        )

        self.assertEqual(metrics.total_lines, 77)
        self.assertEqual(metrics.critical_count, 2)
        self.assertEqual(metrics.avg_loading, 45.5)
        self.assertEqual(metrics.weather_temp, 35.0)


class TestGridMonitorAgent(unittest.TestCase):
    """Test GridMonitorAgent core functionality"""

    def setUp(self):
        """Set up test fixtures"""
        # Mock rating calculator
        self.mock_calculator = Mock()

        # Mock Anthropic client
        with patch('agent_service.Anthropic'):
            self.agent = GridMonitorAgent(rating_calculator=self.mock_calculator)

    def test_agent_initialization(self):
        """Test agent initializes correctly"""
        self.assertIsNotNone(self.agent)
        self.assertIsInstance(self.agent.state, AgentState)
        self.assertEqual(self.agent.rating_calculator, self.mock_calculator)

    def test_update_grid_history(self):
        """Test updating grid history with new data"""
        current_data = {
            'summary': {
                'total_lines': 77,
                'critical_count': 1,
                'high_stress_count': 3,
                'caution_count': 8,
                'normal_count': 65,
                'avg_loading': 42.5,
                'max_loading': 92.3,
                'max_loading_line': 'L48'
            }
        }

        weather = {
            'Ta': 30,
            'WindVelocity': 2.0,
            'WindAngleDeg': 90,
            'SunTime': 12
        }

        self.agent.update_grid_history(current_data, weather)

        self.assertEqual(len(self.agent.state.grid_history), 1)
        latest = self.agent.state.grid_history[0]
        self.assertEqual(latest.total_lines, 77)
        self.assertEqual(latest.critical_count, 1)
        self.assertEqual(latest.weather_temp, 30)

    def test_monitor_grid_state_critical_overload(self):
        """Test detection of critical overloads"""
        current_data = {
            'lines': [
                {
                    'name': 'L48',
                    'stress_level': 'critical',
                    'loading_pct': 105.0,
                    'margin_mva': -5.0
                },
                {
                    'name': 'L49',
                    'stress_level': 'normal',
                    'loading_pct': 45.0,
                    'margin_mva': 50.0
                }
            ],
            'summary': {
                'total_lines': 2,
                'critical_count': 1,
                'high_stress_count': 0,
                'caution_count': 0,
                'normal_count': 1,
                'avg_loading': 75.0,
                'max_loading': 105.0,
                'max_loading_line': 'L48'
            }
        }

        weather = {'Ta': 25, 'WindVelocity': 2.0}

        result = self.agent.monitor_grid_state(current_data, weather)

        self.assertIn('issues', result)
        self.assertGreater(result['issues_detected'], 0)

        # Check for critical overload issue
        critical_issues = [i for i in result['issues'] if i['type'] == 'critical_overload']
        self.assertGreater(len(critical_issues), 0)
        self.assertEqual(critical_issues[0]['severity'], 'emergency')

    def test_monitor_grid_state_high_stress(self):
        """Test detection of high stress conditions"""
        current_data = {
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

        weather = {'Ta': 25, 'WindVelocity': 2.0}

        result = self.agent.monitor_grid_state(current_data, weather)

        high_stress_issues = [i for i in result['issues'] if i['type'] == 'high_stress']
        self.assertGreater(len(high_stress_issues), 0)

    def test_monitor_grid_state_adverse_weather(self):
        """Test detection of adverse weather conditions"""
        current_data = {
            'lines': [
                {
                    'name': 'L48',
                    'stress_level': 'caution',
                    'loading_pct': 75.0,
                    'margin_mva': 10.0
                }
            ],
            'summary': {
                'total_lines': 1,
                'critical_count': 0,
                'high_stress_count': 0,
                'caution_count': 1,
                'normal_count': 0,
                'avg_loading': 75.0,
                'max_loading': 75.0,
                'max_loading_line': 'L48'
            }
        }

        # Hot and calm weather
        weather = {'Ta': 40, 'WindVelocity': 1.0}

        result = self.agent.monitor_grid_state(current_data, weather)

        adverse_weather_issues = [i for i in result['issues'] if i['type'] == 'adverse_weather']
        self.assertGreater(len(adverse_weather_issues), 0)

    def test_predict_future_states(self):
        """Test future state prediction"""
        # Mock rating calculator response
        mock_future_ratings = {
            'lines': [
                {
                    'name': 'L48',
                    'stress_level': 'critical',
                    'loading_pct': 102.0,
                    'margin_mva': -2.0
                }
            ],
            'summary': {
                'total_lines': 1,
                'critical_count': 1,
                'high_stress_count': 0,
                'caution_count': 0,
                'normal_count': 0,
                'avg_loading': 102.0,
                'max_loading': 102.0,
                'max_loading_line': 'L48'
            }
        }

        self.mock_calculator.calculate_all_line_ratings = Mock(return_value=mock_future_ratings)

        weather_forecast = [
            {'Ta': 35, 'WindVelocity': 1.5, 'WindAngleDeg': 90, 'SunTime': 13, 'Date': '12 Jun'},
            {'Ta': 40, 'WindVelocity': 1.0, 'WindAngleDeg': 90, 'SunTime': 14, 'Date': '12 Jun'}
        ]

        result = self.agent.predict_future_states(weather_forecast)

        self.assertIn('predictions', result)
        self.assertIn('alerts', result)
        self.assertEqual(len(result['predictions']), 2)

        # Check that alerts were generated for critical conditions
        self.assertGreater(len(result['alerts']), 0)

    def test_generate_recommendations_rule_based(self):
        """Test rule-based recommendation generation (fallback)"""
        issues = [
            {
                'severity': 'critical',
                'type': 'high_stress',
                'description': 'Line L48 under high stress',
                'affected_lines': ['L48']
            }
        ]

        # Disable AI by mocking client to raise exception
        self.agent.client.messages.create = Mock(side_effect=Exception("API Error"))

        result = self.agent.generate_recommendations(issues)

        self.assertIn('recommendations', result)
        self.assertGreater(len(result['recommendations']), 0)

        rec = result['recommendations'][0]
        self.assertIn('title', rec)
        self.assertIn('priority', rec)
        self.assertIn('confidence', rec)

    def test_learn_from_outcomes_successful(self):
        """Test learning from successful actions"""
        action = ActionRecord(
            action_id='test_action_1',
            timestamp=datetime.now().isoformat(),
            action_type='alert',
            description='Reduced load on L48',
            grid_state_before={'avg_loading': 95.0, 'weather_temp': 35}
        )

        result = {
            'outcome': 'successful',
            'impact_score': 0.9,
            'grid_state_after': {'avg_loading': 75.0}
        }

        initial_pattern_count = len(self.agent.state.recognized_patterns)

        self.agent.learn_from_outcomes(action, result)

        # Check that action was recorded
        self.assertEqual(len(self.agent.state.action_history), 1)

        # Check that pattern was learned
        self.assertGreater(len(self.agent.state.recognized_patterns), initial_pattern_count)

    def test_learn_from_outcomes_failed(self):
        """Test learning from failed actions"""
        action = ActionRecord(
            action_id='test_action_2',
            timestamp=datetime.now().isoformat(),
            action_type='alert',
            description='Attempted load reduction',
            grid_state_before={'avg_loading': 95.0}
        )

        result = {
            'outcome': 'failed',
            'impact_score': 0.1,
            'grid_state_after': {'avg_loading': 95.0}
        }

        initial_threshold = self.agent.state.thresholds['loading']['caution']

        self.agent.learn_from_outcomes(action, result)

        # Check that threshold was adjusted (became more conservative)
        self.assertLess(
            self.agent.state.thresholds['loading']['caution'],
            initial_threshold
        )

    def test_pattern_matching(self):
        """Test pattern recognition and matching"""
        # Add a known pattern
        pattern = PatternData(
            pattern_type='weather_impact',
            trigger_conditions={
                'temp_range': [30, 40],
                'avg_loading_range': [80, 100]
            },
            observed_outcomes=[
                {'action': 'load reduction', 'impact': 0.8}
            ],
            confidence=0.85,
            occurrence_count=5,
            last_seen=datetime.now().isoformat(),
            avg_severity=0.75
        )

        self.agent.state.recognized_patterns.append(pattern)

        # Test with matching conditions
        current_data = {
            'summary': {
                'avg_loading': 85.0
            }
        }

        weather = {'Ta': 35, 'WindVelocity': 2.0}

        issues = self.agent._match_patterns(current_data, weather)

        # Should detect pattern match
        pattern_matches = [i for i in issues if i['type'] == 'pattern_match']
        self.assertGreater(len(pattern_matches), 0)

    def test_calculate_grid_status(self):
        """Test grid status calculation"""
        # Emergency status
        summary = {'critical_count': 2, 'high_stress_count': 1}
        self.assertEqual(self.agent._calculate_grid_status(summary), 'EMERGENCY')

        # Critical status
        summary = {'critical_count': 0, 'high_stress_count': 5}
        self.assertEqual(self.agent._calculate_grid_status(summary), 'CRITICAL')

        # High stress status
        summary = {'critical_count': 0, 'high_stress_count': 1}
        self.assertEqual(self.agent._calculate_grid_status(summary), 'HIGH_STRESS')

        # Caution status
        summary = {'critical_count': 0, 'high_stress_count': 0, 'caution_count': 6}
        self.assertEqual(self.agent._calculate_grid_status(summary), 'CAUTION')

        # Normal status
        summary = {'critical_count': 0, 'high_stress_count': 0, 'caution_count': 2}
        self.assertEqual(self.agent._calculate_grid_status(summary), 'NORMAL')

    def test_get_agent_status(self):
        """Test agent status reporting"""
        status = self.agent.get_agent_status()

        self.assertIn('agent_status', status)
        self.assertIn('uptime_seconds', status)
        self.assertIn('state', status)
        self.assertIn('active_alerts', status)
        self.assertIn('active_recommendations', status)
        self.assertIn('learning_metrics', status)

        self.assertEqual(status['agent_status'], 'active')

    def test_id_generation(self):
        """Test unique ID generation"""
        alert_id_1 = self.agent._generate_id('alert')
        alert_id_2 = self.agent._generate_id('alert')

        self.assertNotEqual(alert_id_1, alert_id_2)
        self.assertTrue(alert_id_1.startswith('alert_'))
        self.assertTrue(alert_id_2.startswith('alert_'))

    def test_detect_trends_increasing_loading(self):
        """Test detection of increasing loading trends"""
        # Add historical data with increasing trend
        for i in range(10):
            metrics = GridMetrics(
                timestamp=datetime.now().isoformat(),
                total_lines=77,
                critical_count=0,
                high_stress_count=0,
                caution_count=0,
                normal_count=77,
                avg_loading=50.0 + i * 5.0,  # Increasing by 5% each snapshot
                max_loading=60.0 + i * 5.0,
                max_loading_line='L48',
                weather_temp=25,
                weather_wind_speed=2.0,
                weather_wind_angle=90,
                weather_sun_time=12
            )
            self.agent.state.grid_history.append(metrics)

        issues = self.agent._detect_trends()

        # Should detect increasing trend
        trend_issues = [i for i in issues if i['type'] == 'increasing_trend']
        self.assertGreater(len(trend_issues), 0)

    def test_risk_factor_identification(self):
        """Test identification of risk factors in predictions"""
        future_ratings = {
            'summary': {
                'critical_count': 2,
                'avg_loading': 85.0
            },
            'lines': []
        }

        weather = {
            'Ta': 45,  # Extreme temperature
            'WindVelocity': 0.5  # Very low wind
        }

        risks = self.agent._identify_risk_factors(future_ratings, weather)

        self.assertGreater(len(risks), 0)
        # Should identify multiple risk factors
        self.assertTrue(any('overload' in r.lower() for r in risks))
        self.assertTrue(any('temperature' in r.lower() for r in risks))
        self.assertTrue(any('wind' in r.lower() for r in risks))

    def test_preventive_actions_generation(self):
        """Test generation of preventive actions"""
        future_ratings = {
            'summary': {
                'critical_count': 2,
                'high_stress_count': 3
            },
            'lines': [
                {'name': 'L48', 'stress_level': 'critical'},
                {'name': 'L49', 'stress_level': 'critical'}
            ]
        }

        actions = self.agent._generate_preventive_actions(future_ratings)

        self.assertGreater(len(actions), 0)
        # Should recommend specific actions
        self.assertTrue(any('L48' in a or 'L49' in a for a in actions))


class TestPydanticModels(unittest.TestCase):
    """Test Pydantic model validation"""

    def test_alert_model(self):
        """Test Alert model validation"""
        alert = Alert(
            alert_id='alert_001',
            timestamp=datetime.now().isoformat(),
            severity='critical',
            title='Line overload detected',
            description='Line L48 is overloaded at 105%',
            affected_lines=['L48'],
            recommended_actions=['Reduce load immediately'],
            confidence=0.9
        )

        self.assertEqual(alert.severity, 'critical')
        self.assertEqual(len(alert.affected_lines), 1)
        self.assertEqual(alert.confidence, 0.9)

    def test_recommendation_model(self):
        """Test Recommendation model validation"""
        rec = Recommendation(
            rec_id='rec_001',
            timestamp=datetime.now().isoformat(),
            priority=1,
            title='Immediate load reduction',
            description='Reduce loading on L48',
            justification='Line is at critical stress',
            expected_impact={'loading_reduction': 10},
            confidence=0.85,
            actionable_steps=['Contact dispatch', 'Reduce generation']
        )

        self.assertEqual(rec.priority, 1)
        self.assertEqual(rec.confidence, 0.85)
        self.assertEqual(len(rec.actionable_steps), 2)

    def test_prediction_model(self):
        """Test Prediction model validation"""
        pred = Prediction(
            prediction_id='pred_001',
            timestamp=datetime.now().isoformat(),
            forecast_time=(datetime.now() + timedelta(hours=2)).isoformat(),
            predicted_metrics={'avg_loading': 95.0},
            confidence=0.8,
            risk_factors=['High temperature', 'Low wind'],
            preventive_actions=['Monitor closely']
        )

        self.assertEqual(pred.confidence, 0.8)
        self.assertEqual(len(pred.risk_factors), 2)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
