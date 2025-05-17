import struct
import numpy as np

class GEM:
    def load_gem(self, input_filename):
        with open(input_filename, "rb") as gem_input:
            # Read header
            if len > 0xa2:
                header, magic, fsiz, unk64, unk011 = struct.unpack("<9shIbb", gem_input.read(9 + 2 + 4 + 1 + 1))
                print(header, magic, fsiz, unk64, unk011)
            # Skip section
            gem_input.seek(18 + 53, 1)
            #or 84
            #gem_input.seek(84, 1)

            # Read parameters
            a, f1, miny, minx, maxy, maxx, dx, dy, unk012, ave, ncol, nvals = struct.unpack("<ddddddddbfII", gem_input.read(8 + 8 + 8 + 8 + 8 + 8 + 8 + 8 + 1 + 4 + 4 + 4))

            # Print parameters (for debugging)
            print(a, f1, miny, minx, maxy, maxx, dx, dy, unk012, ave, ncol, nvals)

            # Set boundary and spacing properties
            R2D = 180. / 3.14159265358979323846
            self.boundary_south = miny
            self.boundary_north = maxy
            self.boundary_west = minx
            self.boundary_east = maxx
            self.spacing_ns = dy
            self.spacing_ew = dx
            self.columns = ncol
            self.rows = nvals / ncol

            # Calculate number of rows
            nrow = nvals / ncol

            # Read undulations and store them in a list
            self.geoid_values = []
            for i in range(0, nrow * ncol):
                row = int(i / ncol)
                col = i % (ncol)
                val, = struct.unpack("h", gem_input.read(2))
                if val == 32767: #placeholder
                    self.geoid_values.append(9999.0)
                else:
                    self.geoid_values.append(ave + val / 1000.)
                #print ave + val / 1000.


    def dump_undulations(self):
        # Reshape the list of undulations into a 2D array
        undulations_grid = np.array(self.geoid_values).reshape((self.rows, self.columns))
        undulations = undulations_grid
        return undulations

