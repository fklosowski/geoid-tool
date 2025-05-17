import struct
import numpy as np

class BinaryGeoid:
    def __init__(self, filename):
        self.filename = filename
        self.header = None
        self.minx = None
        self.maxy = None
        self.maxx = None
        self.miny = None
        self.dx = None
        self.dy = None
        self.ncol = None
        self.nrow = None
        self.ncol2 = None
        self.nrow2 = None
        self.type_ = None
        self.interp = None
        self.zscale = None
        self.zmin = None
        self.nvals = None
        self.R2D = 180. / 3.14159265358979323846
        # Additional parameters
        self.boundary_south = None
        self.boundary_north = None
        self.boundary_west = None
        self.boundary_east = None
        self.spacing_ns = None
        self.spacing_ew = None
        self.columns = None
        self.rows = None
        self.geoid_values = []

    def load_geoid(self):
        with open(self.filename, 'rb') as bin_input:
            if len > 0xa2:
                self.header = struct.unpack("8s", bin_input.read(8))[0]
                _ = struct.unpack("b", bin_input.read(1))[0]  # magic (unused)
                _ = struct.unpack("57s", bin_input.read(57))[0]  # misc_xx (unused)

                self.minx = struct.unpack("d", bin_input.read(8))[0]
                self.maxy = struct.unpack("d", bin_input.read(8))[0]
                self.maxx = struct.unpack("d", bin_input.read(8))[0]
                self.miny = struct.unpack("d", bin_input.read(8))[0]
                self.dx = struct.unpack("d", bin_input.read(8))[0]
                self.dy = struct.unpack("d", bin_input.read(8))[0]

                self.ncol = struct.unpack("I", bin_input.read(4))[0]
                self.nrow = struct.unpack("I", bin_input.read(4))[0]
                self.unk1 = struct.unpack("I", bin_input.read(4))[0]
                self.unk11 = struct.unpack("I", bin_input.read(4))[0]
                self.ncol2 = struct.unpack("I", bin_input.read(4))[0]
                self.nrow2 = struct.unpack("I", bin_input.read(4))[0]
                self.type_ = struct.unpack("I", bin_input.read(4))[0]
                self.unk3 = struct.unpack("I", bin_input.read(4))[0]
                self.interp = struct.unpack("I", bin_input.read(4))[0]
                _ = struct.unpack("I", bin_input.read(4))[0]  # nul1 (unused)
                _ = struct.unpack("I", bin_input.read(4))[0]  # nul2 (unused)

                self.zscale = struct.unpack("d", bin_input.read(8))[0]
                self.zmin = struct.unpack("d", bin_input.read(8))[0]
                self.nvals = struct.unpack("I", bin_input.read(4))[0]

                # Set additional parameters
                self.boundary_south = self.miny * self.R2D
                self.boundary_north = self.maxy * self.R2D
                self.boundary_west = self.minx * self.R2D
                self.boundary_east = self.maxx * self.R2D
                self.spacing_ns = self.dy
                self.spacing_ew = self.dx
                self.columns = self.ncol
                self.rows = self.nrow

                for i in range(0, self.nrow * self.ncol):
                    row = int(i / self.ncol)
                    col = i % self.ncol
                    if self.type_ == 3:  # int2
                        val = struct.unpack("H", bin_input.read(2))[0]
                        if val == 0 or val == 1:  #zero is placeholder
                            self.geoid_values.append(9999.0)
                        else:
                            self.geoid_values.append(self.zmin + (val - 1) / self.zscale)                        
                    elif self.type_ == 4:  # int4
                        val = struct.unpack("I", bin_input.read(4))[0]
                        self.geoid_values.append(self.zmin + val / self.zscale)
                    elif self.type_ == 5:  # float4
                        val = struct.unpack("f", bin_input.read(4))[0]
                        self.geoid_values.append(self.zmin + val)
                        

    def dump_undulations(self):
        # Reshape the list of undulations into a 2D array
        undulations_grid = np.array(self.geoid_values).reshape((self.nrow, self.ncol))
        return undulations_grid

