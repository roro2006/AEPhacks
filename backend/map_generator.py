"""
Hawaii 40 Network - Interactive Map Generator for Grid Monitor
Generates real-time network visualization with power flow data integration
"""

import json
import math
import logging
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, List, Tuple, Optional
from data_models import DataLoadError

# Set up logging
logger = logging.getLogger(__name__)

class GridMapGenerator:
    def __init__(self, data_loader):
        """Initialize with DataLoader instance for accessing grid data"""
        self.data_loader = data_loader
        try:
            self.lines_geojson = data_loader.get_lines_geojson()
            logger.info("Successfully loaded GeoJSON data with %d features", 
                    len(self.lines_geojson.get('features', [])))
        except DataLoadError as e:
            logger.error("Failed to load GeoJSON data: %s", str(e))
            self.lines_geojson = None
        except Exception as e:
            logger.error("Unexpected error loading GeoJSON data: %s", str(e))
            self.lines_geojson = None
        
        # Try to reload if missing
        if not self.lines_geojson:
            try:
                logger.info("Attempting to reload GeoJSON data...")
                self.data_loader.reload_data()
                self.lines_geojson = data_loader.get_lines_geojson()
                logger.info("Successfully reloaded GeoJSON data with %d features",
                        len(self.lines_geojson.get('features', [])))
            except Exception as e:
                logger.error("Failed to reload GeoJSON data: %s", str(e))
                self.lines_geojson = None

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
            'normal': 'rgba(0, 255, 180, 0.2)',   # neon teal
            'caution': 'rgba(255, 204, 0, 0.35)', # amber
            'high': 'rgba(255, 80, 0, 0.45)',     # orange-red
            'critical': 'rgba(255, 0, 60, 0.5)'   # vivid red
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
    width=4.5 if stress_level in ['high', 'critical'] else 3,
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
                        line=dict(width=4.5, color=color),
                        hoverinfo='text',
                        hovertext=line_info,
                        name=f'{int(voltage)} kV Lines',
                        showlegend=(idx == 0),
                        legendgroup=f'{voltage}kV'
                    ))

        # Layout with Apple Maps styling - full screen
        fig.update_layout(
            mapbox=dict(
                style='carto-darkmatter',
                center=dict(lat=center_lat, lon=center_lon),
                zoom=12,
                pitch=0,
                bearing=0
            ),
            height=None,  # Auto height
            autosize=True,  # Auto resize
            hovermode='closest',
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=0.01,
                xanchor='left',
                x=0.01,
                bgcolor='rgba(20, 20, 20, 0.5)',
                bordercolor='rgba(255, 255, 255, 0.05)',
                borderwidth=1,
                font=dict(color='#ffffff', size=12, family='-apple-system, BlinkMacSystemFont, SF Pro Text, sans-serif'),
            ),
            margin=dict(l=0, r=0, t=0, b=0),  # Zero margins
            paper_bgcolor='#0b0b0d',
            plot_bgcolor='#0b0b0d'
        );


        # Generate HTML and inject custom CSS to remove all margins
        # Enable scrollZoom and interactions
        config = {
            'scrollZoom': True,
            'displayModeBar': False,  # Hide the plotly toolbar
            'dragmode': 'pan'
        }
        html_str = fig.to_html(include_plotlyjs='cdn', div_id='grid-map', config=config)

        # Add CSS and custom zoom controls
        custom_css = """
        <style>
            html, body {
                margin: 0 !important;
                padding: 0 !important;
                width: 100% !important;
                height: 100% !important;
                overflow: hidden !important;
            }
            .plotly-graph-div {
                width: 100% !important;
                height: 100vh !important;
                margin: 0 !important;
                padding: 0 !important;
            }
            #grid-map {
                width: 100% !important;
                height: 100vh !important;
                margin: 0 !important;
                padding: 0 !important;
            }

            /* Custom zoom controls */
            .custom-zoom-controls {
                position: fixed;
                bottom: 20px;
                left: 20px;
                z-index: 1000;
                display: flex;
                flex-direction: column;
                gap: 8px;
                background: rgba(20, 20, 22, 0.9);
                backdrop-filter: blur(10px);
                border-radius: 8px;
                padding: 8px;
                border: 1px solid rgba(255, 255, 255, 0.1);
                box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
            }

            .zoom-btn {
                width: 36px;
                height: 36px;
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                color: #ffffff;
                font-size: 20px;
                font-weight: 600;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.2s;
            }

            .zoom-btn:hover {
                background: rgba(255, 255, 255, 0.2);
                transform: scale(1.05);
            }

            .zoom-btn:active {
                transform: scale(0.95);
            }
        </style>
        """

        # Add zoom control JavaScript
        zoom_controls = """
        <div class="custom-zoom-controls">
            <button class="zoom-btn" onclick="zoomIn()">+</button>
            <button class="zoom-btn" onclick="zoomOut()">−</button>
        </div>

        <script>
            function zoomIn() {
                const plotDiv = document.getElementById('grid-map');
                if (plotDiv && plotDiv.layout && plotDiv.layout.mapbox) {
                    const currentZoom = plotDiv.layout.mapbox.zoom || 12;
                    Plotly.relayout(plotDiv, {'mapbox.zoom': currentZoom + 0.5});
                }
            }

            function zoomOut() {
                const plotDiv = document.getElementById('grid-map');
                if (plotDiv && plotDiv.layout && plotDiv.layout.mapbox) {
                    const currentZoom = plotDiv.layout.mapbox.zoom || 12;
                    Plotly.relayout(plotDiv, {'mapbox.zoom': Math.max(1, currentZoom - 0.5)});
                }
            }

            // Enable scroll zoom on the map
            document.addEventListener('DOMContentLoaded', function() {
                const plotDiv = document.getElementById('grid-map');
                if (plotDiv) {
                    plotDiv.on('plotly_relayout', function(eventData) {
                        // Allow zoom interactions
                    });
                }
            });
        </script>
        """

        # Inject CSS after the <head> tag
        html_str = html_str.replace('<head>', '<head>' + custom_css)

        # Inject zoom controls before closing body tag
        html_str = html_str.replace('</body>', zoom_controls + '</body>')

        return html_str

    def generate_outage_map(self, outage_result: Dict) -> str:
        """
        Generate interactive map with outage simulation results

        Args:
            outage_result: Outage simulation result from OutageSimulator

        Returns:
            HTML string of the interactive map with outage visualization
        """
        if not self.lines_geojson:
            raise ValueError("No line GeoJSON data available")

        # Create figure
        fig = go.Figure()

        # Color scheme based on outage stress levels
        stress_colors = {
            'outaged': 'rgba(128, 128, 128, 0.3)',     # Gray/translucent for outaged
            'overloaded': 'rgba(255, 0, 60, 0.6)',     # Bright red for overloaded
            'high_stress': 'rgba(255, 120, 0, 0.5)',   # Orange for high stress
            'affected': 'rgba(255, 204, 0, 0.4)',      # Yellow for affected
            'normal': 'rgba(0, 255, 180, 0.2)'         # Teal for normal
        }

        # Calculate center from line coordinates
        all_coords = []
        for feature in self.lines_geojson['features']:
            for coord in feature['geometry']['coordinates']:
                all_coords.append(coord)

        center_lon = sum(c[0] for c in all_coords) / len(all_coords)
        center_lat = sum(c[1] for c in all_coords) / len(all_coords)

        # Build lookup dictionaries from outage results
        outaged_lines = set(outage_result.get('outage_lines', []))
        loading_dict = {line['name']: line for line in outage_result.get('loading_changes', [])}

        # Group lines by status
        lines_by_status = {
            'outaged': [],
            'overloaded': [],
            'high_stress': [],
            'affected': [],
            'normal': []
        }

        for feature in self.lines_geojson['features']:
            line_name = feature['properties']['Name']
            line_data = loading_dict.get(line_name)

            if line_name in outaged_lines:
                lines_by_status['outaged'].append((feature, line_data))
            elif line_data:
                status = line_data.get('status', 'normal')
                if status in lines_by_status:
                    lines_by_status[status].append((feature, line_data))
                else:
                    lines_by_status['normal'].append((feature, line_data))
            else:
                lines_by_status['normal'].append((feature, None))

        # Add lines grouped by status (outaged lines last so they appear on bottom)
        for status in ['normal', 'affected', 'high_stress', 'overloaded', 'outaged']:
            features = lines_by_status[status]

            for idx, (feature, line_data) in enumerate(features):
                coords = feature['geometry']['coordinates']
                lons = [c[0] for c in coords]
                lats = [c[1] for c in coords]

                # Calculate midpoint
                midpoint_coord = self.calculate_line_midpoint(coords)
                midpoint_text = ""
                if midpoint_coord:
                    midpoint_text = f"<br>Midpoint: {midpoint_coord[1]:.6f}°N, {midpoint_coord[0]:.6f}°W"

                # Build hover text with outage data
                if line_data:
                    if status == 'outaged':
                        line_info = (
                            f"<b style='color: #888'>{feature['properties']['LineName']}</b><br>"
                            f"<b style='color: #ff3c3c'>STATUS: OUTAGED ⚠️</b><br>"
                            f"Line removed from service<br>"
                            f"From: {feature['properties']['BusNameFrom']}<br>"
                            f"To: {feature['properties']['BusNameTo']}"
                            f"{midpoint_text}"
                        )
                    else:
                        change_arrow = "↑" if line_data.get('loading_change_pct', 0) > 0 else "↓"
                        change_color = "#ff4444" if line_data.get('loading_change_pct', 0) > 0 else "#44ff44"

                        # Get solid color for loading display
                        status_color = stress_colors[status].replace('0.6', '1.0').replace('0.5', '1.0').replace('0.4', '1.0')

                        line_info = (
                            f"<b>{feature['properties']['LineName']}</b><br>"
                            f"<b style='color: {status_color}'>Loading: {line_data['loading_pct']:.1f}%</b><br>"
                            f"<b style='color: {change_color}'>Change: {change_arrow} {abs(line_data.get('loading_change_pct', 0)):.1f}%</b><br>"
                            f"Baseline: {line_data.get('baseline_loading_pct', 0):.1f}%<br>"
                            f"Flow: {line_data.get('flow_mva', 0):.1f} MVA<br>"
                            f"Capacity: {line_data.get('s_nom', 0):.1f} MVA<br>"
                            f"From: {feature['properties']['BusNameFrom']}<br>"
                            f"To: {feature['properties']['BusNameTo']}"
                            f"{midpoint_text}"
                        )
                else:
                    line_info = (
                        f"<b>{feature['properties']['LineName']}</b><br>"
                        f"Voltage: {feature['properties']['nomkv']} kV<br>"
                        f"From: {feature['properties']['BusNameFrom']}<br>"
                        f"To: {feature['properties']['BusNameTo']}"
                        f"{midpoint_text}"
                    )

                # Special styling for outaged lines
                line_style = dict(
                    width=5 if status in ['overloaded', 'high_stress'] else (2 if status == 'outaged' else 3),
                    color=stress_colors[status]
                )

                if status == 'outaged':
                    # Dashed line for outaged
                    line_style['dash'] = 'dash'

                fig.add_trace(go.Scattermapbox(
                    lon=lons,
                    lat=lats,
                    mode='lines',
                    line=line_style,
                    hoverinfo='text',
                    hovertext=line_info,
                    name=f'{status.replace("_", " ").title()} Lines',
                    showlegend=(idx == 0),
                    legendgroup=status
                ))

        # Layout with dark map styling
        fig.update_layout(
            mapbox=dict(
                style='carto-darkmatter',
                center=dict(lat=center_lat, lon=center_lon),
                zoom=12,
                pitch=0,
                bearing=0
            ),
            height=None,
            autosize=True,
            hovermode='closest',
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=0.01,
                xanchor='left',
                x=0.01,
                bgcolor='rgba(20, 20, 20, 0.5)',
                bordercolor='rgba(255, 255, 255, 0.05)',
                borderwidth=1,
                font=dict(color='#ffffff', size=12, family='-apple-system, BlinkMacSystemFont, SF Pro Text, sans-serif'),
            ),
            margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor='#0b0b0d',
            plot_bgcolor='#0b0b0d'
        )

        # Generate HTML
        config = {
            'scrollZoom': True,
            'displayModeBar': False,
            'dragmode': 'pan'
        }
        html_str = fig.to_html(include_plotlyjs='cdn', div_id='grid-map', config=config)

        # Add custom CSS (reuse from generate_interactive_map)
        custom_css = """
        <style>
            html, body {
                margin: 0 !important;
                padding: 0 !important;
                width: 100% !important;
                height: 100% !important;
                overflow: hidden !important;
            }
            .plotly-graph-div {
                width: 100% !important;
                height: 100vh !important;
                margin: 0 !important;
                padding: 0 !important;
            }
            #grid-map {
                width: 100% !important;
                height: 100vh !important;
                margin: 0 !important;
                padding: 0 !important;
            }
        </style>
        """

        html_str = html_str.replace('<head>', '<head>' + custom_css)

        return html_str

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
