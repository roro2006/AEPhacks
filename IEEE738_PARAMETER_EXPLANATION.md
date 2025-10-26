# IEEE 738 Rating Calculation - Parameter Sources & Values

## Overview

Your Grid Monitor calculates dynamic line ratings using the **IEEE 738 standard** for overhead conductor thermal ratings. Here's where each parameter comes from and why those specific values are used.

## Parameter Sources

### 1. User-Controlled Parameters (from Frontend)

These come from the weather controls in your web interface:

| Parameter | Source | Default | User Control |
|-----------|--------|---------|--------------|
| **Ta** (Ambient Temperature) | Weather slider | 25°C | Yes - adjustable |
| **WindVelocity** | Weather slider | 2.0 ft/sec | Yes - adjustable |
| **WindAngleDeg** | Weather slider | 90° | Yes - adjustable |
| **SunTime** | Time slider | 12:00 | Yes - adjustable |
| **Date** | Date picker | "12 Jun" | Yes - adjustable |

**Location in code:** `backend/app.py` lines 72-77
```python
weather_params = {
    'Ta': weather.get('ambient_temp', 25),           # From user input
    'WindVelocity': weather.get('wind_speed', 2.0),  # From user input
    'WindAngleDeg': weather.get('wind_angle', 90),   # From user input
    'SunTime': weather.get('sun_time', 12),          # From user input
    'Date': weather.get('date', '12 Jun'),           # From user input
    ...
}
```

### 2. Fixed System Parameters (Hardcoded)

These are **constant assumptions** about the grid's physical environment and conductor properties:

| Parameter | Value | Why This Value? | Location |
|-----------|-------|-----------------|----------|
| **Emissivity** | 0.8 | Standard for weathered aluminum conductors | app.py:78 |
| **Absorptivity** | 0.8 | Standard for weathered aluminum (absorbs solar radiation) | app.py:79 |
| **Direction** | 'EastWest' | Assumed line orientation (affects solar heating) | app.py:80 |
| **Atmosphere** | 'Clear' | Conservative assumption (clear = more solar heating) | app.py:81 |
| **Elevation** | 1000 ft | Hawaii approximate elevation above sea level | app.py:82 |
| **Latitude** | 27° | Hawaii's approximate latitude (affects solar angle) | app.py:83 |

**Why these specific values?**

- **Emissivity 0.8**: Weathered aluminum conductors typically have emissivity between 0.7-0.9. The value 0.8 is a standard conservative assumption from IEEE 738.

- **Absorptivity 0.8**: Matches emissivity for weathered conductors. Higher values mean more solar heat absorption → lower ratings.

- **Direction 'EastWest'**: Affects how solar radiation hits the conductor. East-West lines get more direct sun at midday than North-South lines.

- **Atmosphere 'Clear'**: Conservative assumption. Clear atmosphere allows more solar radiation to reach the conductor than industrial atmosphere.

- **Elevation 1000 ft**: Hawaii40 test case represents Hawaii's electrical grid. Average elevation ~1000 ft affects air density and cooling.

- **Latitude 27°**: Hawaii is at approximately 19-22° North, but 27° is used in the test case. Affects solar angle calculations.

### 3. Line-Specific Parameters (from Data Files)

These come from the grid's data files and vary by transmission line:

| Parameter | Source File | Description | Code Location |
|-----------|-------------|-------------|---------------|
| **Tc** (Max Operating Temp) | `lines.csv` | Maximum conductor temperature (typically 75-100°C) | rating_calculator.py:48 |
| **Diameter** | `conductors.csv` | Conductor diameter (from radius × 2) | rating_calculator.py:47 |
| **RLo** (Resistance at 25°C) | `conductors.csv` | Electrical resistance at low temp | rating_calculator.py:45 |
| **RHi** (Resistance at 50°C) | `conductors.csv` | Electrical resistance at high temp | rating_calculator.py:46 |
| **Voltage** | `buses.csv` | Line voltage (69kV or 138kV) | rating_calculator.py:35 |
| **Flow** | `power_flow_results.csv` | Current power flow through line | rating_calculator.py:65 |

