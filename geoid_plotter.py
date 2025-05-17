import array
import struct
import math
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
# Assuming these are your own modules, ensure they are also Python 3 compatible
from byn_format import *
from ggf_format import *
from gem_format import *
from gsf_format import *
from gff_format import *
from javad_bin_format import *
import matplotlib.ticker as ticker
from matplotlib.ticker import FuncFormatter
import json
from matplotlib.widgets import RectangleSelector
import csv
import pickle

##
def geoid_plot(file_, canvas, ax, fig, undulations_masked_array, lon_grid, lat_grid):
    def onselect(eclick, erelease):
        """
        Handles the rectangle selection event.
        :param eclick: the click event
        :param erelease: the release event
        """
        # Get the selected rectangle coordinates
        x1, y1 = min(eclick.xdata, erelease.xdata), min(eclick.ydata, erelease.ydata)
        x2, y2 = max(eclick.xdata, erelease.xdata), max(eclick.ydata, erelease.ydata)

        # Find indices corresponding to selected rectangle
        # Using boolean indexing for more direct selection
        # For 2D grids, you typically need to select based on both lat and lon.
        # This assumes lon_grid and lat_grid are 1D arrays corresponding to axes
        # and undulations_masked_array is 2D.
        lon_mask = (lon_grid >= x1) & (lon_grid <= x2)
        lat_mask = (lat_grid >= y1) & (lat_grid <= y2)

        # Get the actual data points within the selected range
        # Note: If lon_grid and lat_grid are 1D and undulations_masked_array is 2D (lat, lon)
        # then slicing needs to be careful with indexing.
        # Assuming lon_grid and lat_grid are 1D arrays of unique values for each axis
        lon_start_idx = np.searchsorted(lon_grid, x1)
        lon_end_idx = np.searchsorted(lon_grid, x2, side='right')
        lat_start_idx = np.searchsorted(lat_grid, y1)
        lat_end_idx = np.searchsorted(lat_grid, y2, side='right')

        # Ensure indices are within bounds
        lon_start_idx = max(0, lon_start_idx)
        lon_end_idx = min(len(lon_grid), lon_end_idx)
        lat_start_idx = max(0, lat_start_idx)
        lat_end_idx = min(len(lat_grid), lat_end_idx)

        # Extract selected subgrid for undulations
        selected_undulations_subgrid = undulations_masked_array[lat_start_idx:lat_end_idx,
                                                                 lon_start_idx:lon_end_idx]

        # Get the corresponding longitude and latitude values for the subgrid
        selected_lon_values = lon_grid[lon_start_idx:lon_end_idx]
        selected_lat_values = lat_grid[lat_start_idx:lat_end_idx]

        # Create a flattened array of (lon, lat, undulation) for CSV export
        selected_coords_for_csv = []
        for i, lat_val in enumerate(selected_lat_values):
            for j, lon_val in enumerate(selected_lon_values):
                undulation_val = selected_undulations_subgrid[i, j]
                selected_coords_for_csv.append([lon_val, lat_val, undulation_val])

        # print statement for debugging (Python 3 compatible)
        print(f"Selected Rectangle: ({x1:.2f}, {y1:.2f}) to ({x2:.2f}, {y2:.2f})")
        print(f"Extracted {len(selected_coords_for_csv)} data points.")


        # Save selected coordinates and undulations to CSV file
        with open('selected_data.csv', 'w', newline='') as f: # `newline=''` to prevent extra blank rows
            writer = csv.writer(f)
            writer.writerow(["Longitude", "Latitude", "Undulation"]) # Changed order to match output
            for row in selected_coords_for_csv:
                writer.writerow(row)

    def update_callback(event):
        """
        Handles the update event.
        :param event: the update event
        """
        if r_selector.active:
            r_selector.update()

    lon_min, lon_max = np.min(lon_grid), np.max(lon_grid)
    lat_min, lat_max = np.min(lat_grid), np.max(lat_grid)

    # Clear previous plot
    ax.clear()

    #fig, ax = plt.subplots(figsize=(10, 6))
    # Determine levels for colorbar
    levels = np.linspace(np.min(undulations_masked_array), np.max(undulations_masked_array), 100)
    ax.grid(True, linestyle='--', linewidth=0.5, color='black')
    contour = ax.contourf(lon_grid, lat_grid, undulations_masked_array, levels=levels, cmap='jet')
    cbar = fig.colorbar(contour, format='%.3f', ticks=np.linspace(np.min(undulations_masked_array), np.max(undulations_masked_array), 15))
    contour_levels = cbar.ax.get_yticks()
    # Add contour lines with specific levels
    contour_levels = np.linspace(np.min(undulations_masked_array), np.max(undulations_masked_array), 15)  # Adjust the number of contour lines as needed
    contour = ax.contour(lon_grid, lat_grid, undulations_masked_array, levels=contour_levels, colors="white")

    # Set the limits of the plot
    ax.set_xlim(lon_min, lon_max)
    ax.set_ylim(lat_min, lat_max)

    r_selector = RectangleSelector(ax, onselect, interactive=True, useblit=True)

    ax.clabel(contour, inline=True, fontsize=8, inline_spacing=10)

    # Handling pickle for Python 3
    # When reading a pickle file written in Python 2, you might need to specify encoding if it contains strings.
    # For numerical data like coordinates, it's usually fine.
    # However, if 'boundary_coordinates.pkl' was created in Python 2,
    # consider recreating it in Python 3, or use `encoding='latin1'` if it fails.
    try:
        with open('boundary_coordinates.pkl', 'rb') as f:
            boundary_coordinates_list = pickle.load(f)
    except UnicodeDecodeError:
        print("Warning: Failed to load pickle file. Trying with 'latin1' encoding.")
        with open('boundary_coordinates.pkl', 'rb') as f:
            # This might be needed if the pickle file was created in Python 2 with string data
            boundary_coordinates_list = pickle.load(f, encoding='latin1')

    for boundary_coordinates in boundary_coordinates_list:
        lon, lat = boundary_coordinates.T
        ax.plot(lon, lat, color='black')

    def format_ticks_with_degrees(x, pos):
        # Using f-string for formatting and Unicode for degree symbol
        return f'{x:.0f}\u00b0'
    # Apply the formatter to both x and y axes
    ax.xaxis.set_major_formatter(FuncFormatter(format_ticks_with_degrees))
    ax.yaxis.set_major_formatter(FuncFormatter(format_ticks_with_degrees))

    fig.canvas.mpl_connect('draw_event', update_callback)

    ax.set_title('Undulations Contour Map')
    ax.set_xlabel('Longitude (Decimal Degrees)')
    ax.set_ylabel('Latitude (Decimal Degrees)')

    canvas.draw()
