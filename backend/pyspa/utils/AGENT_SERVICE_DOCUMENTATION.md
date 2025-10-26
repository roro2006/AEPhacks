# Autonomous Grid Monitor Agent Service - Documentation

## Overview

The Autonomous Grid Monitor Agent is an AI-powered system that proactively monitors and manages the power grid. It provides real-time analysis, predictive capabilities, pattern recognition, and automated recommendations for grid operators.

## Architecture

### Core Components

#### 1. **AgentState Class**
Maintains the agent's complete state including:
- **Historical Grid Conditions**: Circular buffer of up to 1000 grid snapshots
- **Pattern Recognition Data**: Learned patterns from successful/failed actions
- **Action History**: Last 500 actions taken and their outcomes
- **Monitoring Thresholds**: Dynamic thresholds that adjust based on learning
- **Active Alerts/Recommendations/Predictions**: Current actionable items

#### 2. **GridMonitorAgent Class**
The main autonomous agent with core capabilities:
- `monitor_grid_state()`: Real-time grid analysis and issue detection
- `predict_future_states()`: IEEE 738-based predictive analysis
- `generate_recommendations()`: AI-powered prioritized recommendations
- `learn_from_outcomes()`: Pattern recognition and threshold adjustment

### Data Models (Pydantic)

All data structures use Pydantic for validation and type safety:

```python
GridMetrics       # Snapshot of grid state at a point in time
PatternData       # Recognized behavioral patterns
ActionRecord      # Record of actions and outcomes
Alert             # Proactive alerts with severity levels
Recommendation    # Prioritized recommendations with justification
Prediction        # Future state predictions with confidence
```

## API Endpoints

### 1. GET `/api/agent/status`

Get current agent state and metrics.

**Response:**
```json
{
  "agent_status": "active",
  "uptime_seconds": 3600.5,
  "state": {
    "grid_history_count": 245,
    "patterns_count": 12,
    "action_history_count": 48,
    "active_alerts_count": 2,
    "active_recommendations_count": 5,
    "prediction_accuracy": 0.87
  },
  "active_alerts": [...],
  "active_recommendations": [...],
  "learning_metrics": {
    "patterns_learned": 12,
    "actions_recorded": 48,
    "prediction_accuracy": 0.87
  }
}
```

### 2. POST `/api/agent/monitor`

Analyze current grid conditions and detect issues.

**Request:**
```json
{
  "weather": {
    "ambient_temp": 35,
    "wind_speed": 1.5,
    "wind_angle": 90,
    "sun_time": 14,
    "date": "12 Jun"
  }
}
```

**Response:**
```json
{
  "timestamp": "2025-01-15T14:30:00",
  "issues_detected": 3,
  "issues": [
    {
      "severity": "critical",
      "type": "high_stress",
      "description": "2 line(s) under high stress (90-100% loading)",
      "affected_lines": ["L48", "L49"],
      "details": [...]
    }
  ],
  "recommendations": [
    {
      "priority": 1,
      "action": "Prepare contingency plans and monitor closely",
      "justification": "High stress lines are at risk of overload"
    }
  ],
  "grid_status": "HIGH_STRESS"
}
```

### 3. POST `/api/agent/predictions`

Predict future grid states based on weather forecast.

**Request:**
```json
{
  "weather_forecast": [
    {
      "ambient_temp": 38,
      "wind_speed": 1.2,
      "wind_angle": 90,
      "sun_time": 15,
      "date": "12 Jun"
    },
    {
      "ambient_temp": 40,
      "wind_speed": 1.0,
      "wind_angle": 90,
      "sun_time": 16,
      "date": "12 Jun"
    }
  ]
}
```

**Response:**
```json
{
  "timestamp": "2025-01-15T14:30:00",
  "predictions": [
    {
      "prediction_id": "pred_20250115143000_1",
      "forecast_time": "2025-01-15T15:30:00",
      "predicted_metrics": {
        "avg_loading": 87.5,
        "max_loading": 98.2,
        "critical_count": 0,
        "high_stress_count": 3
      },
      "confidence": 0.85,
      "risk_factors": [
        "High temperature conditions",
        "Low wind speed reducing cooling"
      ],
      "preventive_actions": [
        "Increase monitoring frequency to 15-minute intervals",
        "Prepare to reduce loading on: L48, L49"
      ]
    }
  ],
  "alerts": [
    {
      "alert_id": "alert_20250115143000_1",
      "severity": "warning",
      "title": "Predicted high stress in 1 hour(s)",
      "description": "3 lines predicted to reach high stress",
      "affected_lines": ["L48", "L49", "L52"],
      "recommended_actions": [...],
      "confidence": 0.85
    }
  ],
  "forecast_horizon_hours": 2
}
```

### 4. POST `/api/agent/recommendations`

