import sys
import os
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QGroupBox, QCheckBox, QPushButton, QTabWidget,
    QTextEdit, QFileDialog, QMenuBar, QMenu, QMessageBox, QGridLayout,
    QSpacerItem, QSizePolicy
)
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

import numpy as np # Used for dummy data generation
import inspect # Retained from original code, but not directly used in the GUI logic

#own modules
from collections import OrderedDict
import geoid_plotter
from geoid_plotter import *
import inspect
from make_data import *


class ZoomableFigureCanvas(FigureCanvas):
    """
    A custom Matplotlib canvas for PyQt5 that supports mouse wheel zooming.
    """
    def __init__(self, fig, ax, parent=None):
        super().__init__(fig)
        self.setParent(parent)
        self.fig = fig
        self.ax = ax  # Store a reference to the specific Axes object for zooming

    def wheelEvent(self, event):
        """
        Handles mouse wheel events for zooming.
        Zooms in/out centered on the mouse cursor position.
        """
        # Get mouse position in display coordinates relative to the FigureCanvas widget
        x_display, y_display = event.pos().x(), event.pos().y()

        # Check if the mouse is inside the current axes' bounding box
        # ax.contains_point() takes display coordinates
        if not self.ax.contains_point((x_display, y_display)):
             # Only zoom if the mouse cursor is over the axes
             return

        # Ensure no modifier keys (like Ctrl, Alt, Shift) are pressed to prevent conflicts
        # with other default behaviors (e.g., scrolling in a list/table if one was there)
        if event.modifiers() == QtCore.Qt.NoModifier:
            self._zoom_on_wheel(event, x_display, y_display)
        # You can add elif conditions here for other modifier keys
        # For example: elif event.modifiers() == QtCore.Qt.ControlModifier: ...

    def _zoom_on_wheel(self, event, x_display, y_display):
        """Internal helper to perform the zoom calculation and redraw."""
        cur_xlim = self.ax.get_xlim()
        cur_ylim = self.ax.get_ylim()

        # Convert mouse display coordinates to data coordinates
        # Use transform.inverted() to go from display to data
        x_data, y_data = self.ax.transData.inverted().transform((x_display, y_display))

        # Determine the zoom factor based on wheel direction
        # event.angleDelta().y() > 0 means wheel up (zoom in)
        if event.angleDelta().y() > 0:
            zoom_factor = 0.8  # Zoom in by 20% (limits become 80% of original range)
        else:
            zoom_factor = 1.2  # Zoom out by 20% (limits become 120% of original range)

        # Calculate new x limits, centered around x_data
        new_xlim_left = x_data - (x_data - cur_xlim[0]) * zoom_factor
        new_xlim_right = x_data + (cur_xlim[1] - x_data) * zoom_factor

        # Calculate new y limits, centered around y_data
        new_ylim_bottom = y_data - (y_data - cur_ylim[0]) * zoom_factor
        new_ylim_top = y_data + (cur_ylim[1] - y_data) * zoom_factor

        # Apply new limits to the axes
        self.ax.set_xlim([new_xlim_left, new_xlim_right])
        self.ax.set_ylim([new_ylim_bottom, new_ylim_top])

        # Redraw the canvas to show the updated plot
        self.draw()


