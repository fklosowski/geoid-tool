import numpy as np
from byn_format import *
from ggf_format import *
from gem_format import *
from gsf_format import *
from javad_bin_format import *



def byn_data():
    # BYN dataset
    geoid = BYN()
    geoid.load_byn('./byn/GUGIK_2011.byn')
    undulations = geoid.dump_undulations()
    # Reshape undulations to 2D array and reverse vertically
    undulations_array = np.array(undulations, dtype=float).reshape((geoid.rows, geoid.columns))[::-1, :]
    #undulations_array = np.flip(undulations_array, axis=1) horizontal flip

    # Mask placeholder values
    undulations_array = np.ma.masked_where((undulations_array == 9999.0) | (undulations_array < -998.5), undulations_array)
    masked_values = np.isnan(undulations_array)

    # If there are masked values, create a masked array
    if np.any(masked_values):
        undulations_array_masked = np.ma.masked_array(undulations_array, mask=masked_values)
    else:
        undulations_array_masked = undulations_array
    # Calculate longitude and latitude grid in decimal degrees for BYN
    lon_grid = np.linspace(geoid.boundary_west / 3600, geoid.boundary_east / 3600, geoid.columns)
    lat_grid = np.linspace(geoid.boundary_south / 3600, geoid.boundary_north / 3600, geoid.rows)
    return (undulations_array_masked, lon_grid, lat_grid)

def ggf_data():
    # GGF dataset
    geoid = GGF('Italy90.GGF', strict=False)
    undulations = geoid.dump_undulations()
    undulations_array = np.array(undulations, dtype=float).reshape((geoid.rows, geoid.columns))[::-1, :]
    masked_values = np.isnan(undulations_array)
    if np.any(masked_values):
        undulations_array_masked = np.ma.masked_array(undulations_array, mask=masked_values)
    else:
        undulations_array_masked = undulations_array
    
    lon_grid = np.linspace(geoid.boundary_west, geoid.boundary_east, geoid.columns)
    lat_grid = np.linspace(geoid.boundary_south, geoid.boundary_north, geoid.rows)
    lon_grid = (lon_grid + 180) % 360 - 180

    return (undulations_array_masked, lon_grid, lat_grid)

def gem_data():
    # GEM dataset
    geoid = GEM()
    geoid.load_gem('.\gem\SWEN17_RH2000.gem')
    undulations = geoid.dump_undulations()
    undulations_array_masked = np.ma.masked_where((undulations == 9999.0), undulations)

    lon_grid = np.linspace(geoid.boundary_west, geoid.boundary_east, geoid.columns)
    lat_grid = np.linspace(geoid.boundary_south, geoid.boundary_north, geoid.rows)
    return (undulations_array_masked, lon_grid, lat_grid)

def gsf_data():
    # GSF dataset
    geoid = GSF(".\gsf\EVRF2007.gsf")
    geoid.load_gsf()
    undulations = geoid.dump_undulations()
    undulations_array_masked = np.ma.masked_where((undulations == 9999.0), undulations)
    lon_grid = np.linspace(geoid.boundary_west, geoid.boundary_east, geoid.columns)
    lat_grid = np.linspace(geoid.boundary_south, geoid.boundary_north, geoid.rows)
    return (undulations_array_masked, lon_grid, lat_grid)

def javad_bin_data():
    # Javad BIN dataset
    geoid = BinaryGeoid('.\javad\geoidpol2008cn_dla_cgeo.bin')
    geoid.load_geoid()
    undulations = geoid.dump_undulations()
    undulations = np.array(undulations, dtype=float).reshape((geoid.rows, geoid.columns))[::-1, :]
    undulations_array_masked = np.ma.masked_where((undulations == 9999.0), undulations)
    lon_grid = np.linspace(geoid.boundary_west, geoid.boundary_east, geoid.columns)
    lat_grid = np.linspace(geoid.boundary_south, geoid.boundary_north, geoid.rows)
    return (undulations_array_masked, lon_grid, lat_grid)

#undulations_array_masked, lon_grid, lat_grid = ggf_data()