Generate prioritized recommendations based on current state.

**Request:**
```json
{
  "weather": {
    "ambient_temp": 35,
    "wind_speed": 1.5
  }
}
```

**Response:**
```json
{
  "timestamp": "2025-01-15T14:30:00",
  "recommendations_count": 4,
  "recommendations": [
    {
      "rec_id": "rec_20250115143000_1",
      "priority": 1,
      "title": "Immediate load reduction on L48",
      "description": "Line L48 is at 98% loading and approaching limits",
      "justification": "Critical proximity to thermal limits with adverse weather",
      "expected_impact": {
        "loading_reduction": 15,
        "risk_mitigation": "high"
      },
      "confidence": 0.92,
      "actionable_steps": [
        "Contact generation dispatch for load redistribution",
        "Prepare N-1 contingency plans",
        "Monitor line temperature sensors"
      ]
    }
  ]
}
```

### 5. POST `/api/agent/learn`

Record action outcome for agent learning.

**Request:**
```json
{
  "action": {
    "action_id": "action_123",
    "action_type": "alert",
    "description": "Reduced load on line L48 by 10 MW",
    "grid_state_before": {
      "avg_loading": 95.0,
      "weather_temp": 38
    }
  },
  "result": {
    "outcome": "successful",
    "impact_score": 0.85,
    "grid_state_after": {
      "avg_loading": 78.0
    }
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Action outcome recorded successfully",
  "patterns_learned": 13,
  "action_id": "action_123"
}
```

### 6. POST `/api/chatbot` (Enhanced)

Chatbot now includes autonomous insights automatically.

**Response includes:**
```json
{
  "response": "Line L48 is currently at 95% loading...",
  "autonomous_insights": {
    "issues_detected": 2,
    "grid_status": "HIGH_STRESS",
    "critical_issues": [...],
    "top_recommendations": [...]
  }
}
```

## Pattern Recognition System

The agent learns from historical data and action outcomes:

### Pattern Types

1. **Weather Impact Patterns**
   - Temperature sensitivity curves
   - Wind speed correlations
   - Solar radiation effects

2. **Loading Trends**
   - Linear regression on historical loading
   - Detection of concerning slopes (>5% per hour)
   - Time-of-day patterns

3. **Issue Sequences**
   - Common cascading failure patterns
   - Precursor conditions to overloads
   - Seasonal variations

4. **Resolution Strategies**
   - Successful mitigation actions
   - Effective load redistribution patterns
   - Optimal response timing

### Pattern Confidence

- Initial patterns: 0.6 confidence
- Confidence increases by 0.05 per occurrence (max 0.95)
- Patterns require >0.7 confidence to trigger actions
- Failed actions reduce threshold sensitivity

## Proactive Monitoring Features

### Issue Detection

1. **Critical Overloads** (≥100% loading)
   - Severity: Emergency
   - Immediate action required

2. **High Stress Lines** (90-100% loading)
   - Severity: Critical
   - Contingency planning needed

3. **Trending Issues**
   - Detects increasing loading rates
   - Projects future state
   - Early warning system

4. **Adverse Weather**
   - Hot (>35°C) + Calm (<1.5 ft/s wind)
   - Triggers enhanced monitoring

5. **Pattern Matches**
   - Conditions similar to known problematic patterns
   - Confidence-weighted alerts

### Alert Severity Levels

- **Emergency**: Critical overloads, immediate action
- **Critical**: High stress, prepare contingency
- **Warning**: Adverse conditions, monitor closely
- **Info**: Pattern matches, informational

## IEEE 738 Integration

All predictions use IEEE 738 thermal rating calculations:

```python
# Heat balance equation
I_max = sqrt((qc + qr - qs) / R(Tc))

Where:
- qc: Convective cooling (wind-dependent)
- qr: Radiative cooling (temperature-dependent)
- qs: Solar heating (time/date-dependent)
- R(Tc): Conductor resistance at temperature
```

### Prediction Confidence

- 1-hour ahead: 0.85 confidence
- 2-hour ahead: 0.80 confidence
- 3-hour ahead: 0.75 confidence
- Decreases by 0.05 per hour

## Learning Mechanism

### Successful Actions
```python
if outcome == 'successful' and impact_score > 0.5:
    # Create/update pattern
    pattern.confidence += 0.05
    pattern.occurrence_count += 1
    state.successful_predictions += 1
```

### Failed Actions
```python
if outcome == 'failed':
    # Adjust thresholds to be more conservative
    thresholds['loading']['caution'] -= 1.0
```

### Pattern Similarity
- Compares weather conditions (±5°C)
- Compares loading levels (±10%)
- Matches action types
- Updates existing patterns when similar

## Thresholds

