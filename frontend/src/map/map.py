#!/usr/bin/env python3
"""
Hawaii 40 Network - Apple Maps Style Interactive Map Generator
Create beautiful, minimal Apple Maps-style maps showing only transmission lines

Usage:
    python create_interactive_map.py [--type plotly|folium] [--output filename.html]
"""

import json
import argparse
from pathlib import Path
import pandas as pd
import math

def calculate_line_midpoint(coords):
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

def load_data():
    """Load GeoJSON data for transmission lines and transformer/bus CSV data"""
    script_dir = Path(__file__).parent

    with open(script_dir / 'gis' / 'oneline_lines.geojson', 'r') as f:
        lines_data = json.load(f)

    # Load transformer and bus data
    transformers_df = pd.read_csv(script_dir / 'csv' / 'transformers.csv')
    buses_df = pd.read_csv(script_dir / 'csv' / 'buses.csv')

    # Merge transformers with bus locations (use bus0 for transformer position)
    transformers_df = transformers_df.merge(
        buses_df[['name', 'x', 'y', 'BusName']],
        left_on='bus0',
        right_on='name',
        suffixes=('', '_from')
    )
    transformers_df = transformers_df.merge(
        buses_df[['name', 'BusName']],
        left_on='bus1',
        right_on='name',
        suffixes=('', '_to')
    )

    return lines_data, transformers_df