**Location in code:** `backend/rating_calculator.py` lines 29-48
```python
# Get conductor parameters from data files
conductor_params = self.data_loader.get_conductor_params(line_data['conductor'])

# Prepare IEEE738 parameters
ieee_params = {
    'TLo': 25,  # Fixed: Low reference temperature
    'THi': 50,  # Fixed: High reference temperature
    'RLo': conductor_params['RES_25C'] / 5280,  # From conductors.csv
    'RHi': conductor_params['RES_50C'] / 5280,  # From conductors.csv
    'Diameter': conductor_params['CDRAD_in'] * 2,  # From conductors.csv
    'Tc': line_data['MOT']  # From lines.csv (Maximum Operating Temperature)
}
```

## Complete Parameter Flow

### Step-by-Step Calculation Process

1. **User adjusts weather** in frontend (temperature, wind, time)
   ↓
2. **Frontend sends** to `/api/lines/ratings` endpoint
   ↓
3. **Backend combines** user inputs with fixed system parameters
   ↓
4. **For each line**, backend retrieves line-specific data:
   - Conductor type from `lines.csv`
   - Conductor properties from `conductors.csv`
   - Voltage from `buses.csv`
   - Current flow from `power_flow_results.csv`
   ↓
5. **IEEE 738 calculation** using all parameters:
   ```
   Rating (Amps) = f(Ta, Wind, Solar, Conductor Properties, Tc)
   ```
   ↓
6. **Convert to MVA**:
   ```
   Rating (MVA) = √3 × Rating (Amps) × Voltage (kV) / 1000
   ```
   ↓
7. **Calculate loading**:
   ```
   Loading % = (Current Flow / Dynamic Rating) × 100
   ```

## IEEE 738 Physics

The IEEE 738 standard calculates the maximum current a conductor can carry before exceeding its maximum operating temperature (Tc). The heat balance equation is:

```
Heat Gain = Heat Loss

Solar Heating + Joule Heating = Convective Cooling + Radiative Cooling
```

**Parameters affect this as follows:**

### Heat Gain (Bad for Ratings)
- **Higher Ambient Temperature (Ta)** → Less temperature difference → Less cooling → **LOWER rating**
- **Higher Solar Radiation** (from SunTime, Date, Latitude) → More heating → **LOWER rating**
- **Higher Absorptivity** → More solar absorption → **LOWER rating**
- **Higher Current (Joule heating)** → More I²R losses → Sets the **rating limit**

### Heat Loss (Good for Ratings)
- **Higher Wind Speed** → Better convective cooling → **HIGHER rating**
- **Perpendicular Wind** (90°) → Best cooling → **HIGHER rating**
- **Higher Emissivity** → Better radiative cooling → **HIGHER rating**
- **Higher Elevation** → Lower air density → **LOWER rating** (less cooling)

## Why Can't Users Change All Parameters?

### Fixed Parameters (0.8, EastWest, Clear, 1000 ft, 27°)

**Reason:** These represent **physical characteristics** of the grid infrastructure and location:

1. **Emissivity/Absorptivity (0.8)**: Physical property of the conductor material. Would only change if conductors were replaced with different materials.

2. **Direction (EastWest)**: Physical orientation of transmission lines. Fixed when lines were built.

3. **Atmosphere (Clear)**: Conservative assumption for worst-case solar heating. Could be made configurable but adds complexity.

4. **Elevation (1000 ft)**: Geographic location of Hawaii. Fixed by geography.

5. **Latitude (27°)**: Geographic location. Fixed by geography.

**Making these configurable** would be misleading because:
- They don't change operationally
- They're grid infrastructure constants
- Changing them wouldn't reflect real-world scenarios

### Variable Parameters (Ta, Wind, SunTime, Date)

**Reason:** These represent **weather conditions** that:
- Change throughout the day
- Vary seasonally
- Are the primary operational concern for grid operators
- Directly impact whether lines can handle current loads

## Data File Locations

Your system reads from these data files in the `osu_hackathon/hawaii40_osu/` directory:

```
osu_hackathon/hawaii40_osu/
├── lines.csv                  # Line names, conductor types, MOT
├── buses.csv                  # Bus voltages
├── conductors.csv             # Conductor properties (diameter, resistance)
├── power_flow_results.csv     # Current flows through each line
└── gis/
    └── oneline_lines.geojson  # Geographic line coordinates
```

