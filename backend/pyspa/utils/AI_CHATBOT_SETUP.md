# AI Chatbot Setup Guide

This guide will help you set up the AI-powered chatbot using Claude API for the Grid Monitor application.

## Features

The AI chatbot provides two core capabilities:

### 1. Data Explanation
- Explains all grid metrics in natural language
- Clarifies technical concepts (loading percentage, dynamic ratings, stress levels)
- Interprets current grid conditions and line statuses
- Provides context based on IEEE 738 standards

### 2. Variable Impact Analysis
- Predicts what happens when weather parameters change
- Analyzes temperature, wind speed, and time-of-day impacts
- Identifies which lines are most affected by variable changes
- Provides operational recommendations

## Prerequisites

- Python 3.8+ with virtual environment
- Node.js 16+ and npm
- Anthropic API key (get one at https://console.anthropic.com/)

## Step 1: Get Your API Key

1. Visit https://console.anthropic.com/
2. Sign up or log in to your account
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key (it starts with `sk-ant-...`)

**IMPORTANT:** Keep this key secure and never commit it to version control!

## Step 2: Configure the Backend

### Install Required Packages

```bash
cd backend

# Activate your virtual environment
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate  # Windows

# Install new dependencies
pip install anthropic==0.39.0 python-dotenv==1.0.0

# Or install all requirements
pip install -r requirements.txt
```

### Set Up Environment Variables

1. Navigate to the `backend` folder
2. Open the `.env` file (it was created automatically)
3. Replace `your_api_key_here` with your actual API key:

```bash
# backend/.env
ANTHROPIC_API_KEY=sk-ant-api03-your-actual-key-here

# Optional: Model configuration
CLAUDE_MODEL=claude-3-5-sonnet-20241022

# Optional: API settings
MAX_TOKENS=1024
TEMPERATURE=0.7
```

**Security Note:** The `.env` file should already be in `.gitignore`. Never commit API keys!

## Step 3: Verify Installation

### Test the Backend

```bash
# Make sure you're in the backend directory with venv activated
python app.py
```

You should see:
```
 * Running on http://0.0.0.0:5000
```

**No errors** means the chatbot service initialized successfully!

If you see a warning like:
```
Warning: AI chatbot disabled - ANTHROPIC_API_KEY not set
```

Go back to Step 2 and verify your API key is set correctly.

### Test the API Endpoint

Open a new terminal and test:

```bash
curl -X POST http://localhost:5000/api/chatbot \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the current grid status?",
    "weather": {
      "ambient_temp": 25,
      "wind_speed": 2.0,
      "wind_angle": 90,
      "sun_time": 12,
      "date": "12 Jun"
    }
  }'
```

You should get an AI-generated response about the grid status!

## Step 4: Start the Frontend

```bash
cd ../frontend

# Install dependencies (if not already done)
npm install

# Start the dev server
npm run dev
```

Open http://localhost:5173 in your browser.

## Step 5: Use the Chatbot

1. Look for the **purple chat button** in the bottom-right corner
2. Click to open the chat window
3. Try the suggested questions or ask your own!

### Example Questions

**Data Explanation:**
- "What is the current grid status?"
- "Explain the loading percentage metric"
- "What does margin to overload mean?"
- "Why is line L0 in critical state?"
- "What is dynamic rating?"

**Variable Impact Analysis:**
- "What if temperature increases by 10°C?"
- "How would doubling the wind speed affect the grid?"
- "What happens if temperature reaches 40°C?"
- "Predict the impact of reducing wind to 0.5 ft/s"
- "Which lines are most sensitive to temperature changes?"

**Specific Line Queries:**
- "What is the status of line L0?"
- "Tell me about the most loaded line"
- "Are there any overloaded lines?"
- "Which lines should I monitor closely?"

## API Endpoints

### Standard Chatbot
```
POST /api/chatbot
```

**Request:**
```json
{
  "message": "Your question here",
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
  "query_type": "data_explanation|impact_analysis|general",
  "ai_powered": true,
  "model": "claude-3-5-sonnet-20241022",
  "tokens": 450,
  "summary": { ... },
  "timestamp": "2025-01-25T10:30:00"
}
```

### Variable Impact Analysis
```
POST /api/chatbot/analyze-impact
```

**Request:**
```json
{
  "variable": "temperature",
  "change": {"from": 25, "to": 35},
  "weather": { ... }
}
```

**Response:**
```json
{
  "analysis": "Detailed impact analysis...",
  "variable": "temperature",
  "change": {"from": 25, "to": 35},
  "timestamp": "2025-01-25T10:30:00"
}
```

## Cost Management

### Understanding Costs

The chatbot uses Claude 3.5 Sonnet which costs:
- **Input:** $3 per million tokens
- **Output:** $15 per million tokens

**Typical usage:**
- Simple query: ~500-800 tokens (~$0.01)
- Complex analysis: ~1000-1500 tokens (~$0.02)

### Cost Optimization Tips

1. **Adjust MAX_TOKENS** in `.env` to limit response length:
   ```bash
   MAX_TOKENS=512  # Shorter responses = lower cost
   ```

2. **Monitor usage** in Anthropic Console:
   - https://console.anthropic.com/settings/usage

3. **Set monthly limits** in your Anthropic account settings

4. **Rate limiting:** The backend automatically fails gracefully if API is unavailable

### Free Tier

Anthropic offers:
- **$5 free credits** for new accounts
- Approximately **50,000-100,000 queries** depending on complexity

## Troubleshooting

### "AI chatbot disabled" warning

**Cause:** API key not set or invalid

**Solution:**
1. Check `backend/.env` file exists
2. Verify API key starts with `sk-ant-`
3. No quotes around the key in .env file
4. Restart the Flask server

### "ModuleNotFoundError: No module named 'anthropic'"

**Cause:** Package not installed

**Solution:**
```bash
cd backend
source venv/bin/activate  # macOS/Linux
pip install anthropic python-dotenv
```

### API returns 401 Unauthorized

**Cause:** Invalid API key

**Solution:**
1. Verify key is correct at https://console.anthropic.com/
2. Make sure key hasn't expired
3. Check for any extra spaces in .env file

### Chatbot responds but says "not configured"

**Cause:** Frontend receiving fallback responses

**Solution:**
1. Check browser console for errors
2. Verify backend is running on port 5000
3. Check backend terminal for initialization errors

### Slow responses

**Cause:** AI processing time (1-3 seconds is normal)

**Solution:**
- This is expected behavior
- Consider caching common questions (future enhancement)
- Reduce MAX_TOKENS for faster responses

### Rate limit errors

**Cause:** Too many requests in short time

**Solution:**
- Anthropic has generous rate limits (50+ requests/min)
- If hit, wait 60 seconds
- Implement request queuing (future enhancement)

## Security Best Practices

1. **Never commit .env files** - Already in .gitignore
2. **Rotate API keys regularly** - Every 90 days recommended
3. **Use environment variables** - Never hardcode keys
4. **Monitor usage** - Set up billing alerts
5. **Restrict API key permissions** - Use least privilege principle

## Advanced Configuration

### Switching Models

Edit `backend/.env`:

```bash
# Use Claude 3 Opus for highest quality (more expensive)
CLAUDE_MODEL=claude-3-opus-20240229

# Use Claude 3 Sonnet for balance (default)
CLAUDE_MODEL=claude-3-5-sonnet-20241022

# Use Claude 3 Haiku for speed/cost (less capable)
CLAUDE_MODEL=claude-3-haiku-20240307
```

### Adjusting Response Style

Edit `backend/.env`:

```bash
# More creative/varied responses
TEMPERATURE=1.0

# More focused/consistent responses (default)
TEMPERATURE=0.7

# Most deterministic responses
TEMPERATURE=0.0
```

### Custom System Prompts

Edit `backend/chatbot_service.py` in the `_build_system_prompt` method to customize:
- Response style and tone
- Technical depth
- Domain expertise
- Safety guidelines

## Architecture

```
Frontend (React/TypeScript)
    ↓
Chatbot.tsx Component
    ↓
API Call: POST /api/chatbot
    ↓
Flask Backend (app.py)
    ↓
GridChatbotService (chatbot_service.py)
    ↓
Claude API (Anthropic)
    ↓
AI Response with Grid Context
```

## What Makes This Chatbot Intelligent?

1. **Contextual Awareness:** Receives real-time grid data, weather conditions, and line ratings
2. **Domain Expertise:** Trained with IEEE 738 standards and power system knowledge
3. **Predictive Analysis:** Can forecast impacts of variable changes
4. **Multi-turn Conversations:** Maintains context across messages
5. **Technical Translation:** Explains complex metrics in accessible language

## Support & Resources

- **Anthropic Documentation:** https://docs.anthropic.com/
- **Claude API Reference:** https://docs.anthropic.com/claude/reference
- **Rate Limits:** https://docs.anthropic.com/claude/reference/rate-limits
- **Pricing:** https://www.anthropic.com/pricing

## Next Steps

1. ✅ Configure API key
2. ✅ Test the chatbot
3. 🚀 Try different questions
4. 📊 Monitor usage and costs
5. 🎨 Customize prompts for your use case
6. 🔒 Set up production security measures

---

**Happy chatting with your AI Grid Assistant!** 🤖⚡