def create_plotly_map(lines_data, transformers_df, output_file='hawaii40_interactive_map.html'):
    """Create Apple Maps-style interactive map using Plotly"""
    try:
        import plotly.graph_objects as go
    except ImportError:
        print("Error: plotly not installed. Run: pip install plotly")
        return False

    print("Creating Apple Maps-style interactive map with Plotly...")

    # Create figure
    fig = go.Figure()

    # Apple Maps-inspired color scheme - elegant and subtle
    voltage_colors = {
        138.0: 'rgba(0, 122, 255, 0.85)',    # Apple blue - for 138kV
        69.0: 'rgba(255, 149, 0, 0.85)'      # Apple orange - for 69kV
    }

    # Calculate center from line coordinates
    all_coords = []
    for feature in lines_data['features']:
        for coord in feature['geometry']['coordinates']:
            all_coords.append(coord)

    center_lon = sum(c[0] for c in all_coords) / len(all_coords)
    center_lat = sum(c[1] for c in all_coords) / len(all_coords)

    # Add transmission lines with Apple Maps styling
    for voltage, color in voltage_colors.items():
        voltage_lines = [f for f in lines_data['features'] if f['properties']['nomkv'] == voltage]

        for idx, feature in enumerate(voltage_lines):
            coords = feature['geometry']['coordinates']
            lons = [c[0] for c in coords]
            lats = [c[1] for c in coords]

            # Calculate midpoint for this line
            midpoint_coord = calculate_line_midpoint(coords)
            midpoint_text = ""
            if midpoint_coord:
                midpoint_text = f"<br>Midpoint: {midpoint_coord[1]:.6f}°N, {midpoint_coord[0]:.6f}°W"

            line_info = (f"<b>{feature['properties']['LineName']}</b><br>"
                        f"Voltage: {feature['properties']['nomkv']} kV<br>"
                        f"Circuit: {feature['properties']['Circuit']}<br>"
                        f"From: {feature['properties']['BusNameFrom']}<br>"
                        f"To: {feature['properties']['BusNameTo']}"
                        f"{midpoint_text}")

            fig.add_trace(go.Scattermapbox(
                lon=lons,
                lat=lats,
                mode='lines',
                line=dict(width=2.5, color=color),
                hoverinfo='text',
                hovertext=line_info,
                name=f'{int(voltage)} kV Lines',
                showlegend=(idx == 0),  # Only show first line in legend
                legendgroup=f'{voltage}kV'
            ))

    # Add transformers as large, visible triangle markers
    transformer_color = '#FF2D55'  # Bright magenta/pink for high visibility

    for idx, transformer in transformers_df.iterrows():
        transformer_info = (f"<b>Transformer: {transformer['name']}</b><br>"
                          f"From: {transformer['BusName']} (Bus {transformer['bus0']})<br>"
                          f"To: {transformer['BusName_to']} (Bus {transformer['bus1']})<br>"
                          f"Rating: {transformer['s_nom']:.1f} MVA<br>"
                          f"Impedance: {transformer['x']:.4f} + j{transformer['r']:.4f}")

        fig.add_trace(go.Scattermapbox(
            lon=[transformer['x']],
            lat=[transformer['y']],
            mode='markers',
            marker=dict(
                size=18,  # Much larger for visibility
                color=transformer_color,
                symbol='triangle',
                opacity=1.0  # Full opacity
            ),
            hoverinfo='text',
            hovertext=transformer_info,
            name='Transformers',
            showlegend=(idx == 0),  # Only show first transformer in legend
            legendgroup='transformers'
        ))
    
    # Add midpoints for all transmission lines
    midpoint_idx = 0
    for feature in lines_data['features']:
        coords = feature['geometry']['coordinates']
        midpoint_coord = calculate_line_midpoint(coords)
        if midpoint_coord:
            voltage = feature['properties']['nomkv']
            color = voltage_colors.get(voltage, '#007AFF')
            
            midpoint_info = f"<b>Midpoint of:</b><br>{feature['properties']['LineName']}"
            
            fig.add_trace(go.Scattermapbox(
                lon=[midpoint_coord[0]],
                lat=[midpoint_coord[1]],
                mode='markers',
                marker=dict(
                    size=8,
                    color=color,
                    opacity=0.9,
                    symbol='circle'
                ),
                hoverinfo='text',
                hovertext=midpoint_info,
                name='Line Midpoints',
                showlegend=(midpoint_idx == 0),
                legendgroup='midpoints'
            ))
            midpoint_idx += 1

    # Apple Maps-inspired layout - clean and minimal
    fig.update_layout(
        title={
            'text': 'Hawaii Electrical Network',
            'x': 0.5,
            'xanchor': 'center',
            'font': {
                'size': 22,
                'color': '#1d1d1f',  # Apple's text color
                'family': '-apple-system, BlinkMacSystemFont, "SF Pro Display", "Helvetica Neue", Arial, sans-serif'
            }
        },
        mapbox=dict(
            style='open-street-map',  # Shows roads in darker grey
            center=dict(lat=center_lat, lon=center_lon),
            zoom=10.5
        ),
        height=850,
        hovermode='closest',
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=0.02,
            xanchor='left',
            x=0.01,
            bgcolor='rgba(255, 255, 255, 0.95)',
            bordercolor='rgba(0, 0, 0, 0.1)',
            borderwidth=1,
            font=dict(
                family='-apple-system, BlinkMacSystemFont, "SF Pro Display", sans-serif',
                size=12,
                color='#1d1d1f'
            )
        ),
        margin=dict(l=0, r=0, t=60, b=0),
        paper_bgcolor='#f5f5f7',  # Apple's light gray
        plot_bgcolor='#f5f5f7'
    )

    # Save to HTML with custom JavaScript for side panel
    html_str = fig.to_html(include_plotlyjs='cdn')

    # Add custom CSS and JavaScript for side panel
    side_panel_code = """
    <style>
        #sidePanel {
            position: fixed;
            right: 20px;
            top: 0;
            width: 400px;
            height: 100vh;
            background: rgba(26, 41, 66, 0.95);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            box-shadow: -4px 0 20px rgba(0, 0, 0, 0.3);
            z-index: 10000;
            color: #e3f2fd;
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Helvetica Neue", Arial, sans-serif;
            overflow-y: auto;
            display: none;
        }

        #sidePanel.open {
            display: block;
        }

        #sidePanelContent {
            padding: 24px;
        }

        #sidePanelHeader {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 24px;
            padding-bottom: 16px;
            border-bottom: 1px solid rgba(100, 150, 200, 0.3);
        }

        #sidePanelTitle {
            font-size: 18px;
            font-weight: 600;
            color: #e3f2fd;
            margin: 0;
            line-height: 1.4;
            flex: 1;
            padding-right: 12px;
        }

        #closePanel {
            background: none;
            border: none;
            color: #64b5f6;
            font-size: 28px;
            cursor: pointer;
            padding: 0;
            width: 32px;
            height: 32px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            transition: background 0.2s;
        }

        #closePanel:hover {
            background: rgba(100, 181, 246, 0.1);
        }

        .info-section {
            margin-bottom: 24px;
        }

        .info-section-title {
            font-size: 14px;
            font-weight: 600;
            color: #90caf9;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 12px;
        }

        .info-row {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid rgba(100, 150, 200, 0.15);
        }

        .info-row:last-child {
            border-bottom: none;
        }

        .info-label {
            color: #90caf9;
            font-size: 14px;
        }

        .info-value {
            color: #e3f2fd;
            font-size: 14px;
            font-weight: 500;
            text-align: right;
        }

        .weather-placeholder {
            background: rgba(100, 181, 246, 0.1);
            border: 1px dashed rgba(100, 181, 246, 0.3);
            border-radius: 8px;
            padding: 16px;
            text-align: center;
            color: #90caf9;
            font-size: 13px;
        }

        #testButton {
            position: fixed;
            bottom: 20px;
            left: 20px;
            background: rgba(100, 181, 246, 0.9);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", sans-serif;
            font-size: 14px;
            font-weight: 500;
            z-index: 9999;
            backdrop-filter: blur(10px);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
        }

        #testButton:hover {
            background: rgba(100, 181, 246, 1);
        }
    </style>

    <button id="testButton" onclick="testPanel()">Test Panel</button>

    <div id="sidePanel">
        <div id="sidePanelContent">
            <div id="sidePanelHeader">
                <h2 id="sidePanelTitle">Transmission Line</h2>
                <button id="closePanel" onclick="closeSidePanel()">&times;</button>
            </div>

            <div class="info-section">
                <div class="info-section-title">Line Information</div>
                <div id="lineInfo"></div>
            </div>

            <div class="info-section">
                <div class="info-section-title">Location</div>
                <div id="locationInfo"></div>
            </div>

            <div class="info-section">
                <div class="info-section-title">Weather Data</div>
                <div class="weather-placeholder">
                    Weather API integration coming soon...<br>
                    <small style="opacity: 0.7; margin-top: 8px; display: block;">
                    Wind gusts, elevation, temperature, etc.
                    </small>
                </div>
            </div>
        </div>
    </div>

    <script>
        let sidePanelOpen = false;

        function testPanel() {
            const testData = {
                name: 'TEST LINE (Sample)',
                voltage: '138.0',
                circuit: '1',
                from: 'Station A',
                to: 'Station B',
                midpoint: {
                    lat: '21.326051°N',
                    lon: '-157.877774°W'
                }
            };
            openSidePanel(testData);
        }

        function openSidePanel(lineData) {
            const panel = document.getElementById('sidePanel');
            const title = document.getElementById('sidePanelTitle');
            const lineInfo = document.getElementById('lineInfo');
            const locationInfo = document.getElementById('locationInfo');

            // Set title
            title.textContent = lineData.name || 'Line Details';

            // Set line information
            lineInfo.innerHTML = `
                <div class="info-row">
                    <span class="info-label">Voltage</span>
                    <span class="info-value">${lineData.voltage} kV</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Circuit</span>
                    <span class="info-value">${lineData.circuit}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">From</span>
                    <span class="info-value">${lineData.from}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">To</span>
                    <span class="info-value">${lineData.to}</span>
                </div>
            `;

            // Set location information
            if (lineData.midpoint) {
                locationInfo.innerHTML = `
                    <div class="info-row">
                        <span class="info-label">Latitude</span>
                        <span class="info-value">${lineData.midpoint.lat}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Longitude</span>
                        <span class="info-value">${lineData.midpoint.lon}</span>
                    </div>
                `;
            }

            panel.classList.add('open');
            sidePanelOpen = true;
        }

        function closeSidePanel() {
            const panel = document.getElementById('sidePanel');
            panel.style.display = 'none';
            panel.classList.remove('open');
            sidePanelOpen = false;
        }

        // Add click event listener to the plot
        function attachClickListener() {
            const plotDiv = document.querySelector('.plotly-graph-div');
            if (plotDiv && plotDiv.on) {
                plotDiv.on('plotly_click', function(data) {
                    console.log('Plotly click detected:', data);
                    if (data.points && data.points.length > 0) {
                        const point = data.points[0];
                        console.log('Point clicked:', point);

                        // Only process line clicks (not markers)
                        if (point.data.mode === 'lines') {
                            // Parse the hovertext to extract line data
                            const hovertext = point.data.hovertext;

                            // Extract information from hovertext
                            const nameMatch = hovertext.match(/<b>(.*?)<\\/b>/);
                            const voltageMatch = hovertext.match(/Voltage: ([\\d.]+) kV/);
                            const circuitMatch = hovertext.match(/Circuit: (.*?)<br>/);
                            const fromMatch = hovertext.match(/From: (.*?)<br>/);
                            const toMatch = hovertext.match(/To: (.*?)<br>/);
                            const midpointMatch = hovertext.match(/Midpoint: ([\\d.]+)°N, ([\\d.-]+)°W/);

                            const lineData = {
                                name: nameMatch ? nameMatch[1] : 'Unknown Line',
                                voltage: voltageMatch ? voltageMatch[1] : 'N/A',
                                circuit: circuitMatch ? circuitMatch[1] : 'N/A',
                                from: fromMatch ? fromMatch[1] : 'N/A',
                                to: toMatch ? toMatch[1] : 'N/A',
                                midpoint: midpointMatch ? {
                                    lat: midpointMatch[1] + '°N',
                                    lon: midpointMatch[2] + '°W'
                                } : null
                            };

                            openSidePanel(lineData);
                        }
                    }
                });
                console.log('Click listener attached successfully');
            } else {
                console.log('Plot div not ready, retrying...');
                setTimeout(attachClickListener, 100);
            }
        }

        // Try to attach listener when DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', attachClickListener);
        } else {
            attachClickListener();
        }

        // Also try after a short delay to ensure Plotly is fully loaded
        setTimeout(attachClickListener, 500);
    </script>
    """

    # Insert the side panel code before the closing </body> tag
    html_str = html_str.replace('</body>', side_panel_code + '\n</body>')

    # Write the modified HTML
    with open(output_file, 'w') as f:
        f.write(html_str)

    print(f"[OK] Apple Maps-style map saved to: {output_file}")
    print(f"  Open in browser to view!")
    return True

