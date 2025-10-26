# Autonomous Grid Monitor Agent - Quick Start Guide

## 🚀 5-Minute Setup

### 1. Install Dependencies
```bash
pip install anthropic pydantic numpy pandas flask flask-cors
```

### 2. Set API Key
```bash
# Create/edit backend/.env
echo "ANTHROPIC_API_KEY=your_key_here" >> backend/.env
```

### 3. Start Server
```bash
cd backend
python app.py
```

### 4. Verify Agent is Running
```bash
curl http://localhost:5000/api/agent/status
```

## 📡 Quick API Reference

### Get Agent Status
```bash
curl http://localhost:5000/api/agent/status
```

### Monitor Grid (Current State)
```bash
curl -X POST http://localhost:5000/api/agent/monitor \
  -H "Content-Type: application/json" \
  -d '{
    "weather": {
      "ambient_temp": 35,
      "wind_speed": 1.5,
      "wind_angle": 90,
      "sun_time": 14,
      "date": "12 Jun"
    }
  }'
```

### Get Predictions (Future States)
```bash
curl -X POST http://localhost:5000/api/agent/predictions \
  -H "Content-Type: application/json" \
  -d '{
    "weather_forecast": [
      {"ambient_temp": 38, "wind_speed": 1.2, "sun_time": 15},
      {"ambient_temp": 40, "wind_speed": 1.0, "sun_time": 16}
    ]
  }'
```

### Get Recommendations
```bash
curl -X POST http://localhost:5000/api/agent/recommendations \
  -H "Content-Type: application/json" \
  -d '{
    "weather": {
      "ambient_temp": 35,
      "wind_speed": 1.5
    }
  }'
```

### Record Action Outcome (Learning)
```bash
curl -X POST http://localhost:5000/api/agent/learn \
  -H "Content-Type: application/json" \
  -d '{
    "action": {
      "action_type": "load_reduction",
      "description": "Reduced load on L48",
      "grid_state_before": {"avg_loading": 95.0}
    },
    "result": {
      "outcome": "successful",
      "impact_score": 0.9,
      "grid_state_after": {"avg_loading": 75.0}
    }
  }'
```

## 🧪 Testing

### Run Unit Tests
```bash
cd backend
python test_agent_service.py -v
```

### Run Integration Tests
```bash
python test_agent_integration.py
```

### Run Interactive Demo
```bash
python ../AGENT_DEMO_SCRIPT.py
```

## 🔍 Python Usage Examples

### Monitor Grid
```python
import requests

response = requests.post('http://localhost:5000/api/agent/monitor', json={
    'weather': {'ambient_temp': 35, 'wind_speed': 1.5}
})

data = response.json()
print(f"Status: {data['grid_status']}")
print(f"Issues: {data['issues_detected']}")

for issue in data['issues']:
    print(f"  {issue['severity']}: {issue['description']}")
```

### Get Predictions
```python
forecast = [
    {'ambient_temp': 38, 'wind_speed': 1.2, 'sun_time': 15},
    {'ambient_temp': 40, 'wind_speed': 1.0, 'sun_time': 16}
]

response = requests.post('http://localhost:5000/api/agent/predictions',
    json={'weather_forecast': forecast})

predictions = response.json()
for pred in predictions['predictions']:
    print(f"Hour {pred['forecast_time']}: {pred['predicted_metrics']}")
    print(f"  Confidence: {pred['confidence']}")
    print(f"  Risks: {pred['risk_factors']}")
```

### Learn from Actions
```python
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

## 📊 Key Endpoints Summary

| Endpoint | Method | Purpose | Response Time |
|----------|--------|---------|---------------|
| `/api/agent/status` | GET | Agent state | <50ms |
| `/api/agent/monitor` | POST | Current analysis | 100-200ms |
| `/api/agent/predictions` | POST | Future forecasts | 0.5-2s |
| `/api/agent/recommendations` | POST | AI suggestions | 2-5s |
| `/api/agent/learn` | POST | Record outcomes | <50ms |

## 🎯 Common Use Cases

### Use Case 1: Real-Time Monitoring Dashboard
```python
# Poll every 5 minutes
weather = get_current_weather()
status = requests.post('/api/agent/monitor', json={'weather': weather}).json()

if status['grid_status'] in ['CRITICAL', 'EMERGENCY']:
    send_alert(status['issues'])
```

### Use Case 2: Predictive Alerts
```python
# Get hourly forecast
forecast = get_weather_forecast(hours=3)
predictions = requests.post('/api/agent/predictions',
    json={'weather_forecast': forecast}).json()

for alert in predictions['alerts']:
    if alert['severity'] == 'critical':
        notify_operators(alert)
```

### Use Case 3: Decision Support
```python
# Get recommendations for current situation
recs = requests.post('/api/agent/recommendations',
    json={'weather': current_weather}).json()

for rec in recs['recommendations']:
    if rec['priority'] <= 2:  # High priority only
        display_recommendation(rec)
