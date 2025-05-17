import struct
import numpy as np

class GFF:
    def __init__(self, filename):
        self.filename = filename
        self.R2D = 180. / 3.14159265358979323846
        self.minLat = None
        self.minLon = None
        self.maxLat = None
        self.maxLon = None
        self.latStep = None
        self.lonStep = None
        self.dLat = None
        self.dLon = None
        self.ncols = None
        self.nrows = None
        self.boundary_south = None
        self.boundary_north = None
        self.boundary_west = None
        self.boundary_east = None
        self.spacing_ns = None
        self.spacing_ew = None
        self.columns = None
        self.rows = None
        self.geoid_values = []
        self.lons = []
        self.lats = []

    def load_gff(self):
        with open(self.filename, 'rb') as file_:
            content = file_.read()

            vRegion = content.find('vRegion')
            if vRegion != -1:
                file_.seek(vRegion + len('vRegion')+13)
                data = file_.read(48)
                val = struct.unpack('<dddddd', data)
                self.minLat = val[0]*self.R2D
                self.latStep = val[1]*self.R2D
                self.minLon = val[2]*self.R2D
                self.lonStep = val[3]*self.R2D
                self.dLat = val[4]*self.R2D
                self.dLon = val[5]*self.R2D
                self.maxLat = val[0]*self.R2D + self.latStep
                self.maxLon = val[2]*self.R2D + self.lonStep
                print(self.minLat, self.minLon, self.maxLat, self.maxLon, self.dLat, self.dLon)

            index = content.find('vNY')
            if index != -1:
                file_.seek(index + len('vNY')+13)
                data = struct.unpack("L", file_.read(4))
                self.ncols = data[0]

            index = content.find('vNX')
            if index != -1:
                file_.seek(index + len('vNX')+13)
                data = struct.unpack("L", file_.read(4))
                self.nrows = data[0]

            self.boundary_south = self.minLat
            self.boundary_north = self.maxLat
            self.boundary_west = self.minLon
            self.boundary_east = self.maxLon
            self.spacing_ns = self.dLat
            self.spacing_ew = self.dLon
            self.columns = self.ncols
            self.rows = self.nrows

            vData = content.find('vData')
            if vData != -1:
                file_.seek(vData + len('vData')+17)
                for i in range(0, self.nrows * self.ncols):
                    row = int(i / self.ncols)
                    col = i % (self.ncols)
                    data = file_.read(4)
                    val = struct.unpack('<f', data)[0]
                    #print "%.9f %.9f %13.6f" % ((self.minLat + col * self.dLat), (self.minLon + row  * self.dLon), val)
                    self.lons.append(self.minLon + col  * self.dLon)
                    self.lats.append(self.minLat + row  * self.dLat)
                    if val == 0. or val == 9.99999000e+05 or val < 0 or val == 1 or val == 0.0010000000475:
                        self.geoid_values.append(9999.0)
                    else:
                        self.geoid_values.append(val)

    def dump_undulations(self, order='left_top_by_columns'):
        if order == 'left_bottom_by_rows':
            undulations_grid = np.array(self.geoid_values).reshape((self.ncols, self.nrows)).T
            lon_grid = np.linspace(self.boundary_west, self.boundary_east, self.ncols)
            lat_grid = np.linspace(self.boundary_south, self.boundary_north, self.nrows)
        elif order == 'left_top_by_rows':
            undulations_grid = np.array(self.geoid_values).reshape((self.ncols, self.nrows))
            lon_grid = np.linspace(self.boundary_west, self.boundary_east, self.nrows)
            lat_grid = np.linspace(self.boundary_south, self.boundary_north, self.ncols)
        elif order == 'left_bottom_by_columns':
            undulations_grid = np.array(self.geoid_values).reshape((self.nrows, self.ncols))
            lon_grid = np.linspace(self.boundary_west, self.boundary_east, self.ncols)
            lat_grid = np.linspace(self.boundary_south, self.boundary_north, self.nrows)
        elif order == 'left_top_by_columns':
            undulations_grid = np.array(self.geoid_values).reshape((self.nrows, self.ncols)).T
            #lon_grid = np.linspace(self.boundary_west, self.boundary_east, self.nrows)
            lat_grid = np.linspace(self.boundary_south, self.boundary_north, self.ncols)
            lon_grid = np.array(self.lons)[:self.nrows]
            lon_grid = np.reshape(lon_grid, (self.nrows,))

            print(lon_grid)

            # Take the first 480 elements and reshape
            #lat_grid = np.array(self.lats)[:self.ncols]
            #lat_grid = np.reshape(lat_grid, (self.ncols,))
            #print lat_grid

            

            #numpy.flip() if you need to reverse the order along other axes
            #numpy.fliplr() to flip the array horizontally.

        #germany working
        #undulations_grid = np.array(self.geoid_values).reshape((self.ncols, self.nrows))
        #undulations_grid = np.flipud(undulations_grid)

        #undulations_grid = np.flipud(undulations_grid)
        #self.geoid_values.reverse()
        # Reshape the list of undulations into a 2D array
        
        #undulations_grid_reversed = undulations_grid[:, ::-1]
        # Transpose the array to swap rows and columns
        #undulations_grid = undulations_grid.T        
        
        # Reverse the rows to move undulations counterclockwise
        #undulations_grid = np.flip(undulations_grid, axis=0)# needed for germany
        #undulations_grid[:, ::-1] = undulations_grid[:, ::-1]
        
        #undulations_grid = np.flipud(undulations_grid)
        #undulations_grid.flatten()[::-1].reshape(undulations_grid.shape)
        #undulations_grid[:, ::-1] [::-1, :]
        
        return undulations_grid, lon_grid, lat_grid