def create_folium_map(lines_data, transformers_df, output_file='hawaii40_folium_map.html'):
    """Create Apple Maps-style interactive map using Folium"""
    try:
        import folium
        from folium import plugins
    except ImportError:
        print("Error: folium not installed. Run: pip install folium")
        return False

    print("Creating Apple Maps-style interactive map with Folium...")

    # Calculate center from line coordinates
    all_coords = []
    for feature in lines_data['features']:
        for coord in feature['geometry']['coordinates']:
            all_coords.append(coord)

    center_lon = sum(c[0] for c in all_coords) / len(all_coords)
    center_lat = sum(c[1] for c in all_coords) / len(all_coords)

    # Create base map with roads visible in darker grey
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=11,
        tiles='OpenStreetMap',  # Shows roads in darker grey
        control_scale=True,
        zoom_control=True,
        prefer_canvas=True
    )

    # Create feature groups with Apple-inspired colors
    lines_138kv = folium.FeatureGroup(name='138 kV Lines', show=True)
    lines_69kv = folium.FeatureGroup(name='69 kV Lines', show=True)
    transformers_group = folium.FeatureGroup(name='Transformers', show=True)
    midpoints_group = folium.FeatureGroup(name='Line Midpoints', show=True)

    voltage_colors = {
        138.0: '#007AFF',  # Apple blue
        69.0: '#FF9500'    # Apple orange
    }
    transformer_color = '#FF2D55'  # Bright magenta/pink for high visibility

    # Add transmission lines with minimal, elegant styling
    for feature in lines_data['features']:
        coords = feature['geometry']['coordinates']
        locations = [[c[1], c[0]] for c in coords]

        voltage = feature['properties']['nomkv']
        color = voltage_colors.get(voltage, '#007AFF')

        # Calculate midpoint for this line
        midpoint_coord = calculate_line_midpoint(coords)
        midpoint_row = ""
        if midpoint_coord:
            midpoint_row = f"""
                <tr style="border-bottom: 1px solid #e5e5e5;">
                    <td style="padding: 4px 8px 4px 0; color: #86868b;">Midpoint</td>
                    <td style="padding: 4px 0; font-weight: 500;">{midpoint_coord[1]:.6f}°N, {midpoint_coord[0]:.6f}°W</td>
                </tr>"""

        popup_html = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif;
                    font-size: 13px; min-width: 250px; color: #1d1d1f;">
            <div style="font-size: 15px; font-weight: 600; margin-bottom: 8px; color: #000;">
                {feature['properties']['LineName']}
            </div>
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="border-bottom: 1px solid #e5e5e5;">
                    <td style="padding: 4px 8px 4px 0; color: #86868b;">Voltage</td>
                    <td style="padding: 4px 0; font-weight: 500;">{voltage} kV</td>
                </tr>
                <tr style="border-bottom: 1px solid #e5e5e5;">
                    <td style="padding: 4px 8px 4px 0; color: #86868b;">Circuit</td>
                    <td style="padding: 4px 0; font-weight: 500;">{feature['properties']['Circuit']}</td>
                </tr>
                <tr style="border-bottom: 1px solid #e5e5e5;">
                    <td style="padding: 4px 8px 4px 0; color: #86868b;">From</td>
                    <td style="padding: 4px 0; font-weight: 500;">{feature['properties']['BusNameFrom']}</td>
                </tr>
                <tr style="border-bottom: 1px solid #e5e5e5;">
                    <td style="padding: 4px 8px 4px 0; color: #86868b;">To</td>
                    <td style="padding: 4px 0; font-weight: 500;">{feature['properties']['BusNameTo']}</td>
                </tr>{midpoint_row}
            </table>
        </div>
        """

        line = folium.PolyLine(
            locations=locations,
            color=color,
            weight=2.5,
            opacity=0.85,
            popup=folium.Popup(popup_html, max_width=300),
            smooth_factor=1.5
        )

        if voltage == 138.0:
            line.add_to(lines_138kv)
        else:
            line.add_to(lines_69kv)
        
        # Calculate and add midpoint marker
        midpoint_coord = calculate_line_midpoint(coords)
        if midpoint_coord:
            # Note: midpoint_coord is [lon, lat], folium expects [lat, lon]
            midpoint_marker = folium.CircleMarker(
                location=[midpoint_coord[1], midpoint_coord[0]],
                radius=4,
                color='white',
                weight=1.5,
                fill=True,
                fillColor=color,
                fillOpacity=0.8,
                popup=folium.Popup(
                    f"<div style='font-family: -apple-system; font-size: 13px;'>"
                    f"<b>Midpoint of:</b><br>{feature['properties']['LineName']}"
                    f"</div>",
                    max_width=300
                )
            )
            midpoint_marker.add_to(midpoints_group)

    # Add transformers as triangle markers
    for _, transformer in transformers_df.iterrows():
        popup_html = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif;
                    font-size: 13px; min-width: 250px; color: #1d1d1f;">
            <div style="font-size: 15px; font-weight: 600; margin-bottom: 8px; color: #FF2D55;">
                {transformer['name']}
            </div>
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="border-bottom: 1px solid #e5e5e5;">
                    <td style="padding: 4px 8px 4px 0; color: #86868b;">From</td>
                    <td style="padding: 4px 0; font-weight: 500;">{transformer['BusName']} (Bus {transformer['bus0']})</td>
                </tr>
                <tr style="border-bottom: 1px solid #e5e5e5;">
                    <td style="padding: 4px 8px 4px 0; color: #86868b;">To</td>
                    <td style="padding: 4px 0; font-weight: 500;">{transformer['BusName_to']} (Bus {transformer['bus1']})</td>
                </tr>
                <tr style="border-bottom: 1px solid #e5e5e5;">
                    <td style="padding: 4px 8px 4px 0; color: #86868b;">Rating</td>
                    <td style="padding: 4px 0; font-weight: 500;">{transformer['s_nom']:.1f} MVA</td>
                </tr>
                <tr>
                    <td style="padding: 4px 8px 4px 0; color: #86868b;">Impedance</td>
                    <td style="padding: 4px 0; font-weight: 500;">{transformer['x']:.4f} + j{transformer['r']:.4f}</td>
                </tr>
            </table>
        </div>
        """

        marker = folium.RegularPolygonMarker(
            location=[transformer['y'], transformer['x']],
            number_of_sides=3,
            radius=14,  # Much larger for visibility
            color='white',  # White outline
            weight=2,  # Border width
            fill=True,
            fillColor=transformer_color,
            fillOpacity=1.0,  # Full opacity
            popup=folium.Popup(popup_html, max_width=300),
            rotation=0
        )
        marker.add_to(transformers_group)

    # Add to map
    lines_138kv.add_to(m)
    lines_69kv.add_to(m)
    transformers_group.add_to(m)
    midpoints_group.add_to(m)

    # Add minimal, Apple-style controls
    folium.LayerControl(
        position='bottomleft',
        collapsed=False,
        autoZIndex=True
    ).add_to(m)

    plugins.Fullscreen(
        position='topleft',
        title='Fullscreen',
        title_cancel='Exit Fullscreen'
    ).add_to(m)

    # Add custom CSS for Apple Maps styling
    apple_style = """
    <style>
        .leaflet-container {
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Helvetica Neue", Arial, sans-serif;
            background: #f5f5f7;
        }
        .leaflet-control-layers {
            border-radius: 12px;
            border: 1px solid rgba(0, 0, 0, 0.1);
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
        }
        .leaflet-bar {
            border-radius: 12px;
            border: 1px solid rgba(0, 0, 0, 0.1);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        }
        .leaflet-bar a {
            color: #007AFF;
        }
        .leaflet-popup-content-wrapper {
            border-radius: 12px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
        }
    </style>
    """
    m.get_root().html.add_child(folium.Element(apple_style))

    # Save
    m.save(output_file)
    print(f"[OK] Apple Maps-style map saved to: {output_file}")
    print(f"  Open in browser to view!")
    return True

