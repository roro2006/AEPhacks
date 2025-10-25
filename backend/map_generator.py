"""
Hawaii 40 Network - Interactive Map Generator for Grid Monitor
Generates real-time network visualization with power flow data integration
"""

import json
import math
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, List, Tuple, Optional

class GridMapGenerator:
    def __init__(self, data_loader):
        """Initialize with DataLoader instance for accessing grid data"""
        self.data_loader = data_loader
        self.lines_geojson = data_loader.get_lines_geojson()

    def calculate_line_midpoint(self, coords: List[List[float]]) -> Optional[List[float]]:
        """Calculate the geographic midpoint along a line string based on distance"""
        if len(coords) < 2:
            return None

        # Calculate distances between consecutive points
        total_distance = 0
        segment_distances = []

        for i in range(len(coords) - 1):
            lon1, lat1 = coords[i]
            lon2, lat2 = coords[i + 1]

            # Haversine distance
            R = 6371  # Earth radius in km
            dlat = math.radians(lat2 - lat1)
            dlon = math.radians(lon2 - lon1)
            a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
            c = 2 * math.asin(math.sqrt(a))
            distance = R * c

            total_distance += distance
            segment_distances.append(distance)

        # Find the midpoint (half the total distance)
        target_distance = total_distance / 2
        accumulated = 0

        for i, segment_dist in enumerate(segment_distances):
            if accumulated + segment_dist >= target_distance:
                # Interpolate within this segment
                frac = (target_distance - accumulated) / segment_dist
                lon1, lat1 = coords[i]
                lon2, lat2 = coords[i + 1]

                mid_lon = lon1 + (lon2 - lon1) * frac
                mid_lat = lat1 + (lat2 - lat1) * frac
                return [mid_lon, mid_lat]

            accumulated += segment_dist

        # Fallback to middle coordinate if calculation fails
        mid_idx = len(coords) // 2
        return coords[mid_idx]

    def get_line_rating_data(self, line_name: str, weather_params: Dict) -> Optional[Dict]:
        """Get real-time rating data for a specific line"""
        from rating_calculator import RatingCalculator

        calculator = RatingCalculator(self.data_loader)
        line_data = self.data_loader.get_line_data(line_name)

        if line_data is None:
            return None

        rating = calculator.calculate_line_rating(line_data, weather_params)
        return rating

    def generate_interactive_map(self, weather_params: Dict, line_ratings: Dict = None) -> str:
        """
        Generate interactive Plotly map with real-time grid data

        Args:
            weather_params: Current weather conditions
            line_ratings: Pre-calculated line ratings (optional)

        Returns:
            HTML string of the interactive map
        """
        if not self.lines_geojson:
            raise ValueError("No line GeoJSON data available")

        # Create figure
        fig = go.Figure()

        # Color scheme based on stress levels
        stress_colors = {
            'normal': 'rgba(22, 163, 74, 0.85)',      # Green
            'caution': 'rgba(202, 138, 4, 0.85)',     # Yellow/Gold
            'high': 'rgba(234, 88, 12, 0.85)',        # Orange
            'critical': 'rgba(220, 38, 38, 0.85)'     # Red
        }

        voltage_colors = {
            138.0: 'rgba(0, 122, 255, 0.85)',    # Apple blue - for 138kV
            69.0: 'rgba(255, 149, 0, 0.85)'      # Apple orange - for 69kV
        }

        # Calculate center from line coordinates
        all_coords = []
        for feature in self.lines_geojson['features']:
            for coord in feature['geometry']['coordinates']:
                all_coords.append(coord)

        center_lon = sum(c[0] for c in all_coords) / len(all_coords)
        center_lat = sum(c[1] for c in all_coords) / len(all_coords)

        # Group lines by stress level if ratings available
        if line_ratings:
            lines_by_stress = {'normal': [], 'caution': [], 'high': [], 'critical': []}
            rating_dict = {r['name']: r for r in line_ratings['lines']}

            for feature in self.lines_geojson['features']:
                line_name = feature['properties']['Name']
                rating = rating_dict.get(line_name)

                if rating:
                    lines_by_stress[rating['stress_level']].append((feature, rating))
                else:
                    # Default to normal if no rating
                    lines_by_stress['normal'].append((feature, None))

            # Add lines grouped by stress level
            for stress_level in ['normal', 'caution', 'high', 'critical']:
                features = lines_by_stress[stress_level]

                for idx, (feature, rating) in enumerate(features):
                    coords = feature['geometry']['coordinates']
                    lons = [c[0] for c in coords]
                    lats = [c[1] for c in coords]

                    # Calculate midpoint
                    midpoint_coord = self.calculate_line_midpoint(coords)
                    midpoint_text = ""
                    if midpoint_coord:
                        midpoint_text = f"<br>Midpoint: {midpoint_coord[1]:.6f}°N, {midpoint_coord[0]:.6f}°W"

                    # Build hover text with real-time data
                    if rating:
                        line_info = (
                            f"<b>{feature['properties']['LineName']}</b><br>"
                            f"<b style='color: {stress_colors[stress_level].replace('0.85', '1.0')}'>Loading: {rating['loading_pct']:.1f}%</b><br>"
                            f"Rating: {rating['rating_mva']:.1f} MVA<br>"
                            f"Flow: {rating['flow_mva']:.1f} MVA<br>"
                            f"Margin: {rating['margin_mva']:.1f} MVA<br>"
                            f"Voltage: {rating['voltage_kv']} kV<br>"
                            f"Conductor: {rating['conductor']}<br>"
                            f"From: {feature['properties']['BusNameFrom']}<br>"
                            f"To: {feature['properties']['BusNameTo']}"
                            f"{midpoint_text}"
                        )
                    else:
                        line_info = (
                            f"<b>{feature['properties']['LineName']}</b><br>"
                            f"Voltage: {feature['properties']['nomkv']} kV<br>"
                            f"Circuit: {feature['properties']['Circuit']}<br>"
                            f"From: {feature['properties']['BusNameFrom']}<br>"
                            f"To: {feature['properties']['BusNameTo']}"
                            f"{midpoint_text}"
                        )

                    fig.add_trace(go.Scattermapbox(
                        lon=lons,
                        lat=lats,
                        mode='lines',
                        line=dict(
                            width=3.5 if stress_level in ['high', 'critical'] else 2.5,
                            color=stress_colors[stress_level]
                        ),
                        hoverinfo='text',
                        hovertext=line_info,
                        name=f'{stress_level.title()} Lines',
                        showlegend=(idx == 0),
                        legendgroup=stress_level,
                        customdata=[[line_name, rating]] if rating else [[line_name, None]]
                    ))
        else:
            # Fallback to voltage-based coloring if no ratings
            for voltage, color in voltage_colors.items():
                voltage_lines = [f for f in self.lines_geojson['features']
                                if f['properties']['nomkv'] == voltage]

                for idx, feature in enumerate(voltage_lines):
                    coords = feature['geometry']['coordinates']
                    lons = [c[0] for c in coords]
                    lats = [c[1] for c in coords]

                    line_info = (
                        f"<b>{feature['properties']['LineName']}</b><br>"
                        f"Voltage: {feature['properties']['nomkv']} kV<br>"
                        f"Circuit: {feature['properties']['Circuit']}<br>"
                        f"From: {feature['properties']['BusNameFrom']}<br>"
                        f"To: {feature['properties']['BusNameTo']}"
                    )

                    fig.add_trace(go.Scattermapbox(
                        lon=lons,
                        lat=lats,
                        mode='lines',
                        line=dict(width=2.5, color=color),
                        hoverinfo='text',
                        hovertext=line_info,
                        name=f'{int(voltage)} kV Lines',
                        showlegend=(idx == 0),
                        legendgroup=f'{voltage}kV'
                    ))

        # Layout with Apple Maps styling
        fig.update_layout(
            title={
                'text': f'Hawaii Electrical Network - Real-Time Status<br><sub>Temp: {weather_params["Ta"]}°C | Wind: {weather_params["WindVelocity"]} ft/s</sub>',
                'x': 0.5,
                'xanchor': 'center',
                'font': {
                    'size': 20,
                    'color': '#1d1d1f',
                    'family': '-apple-system, BlinkMacSystemFont, "SF Pro Display", sans-serif'
                }
            },
            mapbox=dict(
                style='open-street-map',
                center=dict(lat=center_lat, lon=center_lon),
                zoom=10.5
            ),
            height=800,
            hovermode='closest',
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=0.02,
                xanchor='left',
                x=0.01,
                bgcolor='rgba(255, 255, 255, 0.95)',
                bordercolor='rgba(0, 0, 0, 0.1)',
                borderwidth=1
            ),
            margin=dict(l=0, r=0, t=80, b=0),
            paper_bgcolor='#f5f5f7',
            plot_bgcolor='#f5f5f7'
        )

        return fig.to_html(include_plotlyjs='cdn', div_id='grid-map')

    def get_line_details_for_chat(self, line_name: str, weather_params: Dict) -> Dict:
        """Get comprehensive line details formatted for chatbot responses"""
        rating = self.get_line_rating_data(line_name, weather_params)

        if not rating:
            return {
                'found': False,
                'message': f"Line {line_name} not found in the system"
            }

        return {
            'found': True,
            'name': rating['name'],
            'branch_name': rating['branch_name'],
            'loading_pct': rating['loading_pct'],
            'stress_level': rating['stress_level'],
            'rating_mva': rating['rating_mva'],
            'flow_mva': rating['flow_mva'],
            'margin_mva': rating['margin_mva'],
            'voltage_kv': rating['voltage_kv'],
            'conductor': rating['conductor'],
            'connections': f"{rating['bus0']} → {rating['bus1']}"
        }
