import tkinter
import Pmw
from tkinter import *
import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import *

from matplotlib.figure import Figure
import csv
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
from matplotlib.ticker import MultipleLocator
import matplotlib as mpl
mpl.use('TkAgg')
import math
#own modules
from collections import OrderedDict
import geoid_plotter
from geoid_plotter import *
import inspect
from make_data import *

class MainWindow:
    def __init__(self, parent):

        self.parent = parent

        self.menubar = MenuBar(self.parent)
        self.parent.config(menu=self.menubar)

        # Create and pack the NoteBook.
        self.notebook = Pmw.NoteBook(self.parent)
        self.notebook.pack(fill = 'both', expand = 1, padx = 10, pady = 10)

        # Add the "Appearance" page to the notebook.
        self.main_appearance_page = self.notebook.add('Appearance') # Renamed for clarity to avoid confusion with plot page

        pw_hor = PanedWindow(self.main_appearance_page, orient=tk.HORIZONTAL)
        pw_hor.configure(sashrelief = GROOVE, sashpad=10, opaqueresize=False, showhandle=True)
        pw_hor.pack(fill=BOTH, expand=True) # Ensure this PanedWindow fills the appearance page

        # Create the "Toolbar" contents of the page.
        self.group1 = Pmw.Group(self.main_appearance_page, tag_text = 'Settings')
        self.mainframe = Frame(self.group1.interior())
        self.mainframe.pack(fill=BOTH, expand=True) # Make mainframe fill group1.interior()

        pw = PanedWindow(self.mainframe, orient=tk.VERTICAL)
        pw.configure(sashrelief = GROOVE, showhandle=True, opaqueresize=False, sashpad=10)
        pw.pack(fill=BOTH, expand=True) # Make this vertical paned window fill the mainframe

        self.subfr_1 = Frame(self.mainframe)

        def print_answers(event):
            print("Selected Option: {}".format(self.option_.get()))
            return None

        b1 = tkinter.Checkbutton(self.subfr_1, text = 'Show toolbar')
        b1.grid(row = 0, column = 0, sticky=W)
        b2 = tkinter.Checkbutton(self.subfr_1, text = 'Toolbar tips')
        b2.grid(row = 0, column = 1, sticky=W)
        b3 = tkinter.Checkbutton(self.subfr_1, text = 'Show toolbar')
        b3.grid(row = 1, column = 0, sticky=W)
        b4 = tkinter.Checkbutton(self.subfr_1, text = 'Toolbar tips')
        b4.grid(row = 1, column = 1, sticky=W)


        def make_plot():
            undulations_array_masked, lon_grid, lat_grid = ggf_data()
            # Clear existing axes if any, and then add a new one for clean plot updates
            for sub_ax in self.fig.axes:
                sub_ax.remove()
            # Re-add ax to ensure it's fresh and takes up full figure area
            self.ax = self.fig.add_subplot(111) # Use add_subplot(111) for typical full-figure single plot
            self.ax.grid(True) # Re-add grid if desired
            geoid_plot('Geoid Undulations', self.canvas, self.ax, self.fig, undulations_array_masked, lon_grid, lat_grid)
            self.canvas.draw() # Ensure plot is redrawn after updating data

        #plot trigger button
        self.plotbutton=tk.Button(master=self.subfr_1, text="Compute", command=make_plot)
        self.plotbutton.grid(row=3,column=0, sticky=W)
        self.subfr_1.pack(side='top') # Use 'top' as it's within a vertical paned window

        self.subfr_2 = LabelFrame(self.mainframe, text="Console")
        scroll = tkinter.Scrollbar(self.subfr_2, orient='vertical')
        scroll.pack(side='right', fill='y')
        text = Text(self.subfr_2, width=60)
        scroll.config(command=text.yview)
        text.focus_set()
        text.config(state=DISABLED, wrap=WORD, yscrollcommand=scroll.set)
        text.pack(side='top', fill='both', expand=1)
        self.subfr_2.pack(side='bottom', fill='both', expand=True) # Make console fill remaining space

        # REMOVE these two lines, as group1 and group2 are managed by pw_hor
        # self.group1.pack(side='left', fill = 'y', expand = 1, padx = 10, pady = 10)
        # self.mainframe.pack() # This line is correctly handling the mainframe within group1.interior()
        pw.add(self.subfr_1)
        pw.add(self.subfr_2)
        # self.mainframe.pack() # This line is already above, handled by self.mainframe.pack(fill=BOTH, expand=True)

        # Create the "Startup" contents of the page.
        self.group2 = Pmw.Group(self.main_appearance_page, tag_text = 'Results')

        self.nnotebook = Pmw.NoteBook(self.group2.interior())
        # *** CRITICAL CHANGE: Pack sub-notebook to fill its parent (group2.interior())
        self.nnotebook.pack(fill = 'both', expand = True, padx = 0, pady = 0) # Removed side='right' and adjusted padding

        self.plot_page_in_subnotebook = self.nnotebook.add('Geoid Plot') # Renamed `self.page1` to avoid confusion

        # Add mpl Figure
        self.fig, self.ax = plt.subplots(figsize=(10, 10)) # Initial size, but will be overridden by pack
        self.ax.grid()

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_page_in_subnotebook)
        toolbar = NavigationToolbar2Tk(self.canvas, self.plot_page_in_subnotebook)
        toolbar.update()
        # *** CRITICAL CHANGE: Pack the toolbar and canvas correctly
        toolbar.pack(side=tk.TOP, fill=tk.X, expand=False) # Toolbar at the top, fills horizontally
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True) # Canvas below, fills remaining space

        self.page3 = self.nnotebook.add('Geoid Info')

        # REMOVE this line, as group1 and group2 are managed by pw_hor
        # self.group2.pack(fill = 'both', expand = 1, padx = 10, pady = 10)

        # Add groups to the horizontal paned window
        pw_hor.add(self.group1)
        pw_hor.add(self.group2)


        self.page5 = self.notebook.add('Images')

        self.notebook.setnaturalsize()
        self.nnotebook.setnaturalsize()


