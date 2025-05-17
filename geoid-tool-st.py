import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import os
import sys
import csv
import pickle
from matplotlib.ticker import FuncFormatter
import matplotlib.ticker as ticker # This was already in your plotter

import geoid_plotter
from geoid_plotter import *
from make_data import *

# --- Streamlit Application ---

def main_app():
    """
    Main Streamlit application logic.
    """
    st.set_page_config(
        page_title="Geoid Reader - Streamlit",
        layout="wide", # Use wide layout to give more space for plots
        initial_sidebar_state="expanded"
    )

    st.title('Geoid Reader - Streamlit')

    # --- Session State Initialization ---
    if 'console_output' not in st.session_state:
        st.session_state.console_output = "Welcome to the Geoid Reader!\n" \
                                          "Click 'Compute' to generate a dummy plot.\n"
    if 'plot_generated' not in st.session_state:
        st.session_state.plot_generated = False
    if 'geoid_data' not in st.session_state:
        st.session_state.geoid_data = None
    if 'boundary_coordinates_list' not in st.session_state:
        st.session_state.boundary_coordinates_list = []
        # Load boundary coordinates once at app start
        try:
            # Assumes 'boundary_coordinates.pkl' is in the same directory as the app.py
            with open('boundary_coordinates.pkl', 'rb') as f:
                st.session_state.boundary_coordinates_list = pickle.load(f)
            st.session_state.console_output += "Boundary coordinates loaded from boundary_coordinates.pkl.\n"
        except FileNotFoundError:
            st.session_state.console_output += "Warning: 'boundary_coordinates.pkl' not found. Boundary lines will not be plotted.\n"
        except pickle.UnpicklingError as e:
            st.session_state.console_output += f"Error unpickling 'boundary_coordinates.pkl': {e}. Trying with 'latin1' encoding.\n"
            try:
                with open('boundary_coordinates.pkl', 'rb') as f:
                    st.session_state.boundary_coordinates_list = pickle.load(f, encoding='latin1')
                st.session_state.console_output += "Boundary coordinates loaded successfully with 'latin1' encoding.\n"
            except Exception as e_latin1:
                st.session_state.console_output += f"Failed to load boundary_coordinates.pkl even with 'latin1' encoding: {e_latin1}\n"
                st.warning("Could not load boundary_coordinates.pkl. Boundary lines won't be plotted.")
        except Exception as e:
            st.session_state.console_output += f"An unexpected error occurred loading boundary_coordinates.pkl: {e}\n"
            st.warning("Could not load boundary_coordinates.pkl. Boundary lines won't be plotted.")


    # --- Layout Mimicking PyQt5 ---

    # Main Tab Widget (Appearance, Images)
    main_tabs = st.tabs(['Appearance', 'Images'])

    with main_tabs[0]: # "Appearance" Tab
        # Horizontal Splitter (Settings on left, Results on right)
        col1, col2 = st.columns([1, 2]) # Ratio 1:2 to give more space to results/plot

        with col1: # Left Pane: Settings
            st.header("Settings") # Replaces QGroupBox title

            with st.container():
                st.subheader("Controls")

                # Checkboxes - Streamlit equivalent
                st.checkbox('Show toolbar', key='show_toolbar', value=True)
                st.checkbox('Toolbar tips', key='toolbar_tips', value=True)
                st.checkbox('Show toolbar (duplicate)', key='show_toolbar_dup', value=False)
                st.checkbox('Toolbar tips (duplicate)', key='toolbar_tips_dup', value=False)

                # Plot trigger button
                if st.button('Compute'):
                    st.session_state.console_output += "Compute button clicked!\n"
                    try:
                        # Assuming ggf_data() is the function from your make_data.py
                        # It should return undulations_array_masked, lon_grid, lat_grid
                        undulations_array_masked, lon_grid, lat_grid = ggf_data()
                        st.session_state.geoid_data = (undulations_array_masked, lon_grid, lat_grid)
                        st.session_state.plot_generated = True
                        st.session_state.console_output += "Dummy GGF data generated successfully.\n"
                    except Exception as e:
                        st.session_state.console_output += f"Error generating dummy data: {e}\n"
                        st.error(f"Failed to generate data: {e}")

            # Console (bottom pane)
            with st.expander("Console", expanded=True):
                st.text_area("Console Output", st.session_state.console_output, height=250, disabled=True, key="console_text_area")


        with col2: # Right Pane: Results
            st.header("Results")

            # Sub-notebook Tabs (Geoid Plot, Geoid Info)
            sub_tabs = st.tabs(['Geoid Plot', 'Geoid Info'])

            with sub_tabs[0]: # "Geoid Plot" Tab
                st.subheader("Geoid Plot")
                if st.session_state.plot_generated and st.session_state.geoid_data:
                    try:
                        undulations_array_masked, lon_grid, lat_grid = st.session_state.geoid_data

                        # --- Start of your geoid_plot function logic ---
                        # In Streamlit, we create a new figure for each plot display
                        fig, ax = plt.subplots(figsize=(10, 8))

                        lon_min, lon_max = np.min(lon_grid), np.max(lon_grid)
                        lat_min, lat_max = np.min(lat_grid), np.max(lat_grid)

                        # Determine levels for colorbar
                        levels = np.linspace(np.min(undulations_array_masked), np.max(undulations_array_masked), 100)
                        ax.grid(True, linestyle='--', linewidth=0.5, color='black')

                        # Use pcolormesh for continuous color mapping, contourf for filled contours
                        # contourf can handle 1D lon_grid/lat_grid if undulations_masked_array is 2D
                        contour = ax.contourf(lon_grid, lat_grid, undulations_array_masked, levels=levels, cmap='jet')
                        cbar = fig.colorbar(contour, format='%.3f', ticks=np.linspace(np.min(undulations_array_masked), np.max(undulations_array_masked), 15))
                        # contour_levels = cbar.ax.get_yticks() # Not strictly needed here, but shows how to get ticks
                        
                        # Add contour lines with specific levels
                        contour_levels_lines = np.linspace(np.min(undulations_array_masked), np.max(undulations_array_masked), 15)
                        contour_lines = ax.contour(lon_grid, lat_grid, undulations_array_masked, levels=contour_levels_lines, colors="white")
                        ax.clabel(contour_lines, inline=True, fontsize=8, inline_spacing=10)


                        # Set the limits of the plot
                        ax.set_xlim(lon_min, lon_max)
                        ax.set_ylim(lat_min, lat_max)

                        # RectangleSelector is removed as it's not compatible with Streamlit's st.pyplot()
                        # The onselect and update_callback functions are also removed.

                        # Plot boundary coordinates
                        if st.session_state.boundary_coordinates_list:
                            for boundary_coordinates in st.session_state.boundary_coordinates_list:
                                lon_b, lat_b = boundary_coordinates.T
                                ax.plot(lon_b, lat_b, color='black')
                        else:
                            st.session_state.console_output += "No boundary coordinates to plot.\n"


                        def format_ticks_with_degrees(x, pos):
                            return f'{x:.0f}\u00b0'
                        ax.xaxis.set_major_formatter(FuncFormatter(format_ticks_with_degrees))
                        ax.yaxis.set_major_formatter(FuncFormatter(format_ticks_with_degrees))

                        # fig.canvas.mpl_connect('draw_event', update_callback) # Removed

                        ax.set_title('Undulations Contour Map')
                        ax.set_xlabel('Longitude (Decimal Degrees)')
                        ax.set_ylabel('Latitude (Decimal Degrees)')

                        st.pyplot(fig) # Display the matplotlib figure in Streamlit
                        st.session_state.console_output += "Plot displayed successfully.\n"

                        # --- End of your geoid_plot function logic ---

                    except Exception as e:
                        st.session_state.console_output += f"Error making plot: {e}\n"
                        st.error(f"Failed to generate plot: {e}")
                else:
                    st.info("Click 'Compute' to generate the geoid plot.")

            with sub_tabs[1]: # "Geoid Info" Tab
                st.subheader("Geoid Information")
                st.write("Information about the geoid will appear here.")
                if st.session_state.geoid_data:
                    undulations_array_masked, lon_grid, lat_grid = st.session_state.geoid_data
                    st.write(f"Grid dimensions: {undulations_array_masked.shape}")
                    st.write(f"Min undulation: {np.nanmin(undulations_array_masked):.4f} m")
                    st.write(f"Max undulation: {np.nanmax(undulations_array_masked):.4f} m")
                else:
                    st.info("No geoid data loaded yet.")

    with main_tabs[1]: # "Images" Tab
        st.subheader("Images")
        st.write("This tab could display images related to the geoid data.")

    # --- Menu Bar Actions (re-imagined for Streamlit) ---
    st.sidebar.title("App Actions")

    # Open File (QFileDialog equivalent)
    uploaded_file = st.sidebar.file_uploader("Open File", type=["txt", "ggf", "dat", "byn", "gem", "gsf", "gff", "bin"])
    if uploaded_file is not None:
        file_details = {"FileName": uploaded_file.name, "FileType": uploaded_file.type, "FileSize": uploaded_file.size}
        st.session_state.console_output += f"Uploaded file: {file_details['FileName']} ({file_details['FileSize']} bytes)\n"

        # You would add logic here to parse the uploaded file based on its type
        # For a GGF file, you would use your GGF class:
        # if file_details['FileType'] == 'ggf':
        #     ggf_parser = GGF(uploaded_file.name, strict=True) # You need to save the BytesIO to a temp file or adapt GGF to read BytesIO
        #     if ggf_parser.valid:
        #         st.session_state.geoid_data = (ggf_parser.Grid, ggf_parser.LongGrid, ggf_parser.LatGrid) # Assuming these properties exist
        #         st.session_state.plot_generated = True
        #         st.session_state.console_output += "GGF file parsed and data loaded.\n"
        #     else:
        #         st.session_state.console_output += f"Error parsing GGF: {ggf_parser.errorString}\n"
        #         st.error(f"Error parsing GGF file: {ggf_parser.errorString}")
        # For simplicity, this example just previews text.
        try:
            # For general text preview, decode bytes to string
            content = uploaded_file.getvalue().decode('utf-8', errors='ignore')
            preview_content = content[:500] # Read first 500 chars for preview
            st.session_state.console_output += f"\n--- File Content Preview ({uploaded_file.name}) ---\n"
            st.session_state.console_output += preview_content
            st.session_state.console_output += "\n--------------------------------------\n"
        except Exception as e:
            st.session_state.console_output += f"Could not read/decode uploaded file: {e}\n"
            st.error(f"Could not read uploaded file: {e}")

    # Other placeholder actions
    if st.sidebar.button('New'):
        st.session_state.console_output += "Action: New (placeholder)\n"
        st.info("This action does nothing (placeholder).")

    if st.sidebar.button('Save'):
        st.session_state.console_output += "Action: Save (placeholder)\n"
        st.info("This action does nothing (placeholder).")

    if st.sidebar.button('Do Something'):
        st.session_state.console_output += "Action: Do Something (placeholder)\n"
        st.info("This action does nothing (placeholder).")


if __name__ == '__main__':
    main_app()