def main():
    parser = argparse.ArgumentParser(
        description='Create Apple Maps-style interactive maps of Hawaii 40 electrical network'
    )
    parser.add_argument(
        '--type',
        choices=['plotly', 'folium', 'both'],
        default='both',
        help='Type of map to create (default: both)'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Output filename (ignored if type=both)'
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Hawaii 40 Network - Apple Maps Style Generator")
    print("=" * 60)

    # Load data
    print("\nLoading transmission line and transformer data...")
    lines_data, transformers_df = load_data()

    print(f"[OK] Loaded {len(lines_data['features'])} transmission lines")
    print(f"[OK] Loaded {len(transformers_df)} transformers")
    print("[OK] Using basemap for city names and parks")

    # Create maps
    success = True
    if args.type in ['plotly', 'both']:
        output = args.output if args.output and args.type == 'plotly' else 'hawaii40_interactive_map.html'
        success = create_plotly_map(lines_data, transformers_df, output) and success

    if args.type in ['folium', 'both']:
        output = args.output if args.output and args.type == 'folium' else 'hawaii40_folium_map.html'
        success = create_folium_map(lines_data, transformers_df, output) and success

    if success:
        print("\n" + "=" * 60)
        print("SUCCESS! Apple Maps-style maps created")
        print("=" * 60)
        print("\nFeatures:")
        print("  [OK] Clean, minimal Apple Maps aesthetic")
        print("  [OK] City names and parks from basemap")
        print("  [OK] Transmission lines and transformers with hover data")
        print("  [OK] Elegant colors and smooth lines")
        print("  [OK] Interactive legend at bottom-left")
        print("\nOpen the HTML file(s) in your browser!")
    else:
        print("\n" + "=" * 60)
        print("FAILED! Check error messages above")
        print("=" * 60)
        return 1

    return 0

if __name__ == '__main__':
    exit(main())
message.txt