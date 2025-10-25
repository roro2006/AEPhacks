# AI Chatbot Service

## Quick Reference

### Files
- `chatbot_service.py` - Main AI service using Claude API
- `.env` - Configuration file (add your API key here)
- `.env.example` - Template for environment variables

### Setup
```bash
# 1. Install dependencies
pip install anthropic python-dotenv

# 2. Configure API key
# Edit .env and add: ANTHROPIC_API_KEY=your-key-here

# 3. Start server
python app.py
```

### Environment Variables

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-api03-...

# Optional
CLAUDE_MODEL=claude-3-5-sonnet-20241022  # Default model
MAX_TOKENS=1024                           # Max response length
TEMPERATURE=0.7                           # Response creativity (0.0-1.0)
```

### API Endpoints

#### POST /api/chatbot
Main chatbot endpoint with context-aware responses

**Request:**
```json
{
  "message": "What's the grid status?",
  "weather": {
    "ambient_temp": 25,
    "wind_speed": 2.0,
    "wind_angle": 90,
    "sun_time": 12,
    "date": "12 Jun"
  }
}
```

**Response:**
```json
{
  "response": "AI-generated response",
  "query_type": "general|data_explanation|impact_analysis",
  "ai_powered": true,
  "model": "claude-3-5-sonnet-20241022",
  "tokens": 450
}
```

#### POST /api/chatbot/analyze-impact
Specialized variable impact analysis

**Request:**
```json
{
  "variable": "temperature",
  "change": {"from": 25, "to": 35},
  "weather": { ... }
}
```

### How It Works

1. **Context Extraction**: Analyzes current grid state, weather, and line data
2. **System Prompt**: Builds comprehensive context for Claude with IEEE 738 knowledge
3. **AI Processing**: Claude generates intelligent, domain-specific responses
4. **Response**: Returns natural language explanation with technical accuracy

### Grid Context Provided to AI

The chatbot receives:
- **Weather**: Temperature (°C/°F), wind speed (ft/s, mph), wind angle, time of day
- **Grid Summary**: Total lines, stress levels, average/max loading
- **Top Stressed Lines**: 5 most loaded lines with detailed metrics
- **Temperature Sensitivity**: Count of lines close to limits
- **Operational Status**: Overall grid health assessment

### Cost Estimates

**Claude 3.5 Sonnet Pricing:**
- Input: $3 per million tokens
- Output: $15 per million tokens

**Typical Costs:**
- Simple question: ~500 tokens = ~$0.01
- Complex analysis: ~1500 tokens = ~$0.02-0.03
- $5 free credits ≈ 50,000-100,000 queries

### Customization

Edit `chatbot_service.py` to customize:

**System Prompt** (`_build_system_prompt`):
- Response style and tone
- Technical depth
- Domain expertise
- Safety guidelines

**Context Extraction** (`_extract_grid_context`):
- What data to include
- Which lines to highlight
- Summary calculations

**Impact Analysis** (`analyze_variable_impact`):
- Prediction methodology
- Recommendation depth
- Time horizon

### Error Handling

The service gracefully handles:
- Missing API key → Falls back to basic responses
- API errors → Returns error message
- Invalid context → Uses defaults
- Rate limits → Informs user to wait

### Security

✅ **Implemented:**
- Environment variables for API key
- .env in .gitignore
- Error message sanitization
- No key logging

⚠️ **Recommended for Production:**
- Rate limiting per user
- API key rotation
- Usage monitoring/alerts
- Request validation
- HTTPS only

### Monitoring

**Check API usage:**
1. Visit https://console.anthropic.com/settings/usage
2. View requests, tokens, and costs
3. Set up billing alerts

**Backend logs:**
```bash
# Watch for initialization
python app.py
# Should see: No warnings = chatbot enabled
# Warning message = check API key
```

### Development Tips

**Test without frontend:**
```bash
curl -X POST http://localhost:5000/api/chatbot \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Test message",
    "weather": {"ambient_temp": 25, "wind_speed": 2.0}
  }'
```

**Debug mode:**
Edit `chatbot_service.py` to add logging:
```python
print(f"Grid context: {grid_context}")
print(f"System prompt length: {len(system_prompt)}")
print(f"Tokens used: {message.usage}")
```

**Test different models:**
```bash
# In .env
CLAUDE_MODEL=claude-3-haiku-20240307  # Faster, cheaper
CLAUDE_MODEL=claude-3-opus-20240229   # Smarter, expensive
```

### Common Issues

**"AI chatbot disabled"**
→ Check `.env` has valid ANTHROPIC_API_KEY

**"ModuleNotFoundError: anthropic"**
→ Run `pip install anthropic python-dotenv`

**Slow responses**
→ Normal for AI (1-3 seconds). Reduce MAX_TOKENS if needed

**Generic responses**
→ Check grid context is being passed correctly

### Future Enhancements

Ideas for improvement:
- [ ] Conversation history/memory
- [ ] Caching for common questions
- [ ] Multi-language support
- [ ] Voice interface
- [ ] Proactive alerts
- [ ] Learning from user feedback
- [ ] Integration with SCADA systems

---

For complete setup guide, see: `../AI_CHATBOT_SETUP.md`
