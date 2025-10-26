# AI Chatbot Quick Start (2 Minutes)

Get your intelligent Grid Monitor chatbot running in under 2 minutes!

## Step 1: Get API Key (30 seconds)
1. Visit: https://console.anthropic.com/
2. Sign up/login
3. Go to API Keys → Create Key
4. Copy the key (starts with `sk-ant-`)

## Step 2: Configure (30 seconds)
```bash
cd backend
# Edit .env file and add your key:
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

## Step 3: Install Dependencies (30 seconds)
```bash
# Make sure you're in backend/ with venv activated
pip install anthropic python-dotenv
```

## Step 4: Start Backend (15 seconds)
```bash
python app.py
```
✅ No warnings = Success!

## Step 5: Test It! (15 seconds)
1. Open http://localhost:5173
2. Click purple chat button (bottom-right)
3. Try: "What's the current grid status?"

## Example Questions

**Try these to see the AI in action:**

🔍 **Data Explanation:**
- "Explain what loading percentage means"
- "What is dynamic rating?"
- "Why is line L0 in critical state?"

🔮 **Impact Prediction:**
- "What if temperature increases to 35°C?"
- "How would doubling wind speed help?"
- "Predict impact of extreme heat"

📊 **Grid Analysis:**
- "Give me a grid status summary"
- "Which lines are most at risk?"
- "Are there any overloaded lines?"

## Suggested Questions Feature

When you first open the chat, you'll see 5 suggested questions. Click any to try them instantly!

## Troubleshooting

### "AI chatbot disabled" message?
→ Check your API key in `backend/.env`

### Backend won't start?
→ Run: `pip install -r requirements.txt`

### Chat button not appearing?
→ Check frontend is running on http://localhost:5173

## What Makes This Chatbot Smart?

✨ **Real-time Context**: Knows current grid state, weather, and line ratings
✨ **Domain Expert**: Trained on IEEE 738 power system standards
✨ **Predictive**: Can forecast impacts of variable changes
✨ **Natural Language**: Explains complex metrics conversationally

## Cost

- **Free Tier**: $5 credits = ~50,000+ queries
- **Typical Query**: $0.01-0.02 each
- **Monitor Usage**: https://console.anthropic.com/settings/usage

## Need More Help?

📖 **Full Documentation**: See `AI_CHATBOT_SETUP.md`
🔧 **Technical Details**: See `backend/README_CHATBOT.md`
🚀 **General Setup**: See `GETTING_STARTED.md`

---

**You're ready to chat!** Ask away and explore your intelligent grid assistant! 🤖⚡