class MainWindow(QMainWindow):
    """
    Main application window for the Geoid Reader GUI.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Geoid Reader - PyQt5')
        self.setMinimumSize(800, 600) # Set a reasonable initial minimum size

        self._createMenuBar()
        self._createCentralWidget()

        # Redirect stdout to the console_text widget
        self.console_redirector = TextRedirector(self.console_text)
        sys.stdout = self.console_redirector
        print("Welcome to the Geoid Reader!")
        print("Click 'Compute' to generate a dummy plot.")
        print("Use mouse wheel over the plot to zoom in/out.")

    def _createMenuBar(self):
        """Initializes the application's menu bar."""
        self.menubar = self.menuBar() # QMainWindow has its own menuBar()

        # File Menu
        fileMenu = self.menubar.addMenu('&File')
        fileMenu.addAction('&New', self._donothing)
        fileMenu.addAction('&Open', self._openFile)
        fileMenu.addAction('&Save', self._donothing)
        fileMenu.addAction('Save &As...', self._donothing)
        fileMenu.addSeparator()
        fileMenu.addAction('&Exit', self.close) # Connects to QMainWindow's close method

        # Tools Menu
        toolMenu = self.menubar.addMenu('&Tools')
        toolMenu.addAction('Do &Something', self._donothing)

    def _createCentralWidget(self):
        """Sets up the main layout and widgets of the application."""
        # Main container widget for the QMainWindow
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout for the central widget (vertical, containing the main QTabWidget)
        main_layout = QVBoxLayout(central_widget)

        # Corresponds to Pmw.NoteBook(self.parent) -> QTabWidget
        self.notebook = QTabWidget()
        main_layout.addWidget(self.notebook)

        # --- "Appearance" Page (main tab) ---
        self.main_appearance_page = QWidget()
        self.notebook.addTab(self.main_appearance_page, 'Appearance')

        # Layout for the main_appearance_page (contains the horizontal splitter)
        appearance_layout = QVBoxLayout(self.main_appearance_page)

        # Corresponds to PanedWindow(self.page1, orient=tk.HORIZONTAL) -> QSplitter
        pw_hor = QSplitter(QtCore.Qt.Horizontal)
        appearance_layout.addWidget(pw_hor)

        # --- Group 1: Settings (left pane of horizontal splitter) ---
        # Corresponds to Pmw.Group(self.page1, tag_text = 'Settings') -> QGroupBox
        self.group1 = QGroupBox('Settings')
        pw_hor.addWidget(self.group1)

        # Layout for the contents of group1
        group1_layout = QVBoxLayout(self.group1)
        self.mainframe = QWidget() # General container widget
        group1_layout.addWidget(self.mainframe)

        # Corresponds to PanedWindow(self.mainframe, orient=tk.VERTICAL) -> QSplitter
        pw_vert = QSplitter(QtCore.Qt.Vertical)
        mainframe_layout = QVBoxLayout(self.mainframe) # Layout for mainframe
        mainframe_layout.addWidget(pw_vert)

        # ---- Subframe 1: Controls (top pane of vertical splitter) ----
        self.subfr_1 = QWidget()
        pw_vert.addWidget(self.subfr_1)

        subfr1_layout = QGridLayout(self.subfr_1) # Using QGridLayout for checkbuttons

        # Checkboxes (retained from original, even duplicates)
        b1 = QCheckBox('Show toolbar')
        subfr1_layout.addWidget(b1, 0, 0, QtCore.Qt.AlignLeft)
        b2 = QCheckBox('Toolbar tips')
        subfr1_layout.addWidget(b2, 0, 1, QtCore.Qt.AlignLeft)
        b3 = QCheckBox('Show toolbar')
        subfr1_layout.addWidget(b3, 1, 0, QtCore.Qt.AlignLeft)
        b4 = QCheckBox('Toolbar tips')
        subfr1_layout.addWidget(b4, 1, 1, QtCore.Qt.AlignLeft)

        # Plot trigger button
        self.plotbutton = QPushButton('Compute')
        self.plotbutton.clicked.connect(self._make_plot)
        subfr1_layout.addWidget(self.plotbutton, 3, 0, QtCore.Qt.AlignLeft)

        # Add a vertical spacer to push content to the top
        subfr1_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding), 4, 0, 1, 2)


        # ---- Subframe 2: Console (bottom pane of vertical splitter) ----
        self.subfr_2 = QGroupBox("Console") # QGroupBox provides the titled frame
        pw_vert.addWidget(self.subfr_2)

        subfr2_layout = QVBoxLayout(self.subfr_2)
        self.console_text = QTextEdit()
        self.console_text.setReadOnly(True) # Make it read-only for console output
        subfr2_layout.addWidget(self.console_text)


        # --- Group 2: Results (right pane of horizontal splitter) ---
        self.group2 = QGroupBox('Results')
        pw_hor.addWidget(self.group2)

        group2_layout = QVBoxLayout(self.group2)

        self.nnotebook = QTabWidget()
        group2_layout.addWidget(self.nnotebook)

        # --- "Geoid Plot" Page (sub-notebook tab) ---
        self.plot_page_in_subnotebook = QWidget()
        self.nnotebook.addTab(self.plot_page_in_subnotebook, 'Geoid Plot')

        plot_layout = QVBoxLayout(self.plot_page_in_subnotebook)

        # Matplotlib Figure and Canvas setup
        # Initialize self.fig and self.ax here once for consistent reference
        self.fig = Figure(figsize=(10, 10))
        self.ax = self.fig.add_subplot(111) # This ensures self.ax is consistently the same object
        self.ax.grid(True)

        # Use the custom ZoomableFigureCanvas here, passing the specific Axes object
        self.canvas = ZoomableFigureCanvas(self.fig, self.ax, self.plot_page_in_subnotebook)
        plot_layout.addWidget(self.canvas)

        # Matplotlib Navigation Toolbar
        self.toolbar = NavigationToolbar(self.canvas, self.plot_page_in_subnotebook)
        plot_layout.addWidget(self.toolbar)


        # --- "Geoid Info" Page (another sub-notebook tab) ---
        self.page3 = QWidget()
        self.nnotebook.addTab(self.page3, 'Geoid Info')

        # --- "Images" Page (main notebook tab) ---
        self.page5 = QWidget()
        self.notebook.addTab(self.page5, 'Images')

        # Set initial splitter sizes (optional, but helps with balanced initial view)
        pw_hor.setSizes([self.width() // 3, 2 * self.width() // 3])
        pw_vert.setSizes([self.height() // 3, 2 * self.height() // 3])

    def _make_plot(self):
        """
        Handles the 'Compute' button click to generate/update the plot.
        This method now clears the existing axes and redraws, instead of adding new ones.
        """
        print("Compute button clicked!")
        try:
            undulations_array_masked, lon_grid, lat_grid = ggf_data()
            self.ax.clear() # Clear the existing axes content
            self.ax.grid(True) # Re-add grid if desired, as clearing might remove it
            geoid_plot('Geoid Undulations', self.canvas, self.ax, self.fig,
                       undulations_array_masked, lon_grid, lat_grid)
            print("Plot updated successfully.")
        except Exception as e:
            print(f"Error making plot: {e}")
            QMessageBox.critical(self, "Plot Error", f"Failed to generate plot: {e}")
    def _donothing(self):
        """Placeholder function for menu actions."""
        print('Action: Nothing')
        QMessageBox.information(self, "Info", "This action does nothing.")

    def _openFile(self):
        """Handles the 'Open' file menu action."""
        filePath, _ = QFileDialog.getOpenFileName(self,
                                                  "Open File",
                                                  "", # Default directory (current working dir)
                                                  "All Files (*.*);;Text Documents (*.txt)")
        if filePath:
            print(f"Opening file: {filePath}")
            try:
                with open(filePath, 'r') as f:
                    content = f.read(500) # Read first 500 characters for example
                    self.console_text.append(f"\n--- File Content ({os.path.basename(filePath)}) ---")
                    self.console_text.append(content)
                    self.console_text.append("--------------------------------------\n")
            except Exception as e:
                print(f"Could not read file: {e}")
                QMessageBox.warning(self, "File Error", f"Could not read file: {e}")
        else:
            print("File open cancelled.")

class TextRedirector(QtCore.QObject):
    """
    A class to redirect stdout to a QTextEdit widget using PyQt signals,
    ensuring thread-safe updates.
    """
    append_text = QtCore.pyqtSignal(str)

    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget
        self.append_text.connect(self.text_widget.append)

    def write(self, text):
        self.append_text.emit(text)

    def flush(self):
        pass

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.showMaximized()
    sys.exit(app.exec_())
