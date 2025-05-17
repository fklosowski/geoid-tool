import numpy as np

class GSF:
    def __init__(self, filename):
        self.filename = filename
        self.min_lat = None
        self.min_lon = None
        self.max_lat = None
        self.max_lon = None
        self.columns = None
        self.rows = None
        self.undulations = []

        # Additional parameters
        self.boundary_south = None
        self.boundary_north = None
        self.boundary_west = None
        self.boundary_east = None
        self.spacing_ns = None
        self.spacing_ew = None

    def load_gsf(self):
        with open(self.filename, 'r') as f:
            self.min_lat = float(f.readline())
            self.min_lon = float(f.readline())
            self.max_lat = float(f.readline())
            self.max_lon = float(f.readline())
            self.columns = int(f.readline()) + 1
            self.rows = int(f.readline()) + 1

            # Calculate additional parameters
            self.boundary_south = self.min_lat
            self.boundary_north = self.max_lat
            self.boundary_west = 360.0 - abs(self.min_lon) if self.min_lon < 0 else self.min_lon
            self.boundary_east = 360.0 - abs(self.max_lon) if self.max_lon < 0 else self.max_lon
            self.spacing_ns = (self.max_lat - self.min_lat) / self.rows
            self.spacing_ew = (self.max_lon - self.min_lon) / self.columns

            # Read undulations
            for line in f:
                if line.startswith('N'):
                    self.undulations.append(float(9999.0))
                else:
                    self.undulations.append(float(line.strip()))

    def dump_undulations(self):
        # Reshape the list of undulations into a 2D array
        undulations_grid = np.array(self.undulations).reshape((self.rows, self.columns))
        return undulations_grid

