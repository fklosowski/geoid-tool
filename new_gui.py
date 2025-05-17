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
        self.page1 = self.notebook.add('Appearance')
        self.notebook.tab('Appearance').focus_set()

        pw_hor = PanedWindow(self.page1, orient=tk.HORIZONTAL)
        pw_hor.configure(sashrelief = GROOVE, sashpad=10, opaqueresize=False, showhandle=True)

        # Create the "Toolbar" contents of the page.
        self.group1 = Pmw.Group(self.page1, tag_text = 'Settings')

        self.mainframe = Frame(self.group1.interior())
        pw = PanedWindow(self.mainframe, orient=tk.VERTICAL)
        #pw.insert(self.mainframe)
        pw.configure(sashrelief = GROOVE, showhandle=True, opaqueresize=False, sashpad=10)

        self.subfr_1 = Frame(self.mainframe)

        def print_answers(event):
            print("Selected Option: {}".format(self.option_.get()))
            return None

##        optionList = list(plotters_.keys())
##        self.option_ = tk.StringVar()
##        self.option_.set(optionList[0])
##        self.om = tk.OptionMenu(self.subfr_1, self.option_, *optionList, command=print_answers)
##        #self.om.config(width=20)
##        self.om.grid(row=2, column=0, columnspan=2, sticky=tk.EW)
##        # method for disabling an entry
##        self.om['menu'].entryconfigure('Select method', state = "disabled")

        b1 = tkinter.Checkbutton(self.subfr_1, text = 'Show toolbar') # Changed from Tkinter
        b1.grid(row = 0, column = 0, sticky=W)
        b2 = tkinter.Checkbutton(self.subfr_1, text = 'Toolbar tips') # Changed from Tkinter
        b2.grid(row = 0, column = 1, sticky=W)
        b3 = tkinter.Checkbutton(self.subfr_1, text = 'Show toolbar') # Changed from Tkinter
        b3.grid(row = 1, column = 0, sticky=W)
        b4 = tkinter.Checkbutton(self.subfr_1, text = 'Toolbar tips') # Changed from Tkinter
        b4.grid(row = 1, column = 1, sticky=W)

        def make_plot():
            undulations_array_masked, lon_grid, lat_grid = ggf_data()
            for sub_ax in self.fig.axes:
                sub_ax.remove()
            self.ax = self.fig.add_axes([0.1,0.1,0.8,0.8], polar=False)
            geoid_plot('aaaa', self.canvas, self.ax, self.fig, undulations_array_masked, lon_grid, lat_grid)

        #plot trigger button
        self.plotbutton=tk.Button(master=self.subfr_1, text="Compute", command=make_plot)
        self.plotbutton.grid(row=3,column=0, sticky=W)
        self.subfr_1.pack(side='top')


        #self.group1 = Pmw.Group(self.page1, tag_text = 'Output')
        #self.group1.pack(side='left', fill = 'y', expand = 1, padx = 10, pady = 10)

        self.subfr_2 = LabelFrame(self.mainframe, text="Console")
        scroll = tkinter.Scrollbar(self.subfr_2, orient='vertical')
        scroll.pack(side='right', fill='y')
        text = Text(self.subfr_2, width=60)
        scroll.config(command=text.yview)
        text.focus_set()
        text.config(state=DISABLED, wrap=WORD, yscrollcommand=scroll.set)
        text.pack(side='top', fill='both', expand=1)
        self.subfr_2.pack(side='bottom')

        self.group1.pack(side='left', fill = 'y', expand = 1, padx = 10, pady = 10)
        pw.add(self.subfr_1)
        pw.add(self.subfr_2)
        self.mainframe.pack()
        pw.pack(fill=BOTH, expand=True)


        # Create the "Startup" contents of the page.
        self.group2 = Pmw.Group(self.page1, tag_text = 'Results')
        self.nnotebook = Pmw.NoteBook(self.group2.interior())
        self.nnotebook.pack(side='right', fill = 'both', expand = 1, padx = 10, pady = 10)

        self.page1 = self.nnotebook.add('Geoid Plot')
        # Add mpl Figure
        #self.fig = Figure()
        #self.fig.set_figheight(5.5)
        #self.fig.set_figwidth(9.5)
        self.fig, self.ax = plt.subplots(figsize=(10, 10))
        self.ax.grid()
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.page1)
        toolbar = NavigationToolbar2Tk(self.canvas, self.page1)
        toolbar.update()
        self.canvas.get_tk_widget().pack(fill='both')

        self.page3 = self.nnotebook.add('Geoid Info')
        self.group2.pack(fill = 'both', expand = 1, padx = 10, pady = 10)

        pw_hor.add(self.group1)
        pw_hor.add(self.group2)
        pw_hor.pack(fill=BOTH, expand=True)

        self.page5 = self.notebook.add('Images')

        self.notebook.setnaturalsize()
        self.nnotebook.setnaturalsize()


def donothing():
    print('nothing') # Changed from print statement

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
        #fileMenu.add_command(label="Exit", command=parent.menu_callback_stop)
        toolMenu = Menu(self, tearoff=False)
        self.add_cascade(label="Tools", menu=toolMenu)
        #toolMenu.add_command(label="Extract Instructions",
        #                             command=parent.menu_callback_extract)
    def __openFile(self):
        self.__file = askopenfilename(defaultextension=".txt", filetypes=[("All Files","*.*"),("Text Documents","*.txt")])
        if self.__file == "":
            # no file to open
            self.__file = None
        else:
            # Note: widget.st, header_str, and ggf_data() are not defined in the provided snippet.
            # Ensure these are correctly defined or imported in your full application.
            widget.st.clear()
            widget.st.handle_csv(self.__file)
            widget.st.configure(Header_state = 'normal')
            headerLine = header_str
            widget.st.component('columnheader').insert('0.0', headerLine)
            #loaded_points = widget.st.getvalue()
##            #nop = loaded_points.count('\n')
##            f = open(self.__file)
##            for idx, line in enumerate(f):
##                widget.st.component('rowheader').insert('end', str(idx+1)+ '\n')
##                widget.st.insert('end', line)
            widget.st.configure(Header_state = 'disabled')


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
    root = tkinter.Tk() # Changed from Tkinter
    #root.state('zoomed')
    root.resizable(True, True)
    #root.grid_rowconfigure(1, weight=1)
    #root.grid_columnconfigure(1, weight=1)
    Pmw.initialise(root)
    root.title('Geoid reader')
    widget = MainWindow(root)
    root.mainloop()
