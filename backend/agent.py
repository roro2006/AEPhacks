"""
Autonomous Grid Monitor Agent
Implements persistent state, monitoring, prediction, and learning capabilities
"""
import json
import logging
import os
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field, asdict
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class AgentState:
    """
    Persistent agent state with history, patterns, and thresholds

    Attributes:
        history: List of grid state snapshots for trend analysis
        action_history: List of operator actions and outcomes for learning
        thresholds: Configurable detection thresholds
        version: State schema version for compatibility
        last_updated: ISO timestamp of last state update
    """
    history: List[Dict[str, Any]] = field(default_factory=list)
    action_history: List[Dict[str, Any]] = field(default_factory=list)
    thresholds: Dict[str, float] = field(default_factory=lambda: {
        'high_loading': 90.0,
        'critical_loading': 100.0,
        'trend_slope_threshold': 5.0,  # % increase per snapshot
        'rating_decline_threshold': 10.0,  # % rating decline
        'historical_window': 10  # snapshots for trend analysis
    })
    version: str = "1.0.0"
    last_updated: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for JSON serialization"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentState':
        """Create AgentState from dictionary"""
        return cls(**data)

    def save(self, path: str) -> None:
        """
        Persist state to JSON file

        Args:
            path: File path for state persistence
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(path), exist_ok=True)

            # Update timestamp
            self.last_updated = datetime.utcnow().isoformat()

            # Write atomically with temp file
            temp_path = path + '.tmp'
            with open(temp_path, 'w') as f:
                json.dump(self.to_dict(), f, indent=2)

            # Atomic rename
            os.replace(temp_path, path)
            logger.info(f"Agent state saved to {path}")

        except Exception as e:
            logger.error(f"Failed to save agent state: {e}")
            raise

    @classmethod
    def load(cls, path: str) -> 'AgentState':
        """
        Load state from JSON file

        Args:
            path: File path to load state from

        Returns:
            Loaded AgentState instance or new instance if file doesn't exist
        """
        if not os.path.exists(path):
            logger.info(f"No existing state at {path}, creating new state")
            return cls()

        try:
            with open(path, 'r') as f:
                data = json.load(f)
            logger.info(f"Agent state loaded from {path}")
            return cls.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to load agent state: {e}, creating new state")
            return cls()


class GridMonitorAgent:
    """
    Autonomous grid monitoring agent with prediction and learning capabilities

    Uses existing IEEE 738 calculator for rating predictions.
    Detects issues, generates recommendations, and learns from operator feedback.
    """

    def __init__(
        self,
        calculator,
        state: Optional[AgentState] = None,
        logger: Optional[logging.Logger] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize grid monitor agent

        Args:
            calculator: RatingCalculator instance with IEEE 738 capabilities
            state: AgentState instance (creates new if None)
            logger: Logger instance (uses module logger if None)
            config: Configuration overrides
        """
        self.calculator = calculator
        self.state = state or AgentState()
        self.logger = logger or globals()['logger']
        self.config = config or {}
        self.decision_log_path = self.config.get(
            'decision_log_path',
            'backend/data/agent_decisions.log'
        )

        # Ensure decision log directory exists
        os.makedirs(os.path.dirname(self.decision_log_path), exist_ok=True)

        # Set up decision logger
        self.decision_logger = logging.getLogger('agent_decisions')
        if not self.decision_logger.handlers:
            handler = logging.FileHandler(self.decision_log_path)
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.decision_logger.addHandler(handler)
            self.decision_logger.setLevel(logging.INFO)

    def _log_decision(self, action: str, details: Dict[str, Any]) -> None:
        """Log autonomous decision to audit trail"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'action': action,
            'details': details,
            'state_snapshot': {
                'history_size': len(self.state.history),
                'action_history_size': len(self.state.action_history),
                'thresholds': self.state.thresholds
            }
        }
        self.decision_logger.info(json.dumps(log_entry))

    def monitor_grid_state(self, current_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Monitor current grid state and detect issues

        Args:
            current_data: Current grid data with 'lines' and 'summary' keys
                         from calculator.calculate_all_line_ratings()

        Returns:
            List of detected issues, each with:
                - id: Unique issue identifier
                - severity: 'low', 'medium', 'high', 'critical'
                - reason: Human-readable description
                - affected_lines: List of line names
                - metric_snapshots: Relevant metrics
                - timestamp: ISO timestamp
                - confidence: Float 0.0-1.0
                - recommended_actions: List of action dicts with impact estimates
        """
        detected_issues = []
        timestamp = datetime.utcnow().isoformat()

        # Add current state to history
        self.state.history.append({
            'timestamp': timestamp,
            'summary': current_data.get('summary', {}),
            'line_count': len(current_data.get('lines', []))
        })

        # Trim history to window size
        window = int(self.state.thresholds.get('historical_window', 10))
        if len(self.state.history) > window:
            self.state.history = self.state.history[-window:]

        lines = current_data.get('lines', [])
        summary = current_data.get('summary', {})

        # Issue 1: High Loading Detection
        high_loading_threshold = self.state.thresholds.get('high_loading', 90.0)
        critical_loading_threshold = self.state.thresholds.get('critical_loading', 100.0)

        critical_lines = [
            line for line in lines
            if line.get('loading_pct', 0) >= critical_loading_threshold
        ]

        if critical_lines:
            issue = {
                'id': f"critical_loading_{timestamp}",
                'severity': 'critical',
                'reason': f"{len(critical_lines)} line(s) at or above {critical_loading_threshold}% loading",
                'affected_lines': [line['name'] for line in critical_lines],
                'metric_snapshots': {
                    line['name']: {
                        'loading_pct': line.get('loading_pct'),
                        'rating_mva': line.get('rating_mva'),
                        'flow_mva': line.get('flow_mva')
                    }
                    for line in critical_lines
                },
                'timestamp': timestamp,
                'confidence': 1.0,  # Direct measurement
                'recommended_actions': self._generate_actions_for_overload(critical_lines, critical=True)
            }
            detected_issues.append(issue)
            self._log_decision('critical_overload_detected', issue)

        high_stress_lines = [
            line for line in lines
            if high_loading_threshold <= line.get('loading_pct', 0) < critical_loading_threshold
        ]

        if high_stress_lines:
            issue = {
                'id': f"high_loading_{timestamp}",
                'severity': 'high',
                'reason': f"{len(high_stress_lines)} line(s) between {high_loading_threshold}-{critical_loading_threshold}% loading",
                'affected_lines': [line['name'] for line in high_stress_lines],
                'metric_snapshots': {
                    line['name']: {
                        'loading_pct': line.get('loading_pct'),
                        'margin_mva': line.get('margin_mva')
                    }
                    for line in high_stress_lines
                },
                'timestamp': timestamp,
                'confidence': 1.0,
                'recommended_actions': self._generate_actions_for_overload(high_stress_lines, critical=False)
            }
            detected_issues.append(issue)

        # Issue 2: Increasing Loading Trend
        if len(self.state.history) >= 3:
            trend_issue = self._detect_loading_trend(timestamp)
            if trend_issue:
                detected_issues.append(trend_issue)
                self._log_decision('loading_trend_detected', trend_issue)

        # Issue 3: Rating Decline (weather-driven)
        if len(self.state.history) >= 2:
            rating_issue = self._detect_rating_decline(current_data, timestamp)
            if rating_issue:
                detected_issues.append(rating_issue)
                self._log_decision('rating_decline_detected', rating_issue)

        # Issue 4: Sudden Anomalies
        anomaly_issue = self._detect_anomalies(current_data, timestamp)
        if anomaly_issue:
            detected_issues.append(anomaly_issue)
            self._log_decision('anomaly_detected', anomaly_issue)

        return detected_issues

    def _generate_actions_for_overload(
        self,
        lines: List[Dict[str, Any]],
        critical: bool
    ) -> List[Dict[str, Any]]:
        """Generate recommended actions for overloaded lines"""
        actions = []

        if critical:
            actions.append({
                'action': 'Immediate load shedding or line switching',
                'estimated_mva_change': -sum(line.get('flow_mva', 0) - line.get('rating_mva', 0) for line in lines) * 0.3,
                'estimated_pct_change': -20.0,
                'reasoning': 'Critical overload requires immediate action to prevent equipment damage',
                'confidence': 0.95
            })
            actions.append({
                'action': 'Emergency generation redispatch',
                'estimated_mva_change': -sum(abs(line.get('margin_mva', 0)) for line in lines) * 0.5,
                'estimated_pct_change': -15.0,
                'reasoning': 'Redistribute power flow to relieve stressed lines',
                'confidence': 0.85
            })
        else:
            actions.append({
                'action': 'Prepare contingency plans and increase monitoring',
                'estimated_mva_change': 0,
                'estimated_pct_change': 0,
                'reasoning': 'High loading indicates potential for overload with minor changes',
                'confidence': 0.90
            })
            actions.append({
                'action': 'Consider preemptive generation adjustment',
                'estimated_mva_change': -sum(line.get('flow_mva', 0) * 0.1 for line in lines),
                'estimated_pct_change': -10.0,
                'reasoning': 'Small adjustments now can prevent critical issues later',
                'confidence': 0.75
            })

        return actions

    def _detect_loading_trend(self, timestamp: str) -> Optional[Dict[str, Any]]:
        """Detect increasing loading trends from historical data"""
        if len(self.state.history) < 3:
            return None

        # Extract avg_loading from recent history
        recent_loadings = [
            h.get('summary', {}).get('avg_loading', 0)
            for h in self.state.history[-5:]
        ]

        if len(recent_loadings) < 3:
            return None

        # Simple linear regression to detect trend
        x = np.arange(len(recent_loadings))
        y = np.array(recent_loadings)

        # Calculate slope
        slope = np.polyfit(x, y, 1)[0]

        threshold = self.state.thresholds.get('trend_slope_threshold', 5.0)

        if slope > threshold:
            confidence = min(1.0, slope / (threshold * 2))
            return {
                'id': f"loading_trend_{timestamp}",
                'severity': 'medium',
                'reason': f"Average loading increasing at {slope:.2f}% per snapshot",
                'affected_lines': ['system-wide'],
                'metric_snapshots': {
                    'recent_loadings': recent_loadings,
                    'slope': slope,
                    'projected_next': recent_loadings[-1] + slope
                },
                'timestamp': timestamp,
                'confidence': confidence,
                'recommended_actions': [{
                    'action': 'Review load forecast and adjust generation schedule',
                    'estimated_mva_change': -slope * 10,
                    'estimated_pct_change': -slope,
                    'reasoning': 'Proactive adjustment can prevent future overloads',
                    'confidence': confidence
                }]
            }

        return None

    def _detect_rating_decline(
        self,
        current_data: Dict[str, Any],
        timestamp: str
    ) -> Optional[Dict[str, Any]]:
        """Detect significant rating declines due to weather changes"""
        if len(self.state.history) < 2:
            return None

        # Compare current to previous average loading
        prev_avg = self.state.history[-2].get('summary', {}).get('avg_loading', 0)
        curr_avg = current_data.get('summary', {}).get('avg_loading', 0)

        decline_threshold = self.state.thresholds.get('rating_decline_threshold', 10.0)

        if curr_avg - prev_avg > decline_threshold:
            confidence = min(1.0, (curr_avg - prev_avg) / (decline_threshold * 2))
            return {
                'id': f"rating_decline_{timestamp}",
                'severity': 'medium',
                'reason': f"Average loading increased by {curr_avg - prev_avg:.1f}% (likely weather-driven rating decline)",
                'affected_lines': ['system-wide'],
                'metric_snapshots': {
                    'previous_avg_loading': prev_avg,
                    'current_avg_loading': curr_avg,
                    'change': curr_avg - prev_avg
                },
                'timestamp': timestamp,
                'confidence': confidence,
                'recommended_actions': [{
                    'action': 'Monitor weather forecast and prepare for further rating reductions',
                    'estimated_mva_change': 0,
                    'estimated_pct_change': 0,
                    'reasoning': 'Weather conditions may continue to degrade line ratings',
                    'confidence': confidence
                }]
            }

        return None

    def _detect_anomalies(
        self,
        current_data: Dict[str, Any],
        timestamp: str
    ) -> Optional[Dict[str, Any]]:
        """Detect sudden anomalies compared to historical baseline"""
        if len(self.state.history) < 5:
            return None

        # Calculate historical baseline
        historical_loadings = [
            h.get('summary', {}).get('avg_loading', 0)
            for h in self.state.history[:-1]
        ]

        baseline_mean = np.mean(historical_loadings)
        baseline_std = np.std(historical_loadings)

        if baseline_std == 0:
            return None

        current_loading = current_data.get('summary', {}).get('avg_loading', 0)

        # Detect if current is >2 std deviations from baseline
        z_score = abs(current_loading - baseline_mean) / baseline_std

        if z_score > 2.0:
            confidence = min(1.0, z_score / 4.0)
            return {
                'id': f"anomaly_{timestamp}",
                'severity': 'high' if z_score > 3.0 else 'medium',
                'reason': f"Current loading ({current_loading:.1f}%) deviates {z_score:.1f} std deviations from baseline",
                'affected_lines': ['system-wide'],
                'metric_snapshots': {
                    'current_loading': current_loading,
                    'baseline_mean': baseline_mean,
                    'baseline_std': baseline_std,
                    'z_score': z_score
                },
                'timestamp': timestamp,
                'confidence': confidence,
                'recommended_actions': [{
                    'action': 'Investigate cause of sudden loading change',
                    'estimated_mva_change': 0,
                    'estimated_pct_change': 0,
                    'reasoning': 'Unexpected changes may indicate equipment issues or data anomalies',
                    'confidence': confidence
                }]
            }

        return None

    def predict_future_states(
        self,
        weather_forecast: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Predict future grid states using IEEE 738 calculations

        Args:
            weather_forecast: List of weather forecasts with keys:
                - timestamp: ISO timestamp
                - Ta: Temperature (°C)
                - WindVelocity: Wind speed (ft/sec)
                - WindAngleDeg: Wind angle (degrees)
                - (other weather params as needed by calculator)

        Returns:
            Dictionary with:
                - predictions: List of prediction dicts
                - model: "ieee738"
                - generated_at: ISO timestamp
        """
        predictions = []

        for forecast in weather_forecast:
            try:
                # Use calculator to get future ratings
                # Ensure all required weather params are present
                weather_params = {
                    'Ta': forecast.get('Ta', 25),
                    'WindVelocity': forecast.get('WindVelocity', 2.0),
                    'WindAngleDeg': forecast.get('WindAngleDeg', 90),
                    'SunTime': forecast.get('SunTime', 12),
                    'Date': forecast.get('Date', '12 Jun'),
                    'Emissivity': forecast.get('Emissivity', 0.8),
                    'Absorptivity': forecast.get('Absorptivity', 0.8),
                    'Direction': forecast.get('Direction', 'EastWest'),
                    'Atmosphere': forecast.get('Atmosphere', 'Clear'),
                    'Elevation': forecast.get('Elevation', 1000),
                    'Latitude': forecast.get('Latitude', 27)
                }

                # Call IEEE 738 calculator
                future_ratings = self.calculator.calculate_all_line_ratings(weather_params)

                # Extract predicted ratings and assess risk levels
                predicted_ratings = {}
                risk_levels = {}

                for line in future_ratings.get('lines', []):
                    line_name = line['name']
                    loading_pct = line.get('loading_pct', 0)

                    predicted_ratings[line_name] = line.get('rating_mva', 0)

                    # Assess risk level
                    if loading_pct >= self.state.thresholds['critical_loading']:
                        risk_levels[line_name] = 'high'
                    elif loading_pct >= self.state.thresholds['high_loading']:
                        risk_levels[line_name] = 'medium'
                    else:
                        risk_levels[line_name] = 'low'

                # Calculate confidence (decreases with forecast horizon)
                forecast_index = weather_forecast.index(forecast)
                confidence = max(0.5, 1.0 - forecast_index * 0.1)

                prediction = {
                    'timestamp': forecast.get('timestamp', datetime.utcnow().isoformat()),
                    'predicted_ratings': predicted_ratings,
                    'risk_levels': risk_levels,
                    'confidence': confidence,
                    'weather_conditions': weather_params
                }

                predictions.append(prediction)

            except Exception as e:
                self.logger.error(f"Failed to predict for forecast {forecast}: {e}")
                predictions.append({
                    'timestamp': forecast.get('timestamp', datetime.utcnow().isoformat()),
                    'error': str(e),
                    'confidence': 0.0
                })

        result = {
            'predictions': predictions,
            'model': 'ieee738',
            'generated_at': datetime.utcnow().isoformat()
        }

        self._log_decision('predictions_generated', {
            'forecast_count': len(weather_forecast),
            'success_count': len([p for p in predictions if 'error' not in p])
        })

        return result

    def generate_recommendations(
        self,
        issues: List[Dict[str, Any]],
        scope: str = 'grid',
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Generate prioritized recommendations from detected issues

        Args:
            issues: List of issues from monitor_grid_state()
            scope: Filter scope ('line', 'area', 'grid')
            limit: Maximum number of recommendations to return

        Returns:
            List of recommendations with:
                - id: Unique recommendation ID
                - priority: 1 (highest) to 5 (lowest)
                - action: Action description
                - estimated_impact: Dict with 'mva' and 'loading_pct' changes
                - confidence: 0.0-1.0
                - justification: Reasoning for recommendation
        """
        recommendations = []

        # Priority mapping: critical=1, high=2, medium=3, low=4
        severity_to_priority = {
            'critical': 1,
            'high': 2,
            'medium': 3,
            'low': 4
        }

        for issue in issues:
            # Extract recommended actions from issue
            for action_dict in issue.get('recommended_actions', []):
                rec_id = f"{issue['id']}_action_{len(recommendations)}"

                recommendation = {
                    'id': rec_id,
                    'priority': severity_to_priority.get(issue.get('severity', 'low'), 4),
                    'action': action_dict.get('action', 'Review grid conditions'),
                    'estimated_impact': {
                        'mva': action_dict.get('estimated_mva_change', 0),
                        'loading_pct': action_dict.get('estimated_pct_change', 0)
                    },
                    'confidence': action_dict.get('confidence', 0.5),
                    'justification': action_dict.get('reasoning', issue.get('reason', ''))
                }

                recommendations.append(recommendation)

        # Sort by priority (lower number = higher priority)
        recommendations.sort(key=lambda r: (r['priority'], -r['confidence']))

        # Apply limit
        recommendations = recommendations[:limit]

        self._log_decision('recommendations_generated', {
            'issue_count': len(issues),
            'recommendation_count': len(recommendations),
            'top_priority': recommendations[0]['priority'] if recommendations else None
        })

        return recommendations

    def learn_from_outcomes(
        self,
        action_id: str,
        operator_feedback: Dict[str, Any]
    ) -> None:
        """
        Learn from operator feedback on recommendations

        Args:
            action_id: ID of the action that was taken
            operator_feedback: Dict with:
                - result: 'accepted' or 'rejected'
                - success: bool (optional, for accepted actions)
                - metrics: Dict of outcome metrics (optional)
                - notes: String notes from operator (optional)

        Updates AgentState patterns and thresholds based on outcomes
        """
        feedback_entry = {
            'action_id': action_id,
            'timestamp': datetime.utcnow().isoformat(),
            'feedback': operator_feedback
        }

        self.state.action_history.append(feedback_entry)

        # Keep action history bounded
        if len(self.state.action_history) > 100:
            self.state.action_history = self.state.action_history[-100:]

        result = operator_feedback.get('result', 'unknown')

        # Adjust thresholds based on feedback
        if result == 'accepted':
            # If action was successful, maintain current thresholds
            if operator_feedback.get('success', False):
                self.logger.info(f"Action {action_id} was successful, thresholds maintained")
            else:
                # Action accepted but not successful - be more conservative
                self.state.thresholds['high_loading'] = max(
                    70.0,
                    self.state.thresholds['high_loading'] - 2.0
                )
                self.logger.info(f"Action {action_id} accepted but unsuccessful, lowering high_loading threshold to {self.state.thresholds['high_loading']}")

        elif result == 'rejected':
            # Operator rejected - be less aggressive
            self.state.thresholds['high_loading'] = min(
                95.0,
                self.state.thresholds['high_loading'] + 2.0
            )
            self.logger.info(f"Action {action_id} rejected, raising high_loading threshold to {self.state.thresholds['high_loading']}")

        self._log_decision('feedback_received', {
            'action_id': action_id,
            'result': result,
            'updated_thresholds': self.state.thresholds
        })

    def heartbeat_loop(self) -> Dict[str, Any]:
        """
        Perform a single heartbeat monitoring cycle

        Returns:
            Status dict with current state information
        """
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'state_version': self.state.version,
            'history_size': len(self.state.history),
            'action_history_size': len(self.state.action_history),
            'thresholds': self.state.thresholds
        }
