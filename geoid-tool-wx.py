import sys
import os
import wx
import wx.lib.newevent
import numpy as np

import matplotlib
matplotlib.use('WXAgg') # Use the WXAgg backend for wxPython
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar

# Import your data/plotting logic
# Ensure these files are in the same directory or accessible via PYTHONPATH
from geoid_plotter import geoid_plot
from make_data import ggf_data

# Define a custom event for redirecting text from other threads (optional, but good practice)
# Although in this simple app, plot computation is on the main thread,
# it's good practice for general text redirection.
(UpdateTextEvent, EVT_UPDATE_TEXT) = wx.lib.newevent.NewEvent()

class ZoomableFigureCanvas(FigureCanvas):
    """
    A custom Matplotlib canvas for wxPython that supports mouse wheel zooming.
    """
    def __init__(self, fig, ax, parent=None):
        super().__init__(fig)
        self.SetParent(parent) # Set parent for wxPython widgets
        self.fig = fig
        self.ax = ax  # Store a reference to the specific Axes object for zooming

        # Bind mouse wheel event
        self.Bind(wx.EVT_MOUSEWHEEL, self.on_mouse_wheel)

    def on_mouse_wheel(self, event):
        """
        Handles mouse wheel events for zooming.
        Zooms in/out centered on the mouse cursor position.
        """
        # Get mouse position in display coordinates relative to the FigureCanvas widget
        x_display, y_display = event.GetX(), event.GetY()

        # Convert mouse display coordinates to data coordinates
        # Check if the mouse is inside the current axes' bounding box
        # ax.contains_point() takes display coordinates
        # Note: contains_point expects figure coordinates, but event.GetX/Y are canvas coordinates.
        # We need to transform canvas coords to figure coords first.
        # However, for simple checks, often people just check if within axes bounds or
        # try/except the transform. Let's simplify and rely on the transform failing if outside.
        try:
            x_data, y_data = self.ax.transData.inverted().transform((x_display, y_display))
        except ValueError:
            # Mouse is likely outside the axes bounds, ignore zoom
            return

        # Ensure no modifier keys (like Ctrl, Alt, Shift) are pressed to prevent conflicts
        if not (event.ControlDown() or event.AltDown() or event.ShiftDown()):
            self._zoom_on_wheel(event, x_data, y_data)
        event.Skip() # Allow other handlers to process the event

    def _zoom_on_wheel(self, event, x_data, y_data):
        """Internal helper to perform the zoom calculation and redraw."""
        cur_xlim = self.ax.get_xlim()
        cur_ylim = self.ax.get_ylim()

        # Determine the zoom factor based on wheel direction
        # event.GetWheelRotation() > 0 means wheel up (zoom in)
        if event.GetWheelRotation() > 0:
            zoom_factor = 0.8  # Zoom in by 20%
        else:
            zoom_factor = 1.2  # Zoom out by 20%

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


