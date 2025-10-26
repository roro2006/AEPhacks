# Getting Started with Grid Monitor

## Quick Start (5 Minutes)

### Step 1: Start the Backend

#### For macOS/Linux:
```bash
# Open a terminal
cd /Users/anirudhsrc/Desktop/Hackathon_2025/AEPhacks/backend

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the Flask server
python app.py
```

#### For Windows:
```bash
# Open a terminal/command prompt
cd C:\Users\rores\OneDrive\Desktop\Hack25\AEP\grid-monitor\backend

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the Flask server
python app.py
```

✅ Backend should be running at `http://localhost:5000`

### Step 2: Start the Frontend

Open a **NEW** terminal/command prompt:

#### For macOS/Linux:
```bash
# Navigate to frontend
cd /Users/anirudhsrc/Desktop/Hackathon_2025/AEPhacks/frontend

# Install dependencies (first time only)
npm install

# Start the development server
npm run dev
```

#### For Windows:
```bash
# Navigate to frontend
cd C:\Users\rores\OneDrive\Desktop\Hack25\AEP\grid-monitor\frontend

# Install dependencies (first time only)
npm install

# Start the development server
npm run dev
```

✅ Frontend should be running at `http://localhost:5173`

### Step 3: Open in Browser

Navigate to `http://localhost:5173` in your web browser.

## What You'll See

### Live Grid Map Tab
- **Interactive map** of Hawaii40 transmission grid
- **Color-coded lines**:
  - 🟢 Green = Normal (<60% loading)
  - 🟡 Yellow = Caution (60-90% loading)
  - 🟠 Orange = High (90-100% loading)
  - 🔴 Red = Critical (>100% loading - OVERLOADED)

- **Right Sidebar**:
  - Weather controls to adjust temperature, wind speed, time of day
  - Quick scenario buttons
  - System alerts and top stressed lines

### Threshold Analysis Tab
- Find the exact temperature where lines start to overload
- Visual charts showing stress progression
- Operational recommendations

## Try These Scenarios

### Scenario 1: Normal Conditions (Default)
- Temperature: 25°C (77°F)
- Wind Speed: 2.0 ft/s
- Result: All lines should be green or yellow, no overloads

### Scenario 2: Hot & Calm
1. Click "Hot & Calm" button in Weather Controls
2. Temperature: 35°C (95°F)
3. Wind Speed: 1.0 ft/s
4. Result: Some lines turn orange, approaching limits

### Scenario 3: Extreme Heat
1. Click "Extreme Heat" button
2. Temperature: 40°C (104°F)
3. Wind Speed: 0.5 ft/s
4. Result: Some lines turn RED - overloaded!

### Scenario 4: Find Critical Threshold
1. Click "Threshold Analysis" tab
2. Set temperature range: 20°C to 50°C
3. Set wind speed: 2.0 ft/s
4. Click "Run Analysis"
5. See exactly at what temperature lines start failing

## Interactive Features

### On the Map
- **Hover** over lines to see quick info tooltip
- **Click** on lines to open detailed information panel
- **Pan/Zoom** to explore different grid areas

### In the Details Panel (when you click a line)
You'll see:
- Line name and voltage level
- Conductor type and maximum operating temperature
- **Current loading percentage** (key metric!)
- Current flow in MVA
- Dynamic rating vs static rating
- Margin to overload (how close to failure)

## Understanding the Metrics

### Loading Percentage
- **Formula**: (Current Flow / Dynamic Rating) × 100
- **<60%**: Healthy operation
- **60-90%**: Watch this line
- **90-100%**: High stress, prepare action plans
- **>100%**: OVERLOADED! Immediate intervention needed

### Margin to Overload
- **Positive**: Line has capacity remaining
- **Negative**: Line is overloaded by this amount

### Dynamic vs Static Rating
- **Static Rating**: Fixed rating (from s_nom in lines.csv)
- **Dynamic Rating**: Calculated using IEEE 738 based on current weather
- Dynamic ratings decrease with higher temperature and lower wind

## API Testing (Optional)

You can also test the API directly:

```bash
# Health check
curl http://localhost:5000/api/health

# Get grid topology
curl http://localhost:5000/api/grid/topology

# Calculate ratings
curl -X POST http://localhost:5000/api/lines/ratings \
  -H "Content-Type: application/json" \
  -d "{\"ambient_temp\": 30, \"wind_speed\": 1.5, \"wind_angle\": 90, \"sun_time\": 14, \"date\": \"12 Jun\"}"
```