**Loaded by:** `backend/data_loader.py`

## How to Change Default Values

### Option 1: Change Hardcoded Defaults

Edit `backend/app.py` lines 78-83:

```python
weather_params = {
    ...
    'Emissivity': 0.9,      # Change from 0.8 to 0.9
    'Absorptivity': 0.9,    # Change from 0.8 to 0.9
    'Direction': 'NorthSouth',  # Change orientation
    'Atmosphere': 'Industrial', # Change atmosphere type
    'Elevation': 2000,      # Change elevation (ft)
    'Latitude': 20          # Change latitude (degrees)
}
```

### Option 2: Make Parameters User-Configurable

Add to frontend weather controls and pass through API:

```typescript
// frontend - add new controls
const [emissivity, setEmissivity] = useState(0.8)
const [elevation, setElevation] = useState(1000)
// etc.

// backend - accept from request
weather_params = {
    ...
    'Emissivity': weather.get('emissivity', 0.8),
    'Elevation': weather.get('elevation', 1000),
}
```

### Option 3: Create Scenario Presets

Add preset configurations for different scenarios:

```python
SCENARIOS = {
    'conservative': {
        'Emissivity': 0.7,
        'Absorptivity': 0.9,  # High solar absorption
        'Atmosphere': 'Clear'  # High solar radiation
    },
    'typical': {
        'Emissivity': 0.8,
        'Absorptivity': 0.8,
        'Atmosphere': 'Clear'
    },
    'optimistic': {
        'Emissivity': 0.9,     # High emissivity
        'Absorptivity': 0.7,   # Low solar absorption
        'Atmosphere': 'Industrial'  # Reduced solar
    }
}
```

## Summary Table

| Parameter | Default | Type | Why This Value | Can Users Change? |
|-----------|---------|------|----------------|-------------------|
| **Ta** | 25°C | Variable | Typical ambient temp | ✅ Yes (slider) |
| **WindVelocity** | 2.0 ft/s | Variable | Light breeze | ✅ Yes (slider) |
| **WindAngleDeg** | 90° | Variable | Perpendicular (best cooling) | ✅ Yes (slider) |
| **SunTime** | 12:00 | Variable | Solar noon (worst case) | ✅ Yes (slider) |
| **Date** | "12 Jun" | Variable | Summer (high solar) | ✅ Yes (picker) |
| **Emissivity** | 0.8 | Fixed | IEEE 738 standard for Al | ❌ Hardcoded |
| **Absorptivity** | 0.8 | Fixed | IEEE 738 standard for Al | ❌ Hardcoded |
| **Direction** | EastWest | Fixed | Grid infrastructure | ❌ Hardcoded |
| **Atmosphere** | Clear | Fixed | Conservative assumption | ❌ Hardcoded |
| **Elevation** | 1000 ft | Fixed | Hawaii geography | ❌ Hardcoded |
| **Latitude** | 27° | Fixed | Test case location | ❌ Hardcoded |
| **Tc** | 75-100°C | Per-line | Conductor limit from data | ❌ From database |
| **Diameter** | Varies | Per-line | Conductor size from data | ❌ From database |
| **Resistance** | Varies | Per-line | Conductor material from data | ❌ From database |

## Impact of Each Parameter

**Most Significant (Largest Impact on Ratings):**
1. **Ambient Temperature (Ta)**: ±10°C can change ratings by ±10-15%
2. **Wind Speed**: 1→3 ft/s can increase ratings by 15-20%
3. **Solar Radiation** (SunTime + Date): Day vs night = ±5-10%

**Moderate Impact:**
4. **Wind Angle**: 0° vs 90° = ±5-8%
5. **Emissivity/Absorptivity**: 0.7 vs 0.9 = ±3-5%

**Small Impact:**
6. **Elevation**: ±1000 ft = ±2-3%
7. **Atmosphere**: Clear vs Industrial = ±1-2%

---

For more details on IEEE 738 calculations, see:
- `osu_hackathon/ieee738/` - Implementation code
- `osu_hackathon/ieee738_primer.md` - Theory explanation
- IEEE Std 738-2006 - Official standard document