class MainFrame(wx.Frame):
    """
    Main application window for the Geoid Reader GUI.
    """
    def __init__(self, parent=None):
        super().__init__(parent, title='Geoid Reader - wxPython')
        self.SetMinSize(wx.Size(800, 600)) # Set a reasonable initial minimum size

        self._create_menu_bar()
        self._create_widgets()

        # Redirect stdout to the console_text widget
        self.console_redirector = TextRedirector(self.console_text)
        sys.stdout = self.console_redirector
        print("Welcome to the Geoid Reader!")
        print("Click 'Compute' to generate a dummy plot.")
        print("Use mouse wheel over the plot to zoom in/out.")

        self.Maximize(True) # Maximize the window on start

    def _create_menu_bar(self):
        """Initializes the application's menu bar."""
        menubar = wx.MenuBar()

        # File Menu
        file_menu = wx.Menu()
        file_menu.Append(wx.ID_NEW, '&New\tCtrl+N', 'Create a new file')
        file_menu.Append(wx.ID_OPEN, '&Open...\tCtrl+O', 'Open an existing file')
        file_menu.Append(wx.ID_SAVE, '&Save\tCtrl+S', 'Save the current file')
        file_menu.Append(wx.ID_SAVEAS, 'Save &As...', 'Save the current file with a new name')
        file_menu.AppendSeparator()
        file_menu.Append(wx.ID_EXIT, '&Exit\tAlt+F4', 'Exit the application')

        menubar.Append(file_menu, '&File')

        # Tools Menu
        tool_menu = wx.Menu()
        tool_menu.Append(wx.ID_ANY, 'Do &Something', 'Perform some action')
        menubar.Append(tool_menu, '&Tools')

        self.SetMenuBar(menubar)

        # Bind menu events
        self.Bind(wx.EVT_MENU, self._on_new, id=wx.ID_NEW)
        self.Bind(wx.EVT_MENU, self._on_open_file, id=wx.ID_OPEN)
        self.Bind(wx.EVT_MENU, self._on_save, id=wx.ID_SAVE)
        self.Bind(wx.EVT_MENU, self._on_save_as, id=wx.ID_SAVEAS)
        self.Bind(wx.EVT_MENU, self.on_exit, id=wx.ID_EXIT) # wx.ID_EXIT triggers close event
        self.Bind(wx.EVT_MENU, self._on_do_something, id=tool_menu.FindItem('Do &Something'))

    def _create_widgets(self):
        """Sets up the main layout and widgets of the application."""
        # Main panel for the frame
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        panel.SetSizer(main_sizer)

        # Main notebook (QTabWidget equivalent)
        self.notebook = wx.Notebook(panel)
        main_sizer.Add(self.notebook, 1, wx.EXPAND | wx.ALL, 5) # Expand and add padding

        # --- "Appearance" Page (main tab) ---
        main_appearance_page = wx.Panel(self.notebook)
        self.notebook.AddPage(main_appearance_page, 'Appearance')
        appearance_sizer = wx.BoxSizer(wx.VERTICAL)
        main_appearance_page.SetSizer(appearance_sizer)

        # Horizontal splitter (QSplitter equivalent)
        pw_hor = wx.SplitterWindow(main_appearance_page, style=wx.SP_LIVE_UPDATE)
        appearance_sizer.Add(pw_hor, 1, wx.EXPAND | wx.ALL, 0) # No padding for splitter itself

        # --- Group 1: Settings (left pane of horizontal splitter) ---
        # wx.StaticBoxSizer is commonly used for a titled group box
        group1_box = wx.StaticBox(pw_hor, label='Settings')
        group1_sizer = wx.StaticBoxSizer(group1_box, wx.VERTICAL)
        pw_hor.SetWindow1(group1_box) # Set the left pane

        # Vertical splitter (QSplitter equivalent within settings)
        pw_vert = wx.SplitterWindow(group1_box, style=wx.SP_LIVE_UPDATE)
        group1_sizer.Add(pw_vert, 1, wx.EXPAND | wx.ALL, 5) # Add padding inside group box

        # ---- Subframe 1: Controls (top pane of vertical splitter) ----
        subfr_1 = wx.Panel(pw_vert)
        subfr1_sizer = wx.GridSizer(0, 2, 5, 5) # rows, cols, vgap, hgap
        subfr_1.SetSizer(subfr1_sizer)

        # Checkboxes
        b1 = wx.CheckBox(subfr_1, label='Show toolbar')
        subfr1_sizer.Add(b1, 0, wx.ALIGN_LEFT | wx.ALL, 5)
        b2 = wx.CheckBox(subfr_1, label='Toolbar tips')
        subfr1_sizer.Add(b2, 0, wx.ALIGN_LEFT | wx.ALL, 5)
        b3 = wx.CheckBox(subfr_1, label='Show toolbar') # Duplicate from original
        subfr1_sizer.Add(b3, 0, wx.ALIGN_LEFT | wx.ALL, 5)
        b4 = wx.CheckBox(subfr_1, label='Toolbar tips') # Duplicate from original
        subfr1_sizer.Add(b4, 0, wx.ALIGN_LEFT | wx.ALL, 5)

        # Plot trigger button
        self.plot_button = wx.Button(subfr_1, label='Compute')
        self.Bind(wx.EVT_BUTTON, self._on_make_plot, self.plot_button)
        subfr1_sizer.Add(self.plot_button, 0, wx.ALIGN_LEFT | wx.ALL, 5)

        # Add a stretchable space to push content to the top
        subfr1_sizer.AddStretchSpacer(1) # Takes up remaining vertical space
        # Or if you want a fixed size spacer: subfr1_sizer.Add( (20,40), 0)

        pw_vert.SetWindow1(subfr_1) # Set the top pane

        # ---- Subframe 2: Console (bottom pane of vertical splitter) ----
        subfr_2 = wx.StaticBox(pw_vert, label="Console")
        subfr2_sizer = wx.StaticBoxSizer(subfr_2, wx.VERTICAL)
        self.console_text = wx.TextCtrl(subfr_2, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2)
        subfr2_sizer.Add(self.console_text, 1, wx.EXPAND | wx.ALL, 5) # Expand and add padding

        pw_vert.SetWindow2(subfr_2) # Set the bottom pane

        # Set initial sizes for the vertical splitter
        pw_vert.SplitVertically(subfr_1, subfr_2, self.GetSize().GetHeight() // 3)


        # --- Group 2: Results (right pane of horizontal splitter) ---
        group2_box = wx.StaticBox(pw_hor, label='Results')
        group2_sizer = wx.StaticBoxSizer(group2_box, wx.VERTICAL)
        pw_hor.SetWindow2(group2_box) # Set the right pane

        self.sub_notebook = wx.Notebook(group2_box)
        group2_sizer.Add(self.sub_notebook, 1, wx.EXPAND | wx.ALL, 5)

        # --- "Geoid Plot" Page (sub-notebook tab) ---
        plot_page_in_subnotebook = wx.Panel(self.sub_notebook)
        self.sub_notebook.AddPage(plot_page_in_subnotebook, 'Geoid Plot')
        plot_layout = wx.BoxSizer(wx.VERTICAL)
        plot_page_in_subnotebook.SetSizer(plot_layout)

        # Matplotlib Figure and Canvas setup
        self.fig = Figure(figsize=(10, 10))
        self.ax = self.fig.add_subplot(111)
        self.ax.grid(True)

        self.canvas = ZoomableFigureCanvas(self.fig, self.ax, plot_page_in_subnotebook)
        plot_layout.Add(self.canvas, 1, wx.EXPAND | wx.ALL, 0)

        # Matplotlib Navigation Toolbar
        self.toolbar = NavigationToolbar(self.canvas) # Parent is typically optional or the frame
        plot_layout.Add(self.toolbar, 0, wx.EXPAND | wx.ALL, 0)

        # --- "Geoid Info" Page (another sub-notebook tab) ---
        page3 = wx.Panel(self.sub_notebook)
        self.sub_notebook.AddPage(page3, 'Geoid Info')

        # --- "Images" Page (main notebook tab) ---
        page5 = wx.Panel(self.notebook)
        self.notebook.AddPage(page5, 'Images')

        # Set initial sizes for the horizontal splitter
        pw_hor.SplitVertically(group1_box, group2_box, self.GetSize().GetWidth() // 3)

        panel.Layout() # Re-layout the panel after all widgets are added

    def _on_make_plot(self, event):
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
            wx.MessageBox(f"Failed to generate plot: {e}", "Plot Error", wx.OK | wx.ICON_ERROR)

    # --- Menu event handlers ---
    def _on_new(self, event):
        print('Action: New')
        wx.MessageBox("This action does nothing.", "Info", wx.OK | wx.ICON_INFORMATION)

    def _on_open_file(self, event):
        """Handles the 'Open' file menu action."""
        with wx.FileDialog(self, "Open File", wildcard="All Files (*.*)|*.*",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as file_dialog:
            if file_dialog.ShowModal() == wx.ID_CANCEL:
                print("File open cancelled.")
                return

            file_path = file_dialog.GetPath()
            print(f"Opening file: {file_path}")
            try:
                with open(file_path, 'r') as f:
                    content = f.read(500) # Read first 500 characters for example
                    self.console_text.AppendText(f"\n--- File Content ({os.path.basename(file_path)}) ---\n")
                    self.console_text.AppendText(content + "\n")
                    self.console_text.AppendText("--------------------------------------\n\n")
            except Exception as e:
                print(f"Could not read file: {e}")
                wx.MessageBox(f"Could not read file: {e}", "File Error", wx.OK | wx.ICON_WARNING)

    def _on_save(self, event):
        print('Action: Save')
        wx.MessageBox("This action does nothing.", "Info", wx.OK | wx.ICON_INFORMATION)

    def _on_save_as(self, event):
        print('Action: Save As')
        wx.MessageBox("This action does nothing.", "Info", wx.OK | wx.ICON_INFORMATION)

    def _on_do_something(self, event):
        print('Action: Do Something')
        wx.MessageBox("This action does nothing.", "Info", wx.OK | wx.ICON_INFORMATION)

    def on_exit(self, event):
        """Handles the 'Exit' menu action."""
        self.Close(True) # Close the frame


class TextRedirector:
    """
    A class to redirect stdout to a wx.TextCtrl widget using wx.PostEvent,
    ensuring thread-safe updates.
    """
    def __init__(self, text_ctrl: wx.TextCtrl):
        self.text_ctrl = text_ctrl
        self.buffer = ''

        # Bind the custom event to the text control
        # The text control itself will handle the event on the GUI thread
        self.text_ctrl.Bind(EVT_UPDATE_TEXT, self._on_update_text)

    def write(self, text: str):
        self.buffer += text
        if '\n' in self.buffer:
            lines = self.buffer.split('\n')
            for line in lines[:-1]:
                # Post event to GUI thread
                evt = UpdateTextEvent(text_content=line + '\n')
                wx.PostEvent(self.text_ctrl, evt)
            self.buffer = lines[-1]

    def flush(self):
        if self.buffer:
            evt = UpdateTextEvent(text_content=self.buffer + '\n')
            wx.PostEvent(self.text_ctrl, evt)
            self.buffer = ''

    def _on_update_text(self, event: UpdateTextEvent):
        """Handler for the custom event, appending text to the TextCtrl."""
        self.text_ctrl.AppendText(event.text_content)


if __name__ == '__main__':
    app = wx.App(False) # False means don't redirect stdout/stderr to a console window
    frame = MainFrame()
    frame.Show(True)
    app.MainLoop()