def donothing():
    print('nothing')

class MenuBar(Menu):
    def __init__(self, parent):
        Menu.__init__(self, parent)
        filemenu = Menu(self, tearoff=False)
        filemenu.add_command(label="New", command=donothing)
        filemenu.add_command(label="Open", command=self.__openFile)
        filemenu.add_command(label="Save", command=donothing)
        filemenu.add_command(label="Save as...", command=donothing)
        filemenu.add_command(label="Close", command=donothing)
        self.add_cascade(label="File", menu=filemenu)
        toolMenu = Menu(self, tearoff=False)
        self.add_cascade(label="Tools", menu=toolMenu)

    def __openFile(self):
        self.__file = askopenfilename(defaultextension=".txt", filetypes=[("All Files","*.*"),("Text Documents","*.txt")])
        if self.__file == "":
            self.__file = None
        else:
            # Placeholder for widget.st and header_str - these need to be defined elsewhere in your full application
            print(f"Opening file: {self.__file}")
            # widget.st.clear()
            # widget.st.handle_csv(self.__file)
            # widget.st.configure(Header_state = 'normal')
            # headerLine = header_str
            # widget.st.component('columnheader').insert('0.0', headerLine)
            # widget.st.configure(Header_state = 'disabled')


class TextRedirector(object):
    def __init__(self, widget, tag="stdout"):
        self.widget = widget
        self.tag = tag

    def write(self, str):
        self.widget.configure(state="normal")
        self.widget.insert("end", str, (self.tag,))
        self.widget.configure(state="disabled")

######################################################################

# Create demo in root window for testing.
if __name__ == '__main__':
    root = tkinter.Tk()
    root.resizable(True, True)
    Pmw.initialise(root)
    root.title('Geoid reader')
    widget = MainWindow(root) # Keep 'widget' reference if other parts of code rely on it for global access
    root.mainloop()
