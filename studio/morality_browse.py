from tkinter import *
from tkinter import ttk, filedialog
from pandastable import Table
import pandas as pd
import os

from studio.languages import LANGUAGES
from studio import theme
from asociety.morality import mfq


class MoralityBrowser:
    def __init__(self, parent) -> None:
        self.lang = 'zh'
        self.main = ttk.Frame(parent, padding=theme.PAGE_PADDING)
        self.main.pack(fill=BOTH, expand=True)

        self.title_label = ttk.Label(self.main, text=LANGUAGES[self.lang]['morality'],
                                     font=theme.FONT_H2)
        self.title_label.pack(anchor='w', pady=(0, theme.M))

        inner_panedwindow = ttk.PanedWindow(self.main, orient=VERTICAL)
        inner_panedwindow.pack(fill=BOTH, expand=True)

        self.top_frame = ttk.Frame(inner_panedwindow)
        bottom_frame = ttk.Frame(inner_panedwindow)
        inner_panedwindow.add(self.top_frame, weight=2)
        inner_panedwindow.add(bottom_frame, weight=1)

        self.canvas = None
        self.fig = None
        self.axs = None
        self.plot_empty()

        # --- Control Frame ---
        control_frame = ttk.Frame(bottom_frame)
        control_frame.pack(fill=X, pady=(theme.S, theme.M))
        self.file_label = ttk.Label(control_frame, text="Selected File: None")
        self.file_label.pack(side=LEFT, padx=(theme.S, 0))
        browse_button = ttk.Button(control_frame, text="Browse File...", command=self.browse_file)
        browse_button.pack(side=LEFT, padx=theme.S)

        # --- Table Frame ---
        table_frame = ttk.Frame(bottom_frame)
        table_frame.pack(fill=BOTH, expand=True)
        self.table = Table(table_frame, showstatusbar=True)
        if hasattr(self.table, 'toolbar'):
            del self.table.toolbar
        self.table.show()
        self.table.bind("<ButtonRelease-1>", self.on_row_click)
        self.table.model.df = pd.DataFrame()
        self.table.redraw()

    def browse_file(self):
        file_path = filedialog.askopenfilename(
            title='Select a persona DB file',
            initialdir='data/db/morality',
            filetypes=[('SQLite DB', '*.db'), ('All Files', '*.*')]
        )
        if file_path:
            self.file_label.config(text=f"Selected File: ...{os.path.basename(file_path)}")
            self.refresh_data(file_path)

    def setData(self, item, updateTree):
        self.table.redraw()

    def on_row_click(self, event):
        row_clicked = self.table.get_row_clicked(event)
        if row_clicked is not None:
            self.plot_fill(self.table.model.df.iloc[row_clicked])

    def plot_empty(self):
        import matplotlib
        matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'STHeiti', 'Arial Unicode MS']
        matplotlib.rcParams['axes.unicode_minus'] = False
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        import matplotlib.pyplot as plt
        if self.canvas is not None:
            self.canvas.get_tk_widget().destroy()
        self.fig, self.axs = plt.subplots(1, 2, figsize=(11, 5))
        self._style_axes()
        self.fig.tight_layout()
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.top_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)

    def _style_axes(self):
        lang = self.lang
        for ax, title in zip(self.axs, (LANGUAGES[lang]['morality_foundation_group'],
                                        LANGUAGES[lang]['morality_higher_group'])):
            ax.set_title(title)
            ax.set_xlabel(LANGUAGES[lang]['score'])

    def plot_fill(self, row):
        for ax, columns, color in ((self.axs[0], mfq.FOUNDATION_TO_COLUMN, 'steelblue'),
                                   (self.axs[1], mfq.HIGHER_TO_COLUMN, 'darkorange')):
            names = list(columns.keys())
            ax.cla()
            ax.barh(names, [row[columns[n]] for n in names], color=color)
        self._style_axes()
        self.canvas.draw()

    def set_language(self, lang):
        self.lang = lang
        self.title_label.config(text=LANGUAGES[lang]['morality'])
        self.plot_empty()

    def refresh_data(self, db_path):
        from sqlalchemy import create_engine
        engine = create_engine(f'sqlite:///{db_path}')
        df = pd.read_sql_query("select * from morality", engine)
        self.table.model.df = df
        self.table.redraw()