### Default Thresholds
```python
{
  'loading': {
    'normal': 60.0,      # <60%
    'caution': 90.0,     # 60-90%
    'high': 100.0,       # 90-100%
    'critical': 100.0    # ≥100%
  },
  'trend': {
    'loading_increase_rate': 5.0,  # % per snapshot
    'temperature_sensitivity': 0.5  # % loading per °C
  },
  'pattern_confidence': 0.7,
  'prediction_horizon': 2.0  # hours
}
```

### Adaptive Thresholds
Thresholds adjust based on learning:
- Failed actions → Lower thresholds (more conservative)
- Successful patterns → Confidence increases
- System learns optimal operating points

## Error Handling

All endpoints include:
- Try-catch blocks with detailed error messages
- Graceful fallbacks (AI → rule-based)
- NaN-safe JSON serialization
- Comprehensive logging
- HTTP 503 when agent disabled
- HTTP 500 for unexpected errors

## Testing

Run comprehensive unit tests:
```bash
cd backend
python test_agent_service.py
```

### Test Coverage
- AgentState initialization and serialization
- GridMetrics data validation
- Issue detection (critical, high stress, weather)
- Prediction generation with IEEE 738
- Pattern recognition and matching
- Learning from outcomes (success/failure)
- Trend detection
- Risk factor identification
- Recommendation generation
- All Pydantic model validation

## Performance Considerations

### Memory Management
- Circular buffers limit history (1000 snapshots)
- Action history limited to 500 records
- Patterns pruned if confidence < 0.3

### Computation
- IEEE 738 calculations cached when possible
- Pattern matching uses efficient dict lookups
- Trend detection uses NumPy for speed

### Scalability
- Agent is stateful (single instance recommended)
- Can be extended to distributed architecture
- Historical data can be persisted to database

## Usage Examples

### Basic Monitoring
```python
# Monitor current grid state
response = requests.post('http://localhost:5000/api/agent/monitor', json={
    'weather': {
        'ambient_temp': 35,
        'wind_speed': 1.5
    }
})

result = response.json()
if result['grid_status'] == 'CRITICAL':
    print(f"ALERT: {result['issues_detected']} issues detected!")
    for issue in result['issues']:
        print(f"  - {issue['description']}")
```

### Predictive Analysis
```python
# Get 2-hour forecast
forecast = [
    {'ambient_temp': 38, 'wind_speed': 1.2, 'sun_time': 15},
    {'ambient_temp': 40, 'wind_speed': 1.0, 'sun_time': 16}
]

response = requests.post('http://localhost:5000/api/agent/predictions', json={
    'weather_forecast': forecast
})

predictions = response.json()
for alert in predictions['alerts']:
    if alert['severity'] == 'critical':
        print(f"Future risk: {alert['description']}")
        print(f"Actions: {alert['recommended_actions']}")
```

### Learning from Operator Actions
```python
# Record that an action was successful
requests.post('http://localhost:5000/api/agent/learn', json={
    'action': {
        'action_type': 'load_reduction',
        'description': 'Reduced load on L48',
        'grid_state_before': {'avg_loading': 95.0}
    },
    'result': {
        'outcome': 'successful',
        'impact_score': 0.9,
        'grid_state_after': {'avg_loading': 75.0}
    }
})
```

## Future Enhancements

Potential improvements:
1. Database persistence for long-term pattern storage
2. Multi-agent coordination for distributed grids
3. Reinforcement learning for optimal action selection
4. Integration with SCADA systems for real-time data
5. Advanced time-series forecasting (LSTM/Transformers)
6. Automated action execution (with human approval)
7. Natural language explanations of all decisions
8. Integration with weather APIs for automatic forecasting

## Security Considerations

- API key required (ANTHROPIC_API_KEY)
- All endpoints use POST to prevent caching
- Input validation via Pydantic models
- No user data stored permanently
- Consider adding authentication for production use

## Troubleshooting

### Agent Not Initializing
```
Error: "Grid Monitor Agent disabled - ANTHROPIC_API_KEY not set"
Solution: Set ANTHROPIC_API_KEY in backend/.env file
```

### Low Prediction Accuracy
```
Issue: prediction_accuracy < 0.5
Solution:
- Verify IEEE 738 calculations are accurate
- Check weather forecast quality
- Review pattern confidence thresholds
- Examine failed predictions in action_history
```

### Pattern Not Triggering
```
Issue: Known pattern not generating alerts
Solution:
- Check pattern.confidence >= 0.7
- Verify trigger_conditions match current state
- Review _calculate_pattern_match() logic
```

## Contributing

When extending the agent:
1. Add new pattern types in `PatternData`
2. Implement detection in `monitor_grid_state()`
3. Add learning logic in `learn_from_outcomes()`
4. Create unit tests in `test_agent_service.py`
5. Update this documentation

## License

Part of the AEP Grid Monitor System - MIT License