## Using the AI Chatbot 🤖

The Grid Monitor now includes an **AI-powered chatbot** using Claude API! Look for the purple chat button in the bottom-right corner.

### ⚠️ First Time Setup Required
Before using the chatbot, you need to configure your Claude API key. See **[AI_CHATBOT_SETUP.md](AI_CHATBOT_SETUP.md)** for complete setup instructions.

**Quick setup:**
1. Get API key from https://console.anthropic.com/
2. Add to `backend/.env`: `ANTHROPIC_API_KEY=your-key-here`
3. Restart backend server
4. Start chatting!

### What makes this chatbot special:
- **Data Explanation**: Understands and explains all grid metrics in natural language
- **Impact Analysis**: Predicts what happens when you change weather variables
- **Real-time Context**: Always aware of current grid state and conditions
- **Domain Expert**: Trained on IEEE 738 standards and power system knowledge

### Example questions:
- **Data Explanation**: "Explain what loading percentage means" or "Why is line L0 critical?"
- **Impact Analysis**: "What if temperature increases by 10°C?" or "How would higher wind speed help?"
- **Grid Status**: "What's the current grid status?" or "Are there any overloaded lines?"
- **Technical Help**: "What is dynamic rating?" or "Explain margin to overload"

The chatbot uses real-time grid data, current weather conditions, and advanced AI to give you intelligent, context-aware responses!

## Troubleshooting

### Backend won't start
- **Error: `ModuleNotFoundError`**: Run `pip install -r requirements.txt`
- **Error: Port 5000 in use**:
  - macOS/Linux: Check with `lsof -i :5000` and kill process if needed
  - Windows: Change port in `backend/app.py` line: `app.run(port=5001)`
- **Error: Cannot find ieee738**: Make sure the `osu_hackathon` folder is in the correct location
- **macOS: Permission denied**: Try `python3` instead of `python`

### Frontend won't start
- **Error: `command not found: npm`**: Install Node.js from https://nodejs.org
- **Error: Port 5173 in use**: Vite will auto-select another port
- **Blank page**: Check browser console (F12) for errors, ensure backend is running
- **macOS: EACCES error**: Try `sudo npm install -g npm@latest` or use nvm (Node Version Manager)

### Map not loading
- **Check backend**: Make sure `http://localhost:5000/api/health` returns `{"status": "healthy"}`
- **CORS errors**: Make sure flask-cors is installed
- **GeoJSON errors**: Verify the `osu_hackathon` folder exists and contains the data files

### Chatbot not responding
- **Backend not running**: Ensure Flask server is running on port 5000
- **CORS errors**: Make sure flask-cors is installed (`pip install flask-cors`)
- **Check browser console**: Press F12 and look for errors in the Console tab

### No data showing
- **Error in console about data files**: Check paths in `data_loader.py`
- **macOS**: Paths should use forward slashes: `/Users/username/...`
- **Windows**: Paths should use backslashes: `C:\Users\username\...`

## Next Steps

1. **Explore the grid**: Try different weather scenarios
2. **Find thresholds**: Use threshold analysis to find critical temperatures
3. **Understand patterns**: Which lines are most sensitive to weather?
4. **Present findings**: Prepare demo showing normal → stressed → critical conditions

## Key Questions to Answer for Demo

1. **At what temperature do lines start to overload?**
   - Use Threshold Analysis to find exact answer

2. **Which lines get stressed first?**
   - Look at Alert Dashboard → Top Lines Requiring Attention

3. **How significant is the stress?**
   - Check Grid Health Status indicator
   - View overloaded lines count
   - See margin to overload for critical lines

## Data Source

The app uses the **Hawaii40 synthetic grid** from the `osu_hackathon` folder. This is a real power system test case with:
- 80 transmission lines
- Multiple voltage levels (69 kV and 138 kV)
- Various conductor types
- Realistic load flows

All ratings are calculated using **IEEE Standard 738-2006** for overhead conductor thermal ratings.

## Support

For help:
- Check main `README.md` for detailed documentation
- Review backend logs in terminal for API errors
- Check browser console (F12) for frontend errors
- Refer to `osu_hackathon/README.md` for data documentation

---

**Happy Grid Monitoring!** 🔌⚡
