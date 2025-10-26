"""
AI-Powered Chatbot Service using Claude API
Provides intelligent data explanation and variable impact analysis
"""
import os
from anthropic import Anthropic
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

class GridChatbotService:
    def __init__(self):
        """Initialize the chatbot service with Claude API"""
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key or api_key == 'your_api_key_here':
            raise ValueError(
                "ANTHROPIC_API_KEY not set. Please add your API key to backend/.env file"
            )

        self.client = Anthropic(api_key=api_key)
        # Use Claude 3 Opus as fallback (most widely available)
        self.model = os.getenv('CLAUDE_MODEL', 'claude-3-5-haiku-20241022')
        self.max_tokens = int(os.getenv('MAX_TOKENS', 1024))
        self.temperature = float(os.getenv('TEMPERATURE', 0.7))

    def _build_system_prompt(self, grid_context: dict) -> str:
        """Build comprehensive system prompt with grid context"""
        return f"""You are an intelligent grid monitoring assistant for the AEP Transmission Planning System. You help operators understand transmission line data, predict impacts of variable changes, and make informed decisions.

CURRENT GRID STATE:
{json.dumps(grid_context, indent=2)}

YOUR CAPABILITIES:
1. DATA EXPLANATION: Explain any metric, line status, or grid condition in clear, natural language
2. VARIABLE IMPACT ANALYSIS: Predict and explain what happens when weather or operational parameters change
3. TECHNICAL GUIDANCE: Provide IEEE 738 standard context and industry best practices
4. ALERT INTERPRETATION: Help operators understand stress levels and take appropriate actions

KEY METRICS YOU SHOULD UNDERSTAND:
- Loading Percentage: (Current Flow / Dynamic Rating) × 100
  - <60%: Normal operation
  - 60-90%: Caution zone, monitor closely
  - 90-100%: High stress, prepare contingency plans
  - >100%: CRITICAL - Line is overloaded, immediate action required

- Dynamic Rating: Calculated using IEEE 738 based on:
  - Ambient temperature (higher temp = lower rating)
  - Wind speed (higher wind = better cooling = higher rating)
  - Wind angle (perpendicular wind cools better)
  - Solar radiation (more sun = more heating = lower rating)
  - Conductor properties (type, diameter, emissivity)

- Margin to Overload: How much additional power (in MVA) the line can handle
  - Positive: Available capacity
  - Negative: Amount of overload

WEATHER IMPACT PATTERNS:
- Temperature increase of 10°C typically reduces ratings by 5-8%
- Wind speed increase from 1 to 3 ft/s can improve ratings by 10-15%
- Hot & calm conditions are worst-case scenarios for grid operation
- Solar radiation peaks around noon, adding thermal stress

RESPONSE GUIDELINES:
- Be concise but informative (2-4 sentences typical)
- Use specific numbers from the current grid state
- When predicting impacts, reference similar patterns in current data
- For variable changes, explain both immediate and secondary effects
- Always prioritize safety and operational reliability
- Use natural, conversational language while being technically accurate

Remember: You're helping grid operators make critical decisions. Accuracy and clarity are paramount."""

    def _extract_grid_context(self, ratings_data: dict, weather: dict) -> dict:
        """Extract relevant context from grid data"""
        lines = ratings_data.get('lines', [])
        summary = ratings_data.get('summary', {})

        # Get top stressed lines
        stressed_lines = sorted(
            lines,
            key=lambda x: x['loading_pct'],
            reverse=True
        )[:5]

        # Calculate weather sensitivity indicators
        high_temp_sensitive = [
            l for l in lines
            if l['loading_pct'] > 80  # Lines close to limits
        ]

        return {
            'weather': {
                'temperature_celsius': weather.get('Ta', weather.get('ambient_temp', 25)),
                'temperature_fahrenheit': round(weather.get('Ta', 25) * 9/5 + 32, 1),
                'wind_speed_fps': weather.get('WindVelocity', weather.get('wind_speed', 2.0)),
                'wind_speed_mph': round(weather.get('WindVelocity', 2.0) * 0.681818, 1),
                'wind_angle': weather.get('WindAngleDeg', weather.get('wind_angle', 90)),
                'time_of_day': f"{weather.get('SunTime', weather.get('sun_time', 12))}:00",
            },
            'grid_summary': {
                'total_lines': summary.get('total_lines', len(lines)),
                'critical_count': summary.get('critical_count', 0),
                'high_stress_count': summary.get('high_stress_count', 0),
                'caution_count': summary.get('caution_count', 0),
                'normal_count': summary.get('normal_count', 0),
                'average_loading': round(summary.get('avg_loading', 0), 1),
                'max_loading': round(summary.get('max_loading', 0), 1),
                'max_loading_line': summary.get('max_loading_line', 'N/A'),
            },
            'top_stressed_lines': [
                {
                    'name': l['name'],
                    'branch': l['branch_name'],
                    'loading_pct': round(l['loading_pct'], 1),
                    'rating_mva': round(l['rating_mva'], 1),
                    'flow_mva': round(l['flow_mva'], 1),
                    'margin_mva': round(l['margin_mva'], 1),
                    'stress_level': l['stress_level']
                }
                for l in stressed_lines
            ],
            'temperature_sensitive_lines': len(high_temp_sensitive),
            'operational_status': 'CRITICAL' if summary.get('critical_count', 0) > 0
                                 else 'HIGH STRESS' if summary.get('high_stress_count', 0) > 0
                                 else 'CAUTION' if summary.get('caution_count', 0) > 0
                                 else 'NORMAL'
        }

    def get_response(self, user_message: str, grid_data: dict, weather: dict) -> dict:
        """
        Get AI-powered response with data explanation and impact analysis

        Args:
            user_message: User's question or request
            grid_data: Current grid ratings and line data
            weather: Current weather parameters

        Returns:
            dict with 'response', 'context_used', and 'type' fields
        """
        try:
            # Extract grid context
            grid_context = self._extract_grid_context(grid_data, weather)

            # Build system prompt with context
            system_prompt = self._build_system_prompt(grid_context)

            # Detect query type for better routing
            message_lower = user_message.lower()
            query_type = 'general'

            if any(word in message_lower for word in ['what if', 'change', 'increase', 'decrease', 'impact', 'happen', 'predict']):
                query_type = 'impact_analysis'
            elif any(word in message_lower for word in ['explain', 'what is', 'what does', 'how does', 'why', 'meaning']):
                query_type = 'data_explanation'

            # Call Claude API
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": user_message
                    }
                ]
            )

            # Extract response
            response_text = message.content[0].text

            return {
                'response': response_text,
                'context_used': grid_context,
                'query_type': query_type,
                'model_used': self.model,
                'tokens_used': message.usage.input_tokens + message.usage.output_tokens
            }

        except Exception as e:
            # Graceful fallback
            return {
                'response': f"I encountered an error: {str(e)}. Please check your API configuration.",
                'context_used': {},
                'query_type': 'error',
                'error': str(e)
            }

    def analyze_variable_impact(self, variable: str, change: dict, current_weather: dict, grid_data: dict) -> dict:
        """
        Specialized method for detailed variable impact analysis

        Args:
            variable: Variable to analyze (e.g., 'temperature', 'wind_speed')
            change: Dict with 'from' and 'to' values
            current_weather: Current weather parameters
            grid_data: Current grid data

        Returns:
            Detailed impact analysis
        """
        grid_context = self._extract_grid_context(grid_data, current_weather)

        prompt = f"""Analyze the impact of changing {variable} from {change['from']} to {change['to']}.

Current Grid Context:
{json.dumps(grid_context, indent=2)}

Provide a detailed analysis covering:
1. Expected change in line ratings (percentage impact)
2. Which lines will be most affected and why
3. Potential new overloads or resolved overloads
4. Recommended operational actions
5. Time criticality of the change

Be specific with numbers and line names from the current data."""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=self._build_system_prompt(grid_context),
                messages=[{"role": "user", "content": prompt}]
            )

            return {
                'impact_analysis': message.content[0].text,
                'variable': variable,
                'change': change,
                'context': grid_context
            }

        except Exception as e:
            return {
                'impact_analysis': f"Error analyzing impact: {str(e)}",
                'error': str(e)
            }