```

### Use Case 4: Continuous Learning
```python
# After operator takes action
action_result = monitor_action_outcome(action_id)

requests.post('/api/agent/learn', json={
    'action': action_details,
    'result': action_result
})
```

## 🛠️ Troubleshooting

### Agent Not Initializing
**Error**: `Grid Monitor Agent disabled`
**Solution**: Set `ANTHROPIC_API_KEY` in `backend/.env`

### Low Prediction Accuracy
**Check**: `/api/agent/status` → `prediction_accuracy`
**Fix**: Review failed predictions, adjust thresholds, verify weather data quality

### No Patterns Learning
**Check**: `/api/agent/status` → `patterns_count`
**Fix**: Ensure you're calling `/api/agent/learn` with action outcomes

### Slow Response Times
**Check**: AI-powered endpoints (recommendations) take 2-5s
**Fix**: Use caching, call predictively, show loading indicator

## 📚 Documentation Files

- **Full API Reference**: `AGENT_SERVICE_DOCUMENTATION.md`
- **Implementation Details**: `AGENT_IMPLEMENTATION_SUMMARY.md`
- **This Guide**: `QUICK_START_AGENT.md`
- **Demo Script**: `AGENT_DEMO_SCRIPT.py`

## 🎓 Learning Path

1. **Start Here**: Run `AGENT_DEMO_SCRIPT.py` for interactive tour
2. **Understand Architecture**: Read `AGENT_IMPLEMENTATION_SUMMARY.md`
3. **API Details**: Review `AGENT_SERVICE_DOCUMENTATION.md`
4. **Code Deep Dive**: Study `backend/agent_service.py`
5. **Testing**: Run and review `test_agent_service.py`

## 💡 Tips & Best Practices

### Performance
- Cache agent status for dashboards (TTL: 30s)
- Call predictions proactively, not reactively
- Batch learning calls if possible

### Accuracy
- Record all operator actions for learning
- Verify weather forecast quality
- Monitor prediction accuracy over time

### Reliability
- Handle 503 errors (agent disabled)
- Implement retry logic for transient failures
- Gracefully degrade if AI unavailable (rule-based fallback)

### Security
- Never expose API key in frontend
- Validate all weather inputs
- Rate-limit learning endpoint to prevent spam

## 🔗 Integration Examples

### React Frontend
```typescript
const monitorGrid = async (weather: WeatherParams) => {
  const response = await fetch('/api/agent/monitor', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ weather })
  });
  const data = await response.json();

  if (data.grid_status === 'CRITICAL') {
    showAlert(data.issues);
  }

  return data;
};
```

### Dashboard Widget
```typescript
const AgentInsightsWidget = () => {
  const [status, setStatus] = useState(null);

  useEffect(() => {
    const fetchStatus = async () => {
      const data = await fetch('/api/agent/status').then(r => r.json());
      setStatus(data);
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 30000); // 30s
    return () => clearInterval(interval);
  }, []);

  return (
    <div>
      <h3>Agent Status: {status?.agent_status}</h3>
      <p>Patterns Learned: {status?.learning_metrics.patterns_learned}</p>
      <p>Accuracy: {(status?.learning_metrics.prediction_accuracy * 100).toFixed(1)}%</p>
    </div>
  );
};
```

## ✅ Verification Checklist

- [ ] Agent initializes without errors
- [ ] `/api/agent/status` returns 200
- [ ] Unit tests pass (22/22)
- [ ] Integration tests pass (6/6)
- [ ] Monitoring detects issues correctly
- [ ] Predictions use IEEE 738 calculations
- [ ] Recommendations are prioritized
- [ ] Learning updates patterns
- [ ] Chatbot includes autonomous insights

## 🚦 Health Check

```bash
# Quick health check script
#!/bin/bash

echo "Checking agent health..."

# 1. Server running?
curl -s http://localhost:5000/api/health > /dev/null
echo "✓ Server is up"

# 2. Agent active?
STATUS=$(curl -s http://localhost:5000/api/agent/status | jq -r '.agent_status')
if [ "$STATUS" = "active" ]; then
  echo "✓ Agent is active"
else
  echo "✗ Agent not active"
  exit 1
fi

# 3. Learning working?
PATTERNS=$(curl -s http://localhost:5000/api/agent/status | jq -r '.learning_metrics.patterns_learned')
echo "✓ Agent has learned $PATTERNS patterns"

echo "✅ All health checks passed!"
```

## 📞 Support

- **Issues**: Check `AGENT_SERVICE_DOCUMENTATION.md` troubleshooting section
- **Testing**: Run unit tests to isolate problems
- **Logs**: Check Flask console output for errors
- **API Errors**: Use `/api/health` to verify server status

---

**Quick Start Complete! 🎉**

You're now ready to use the Autonomous Grid Monitor Agent. Start with the demo script, then integrate into your application!
