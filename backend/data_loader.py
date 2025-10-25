"""
Data loader for grid data from CSV and GeoJSON files
"""
import pandas as pd
import json
import os

class DataLoader:
    def __init__(self, data_path=None):
        if data_path is None:
            # Default to osu_hackathon data
            base_path = os.path.join(os.path.dirname(__file__), '..', '..', 'osu_hackathon')
            self.data_path = os.path.join(base_path, 'hawaii40_osu')
            self.ieee738_path = os.path.join(base_path, 'ieee738')
        else:
            self.data_path = data_path

        # Load all data
        self.lines_df = None
        self.buses_df = None
        self.flows_df = None
        self.conductors_df = None
        self.lines_geojson = None
        self.buses_geojson = None

        self._load_data()

    def _load_data(self):
        """Load all data files"""
        print(f"Loading data from {self.data_path}")

        # Load CSV files
        csv_path = os.path.join(self.data_path, 'csv')
        self.lines_df = pd.read_csv(os.path.join(csv_path, 'lines.csv'))
        self.buses_df = pd.read_csv(os.path.join(csv_path, 'buses.csv'))
        self.flows_df = pd.read_csv(os.path.join(self.data_path, 'line_flows_nominal.csv'))

        # Strip whitespace from bus names to ensure matching
        if 'bus0_name' in self.lines_df.columns:
            self.lines_df['bus0_name'] = self.lines_df['bus0_name'].astype(str).str.strip()
        if 'bus1_name' in self.lines_df.columns:
            self.lines_df['bus1_name'] = self.lines_df['bus1_name'].astype(str).str.strip()
        if 'BusName' in self.buses_df.columns:
            self.buses_df['BusName'] = self.buses_df['BusName'].astype(str).str.strip()

        # Load conductor library
        self.conductors_df = pd.read_csv(
            os.path.join(self.ieee738_path, 'conductor_library.csv')
        )

        # Load GeoJSON
        gis_path = os.path.join(self.data_path, 'gis')
        with open(os.path.join(gis_path, 'oneline_lines.geojson'), 'r') as f:
            self.lines_geojson = json.load(f)

        try:
            with open(os.path.join(gis_path, 'oneline_busses.geojson'), 'r') as f:
                self.buses_geojson = json.load(f)
        except:
            self.buses_geojson = None

        print(f"Loaded {len(self.lines_df)} lines, {len(self.buses_df)} buses")

    def get_lines_geojson(self):
        """Return lines GeoJSON"""
        return self.lines_geojson

    def get_buses_geojson(self):
        """Return buses GeoJSON"""
        return self.buses_geojson

    def get_line_data(self, line_name):
        """Get line data by name"""
        line = self.lines_df[self.lines_df['name'] == line_name]
        if len(line) == 0:
            return None
        return line.iloc[0].to_dict()

    def get_all_lines(self):
        """Get all lines as list of dictionaries"""
        return self.lines_df.to_dict('records')

    def get_conductor_params(self, conductor_name):
        """Get conductor parameters"""
        conductor = self.conductors_df[
            self.conductors_df['ConductorName'] == conductor_name
        ]
        if len(conductor) == 0:
            return None
        return conductor.iloc[0].to_dict()

    def get_line_flow(self, line_name):
        """Get nominal flow for a line"""
        flow = self.flows_df[self.flows_df['name'] == line_name]
        if len(flow) == 0:
            return 0
        return flow.iloc[0]['p0_nominal']

    def get_bus_voltage(self, bus_name):
        """Get bus voltage in kV"""
        # Bus names are in 'BusName' column, not 'name' column
        bus = self.buses_df[self.buses_df['BusName'] == bus_name]
        if len(bus) == 0:
            return None
        return bus.iloc[0]['v_nom']

    def get_line_info(self, line_name):
        """Get complete line information including flow and conductor data"""
        line_data = self.get_line_data(line_name)
        if line_data is None:
            return None

        conductor_params = self.get_conductor_params(line_data['conductor'])
        flow = self.get_line_flow(line_name)
        voltage = self.get_bus_voltage(line_data['bus0_name'])

        return {
            **line_data,
            'conductor_params': conductor_params,
            'flow_nominal': flow,
            'voltage_kv': voltage
        }
