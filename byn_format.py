#
# geoid.py
#
# Uses the contents of a Natural Resources Canada GPS-H Grid file (BYN)
# to interpolate geoid separation values for specified geographic
# coordinates (spatial reference system is assumed to be the same as the
# geoid file)
#
# Contact:
#
# Trevor Milne
# Gaiamatics Solutions Inc.
# tmilne@gaiamatics.com
#
# License:
#
# This script has been placed in the public domain without warranty
# Gaiamatics Solutions is not responsible for any application of
# this script or its derivatives.
#

import array, struct, math
import numpy as np

class BYN:

        #
        # reads the contents of the specified BYN file and retains
        # the header information and grid separation values for
        # computations in compute_separation()
        #

        def load_byn(self, input_filename):

                # open the BYN file
                byn_input = file(input_filename, "rb")

                # data extents
                data = byn_input.read(20)
                data = struct.unpack("llllhh", data)

                self.boundary_south = data[0]
                self.boundary_north = data[1]
                self.boundary_west  = data[2]
                self.boundary_east  = data[3]
                self.spacing_ns     = data[4]
                self.spacing_ew     = data[5]

                # data format
                data = byn_input.read(4)
                data = struct.unpack('hh', data)

                self.model_type = data[0]
                self.data_type  = data[1]

                data = byn_input.read(12)
                data = struct.unpack('dhh', data)

                self.factor    = data[0]
                self.data_size = data[1]
                self.std_avail = data[2]

                # format & coordinate system
                data = byn_input.read(16)
                data = struct.unpack('dhhhh', data)

                self.std_factor = data[0]
                self.datum      = data[1]
                self.ellipsoid  = data[2]
                self.byte_order = data[3]
                self.bndy_scale = data[4]

                # remainder of header
                data = byn_input.read(28)

                # verify that data is a geoid model, 32-bit integer & PC byte order
                #if (self.data_type != 1) or (self.data_size != 4) or (self.byte_order != 1):
                 #       raise Exception("Incompatible BYN file.")

                # compute number of rows & columns
                self.columns = int((self.boundary_east - self.boundary_west) / self.spacing_ew + 1)
                self.rows = int((self.boundary_north - self.boundary_south) / self.spacing_ns + 1)

                # create block of long integers (4 byte) and read grid values
                int_values = array.array('l')
                int_values.fromfile(byn_input, self.columns * self.rows)

                # convert grid cells from integers to floating points
                self.geoid_values = array.array('f')

                for value in int_values:

                        # apply scale factor to create 'floating point' values
                        self.geoid_values.append(value / self.factor)

                # close the files
                byn_input.close()

                # deallocate temporary objects
                del int_values

        #
        # extracts the separation value from the specified grid cell
        #

        def __extract_value(self, cell_x, cell_y):

                # check grid bounds
                if (cell_x < 0) or (cell_x > self.columns) or (cell_y < 0) or (cell_y > self.rows):
                        return 0

                # account for Y-axis going "north"
                cell_y = (self.rows - cell_y - 1)

                # compute grid index for specified cell
                offset = cell_y * self.columns + cell_x

                return self.geoid_values[offset]

        #
        # compute a matrix multiplication of two 2D arrays
        #

        def __multiply(self, left, right):

                # retrieve dimensions
                rows = len(left)
                cols = len(right[0])

                # check dimensions
                if (len(left[0]) != len(right)): raise Exception("Cannot be multiplied.")

                # create an empty array for the matrix
                matrix = [[0 for col in range(cols)] for row in range(rows)]

            # multiple the matrices
                for row in range(rows):
                        for col in range(cols):
                                for sum in range(len(left[0])):
                                        matrix[row][col] += left[row][sum] * right[sum][col]

                return matrix

        #
        # computes the geoid separation value for the given Longitude, Latitude
        #
        # quadratic equations derived from:
        #    Computation of a File of Geoidal Heights Using
        #    Molodenskij's Truncation Method. - P. Vanicek et al, 1990
        #

        def dump_undulations(self):
                undulations = []
                for y in range(self.rows):
                    for x in range(self.columns):
                        undulation = self.geoid_values[y * self.columns + x]
                        undulations.append(undulation)
                return undulations

        def dump_undulations(self):
            # Reshape the grid into a 2D array
            undulations_grid = np.array(self.geoid_values).reshape((self.rows, self.columns))
            # Flatten the 2D array to get undulations in a 1D array
            undulations = undulations_grid.flatten()
            return undulations
        

        def compute_separation(self, longitude, latitude):

                # convert longitude & latitude into arcseconds
                point_x = longitude * 3600
                point_y = latitude * 3600

                # shift to in reference to geoid grid boundaries
                point_x = point_x - self.boundary_west
                point_y = point_y - self.boundary_south

                # determine which grid cell the point falls into
                grid_x5 = int(math.floor(point_x / self.spacing_ew))
                grid_y5 = int(math.floor(point_y / self.spacing_ns))

                # extract the neighbourhood
                L = [
                                [self.__extract_value(grid_x5 - 1, grid_y5 + 1)],
                                [self.__extract_value(grid_x5    , grid_y5 + 1)],
                                [self.__extract_value(grid_x5 + 1, grid_y5 + 1)],

                                [self.__extract_value(grid_x5 - 1, grid_y5)],
                                [self.__extract_value(grid_x5    , grid_y5)],
                                [self.__extract_value(grid_x5 + 1, grid_y5)],

                                [self.__extract_value(grid_x5 - 1, grid_y5 - 1)],
                                [self.__extract_value(grid_x5    , grid_y5 - 1)],
                                [self.__extract_value(grid_x5 + 1, grid_y5 - 1)],
                        ]

                # use a pre-computed Ai matrix for the quadratic surface equations
                #
                # values of +/-1 for x1/y1 to x9/t9 used to simplify the computations;
                # the arcseconds coordinates are divided by "spacing" to normalize
                # them into "grid coordinates" (e.g. 1 = cell size)
                #

                Ai = [
                        [ 0.25, -0.5, 0.25, -0.5,  1.0, -0.5,  0.25, -0.5,  0.25],
                        [ 0.25, -0.5, 0.25, -0.0,  0.0, -0.0, -0.25,  0.5, -0.25],
                        [-0.25,  0.0, 0.25,  0.5,  0.0, -0.5, -0.25,  0.0,  0.25],
                        [ 0.0,  -0.0, 0.0,   0.5, -1.0,  0.5,  0.0,   0.0,  0.0 ],
                        [ 0.0,   0.5, 0.0,   0.0, -1.0,  0.0,  0.0,   0.5,  0.0 ],
                        [-0.25, -0.0, 0.25,  0.0,  0.0,  0.0,  0.25,  0.0, -0.25],
                        [ 0.0,   0.0, 0.0,  -0.5,  0.0,  0.5,  0.0,   0.0,  0.0 ],
                        [ 0.0,   0.5, 0.0,   0.0,  0.0,  0.0,  0.0,  -0.5,  0.0 ],
                        [ 0.0,   0.0, 0.0,   0.0,  1.0,  0.0,  0.0,   0.0,  0.0 ]
                        ]

                # compute interpolation coefficients
                X = self.__multiply(Ai, L)

                # convert point location to reference x5,y5 (in grid coordinates)
                x1 = (point_x / self.spacing_ew) - grid_x5
                y1 = (point_y / self.spacing_ns) - grid_y5

                # compute interpolation terms
                A = [[x1**2 * y1**2, x1**2 * y1, x1 * y1**2, x1**2, y1**2, x1 * y1, x1, y1, 1]]

                # interpolate the final geoid separation value
                L = self.__multiply(A, X)

                # return the computed value
                return L[0][0]

