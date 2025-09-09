
from tkinter import *
from tkinter import ttk
from pandastable import Table
import pandas as pd
from tkinter import scrolledtext
from asociety.generator.persona_generator import *
from studio.languages import LANGUAGES
from asociety.repository.database import get_engine
from tkinter import ttk, filedialog
import os
class PersonalityBrowser:
    def __init__(self, parent) -> None:
        self.lang = 'zh'
        self.main = inner_panedwindow = ttk.PanedWindow(parent, orient=VERTICAL)
        inner_panedwindow.pack(fill=BOTH, expand=True)

        # Create two frames to be added to the inner PanedWindow
        self.top_frame = ttk.Frame(inner_panedwindow, width=400, height=500, relief=SUNKEN,style='TFrame')
        bottom_frame = ttk.Frame(inner_panedwindow, width=400, height=200, relief=SUNKEN,style='TFrame')

        # Add the frames to the inner PanedWindow
        inner_panedwindow.add(self.top_frame, weight=2)
        inner_panedwindow.add(bottom_frame, weight=1)

        # 标题
        self.title_label = ttk.Label(self.top_frame, text=LANGUAGES[self.lang]['personality'], font=("Helvetica", 16, "bold"))
        self.title_label.pack(pady=(10, 0))

        self.canvas = None
        self.fig = None
        self.axs = None
        self.plot_empty()

        # --- Control Frame ---
        control_frame = ttk.Frame(bottom_frame)
        control_frame.pack(fill=X, pady=5)
        self.file_label = ttk.Label(control_frame, text="Selected File: None")
        self.file_label.pack(side=LEFT, padx=10)
        browse_button = ttk.Button(control_frame, text="Browse File...", command=self.browse_file)
        browse_button.pack(side=LEFT, padx=10)

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
            initialdir='data/db',
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
            pjson = self.table.model.df.iloc[row_clicked]['personality_json']
            import threading
            task_thread = threading.Thread(target=self.plot_fill,kwargs={'pjson':pjson})
            task_thread.start()
    def plot_empty(self):
        import matplotlib
        matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'STHeiti', 'Arial Unicode MS']
        matplotlib.rcParams['axes.unicode_minus'] = False
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        import matplotlib.pyplot as plt
        lang = self.lang
        titles = LANGUAGES[lang]['trait_names'] + ['']
        # 销毁旧canvas
        if hasattr(self, 'canvas') and self.canvas is not None:
            self.canvas.get_tk_widget().destroy()
        self.fig, self.axs = plt.subplots(3, 2)
        self.axs[2,1].set_axis_off()    
        for i, ax in enumerate(self.axs.flat):
            ax.set_title(titles[i] if i < len(titles) else '')
            ax.set(xlabel=LANGUAGES[lang]['age'], ylabel=LANGUAGES[lang]['score'])
        self.fig.tight_layout()
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.top_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)
    def plot_fill(self,pjson):
        import matplotlib
        matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'STHeiti', 'Arial Unicode MS']
        matplotlib.rcParams['axes.unicode_minus'] = False
        from asociety.personality.ipipneo.quiz import plot_results_by
        import json
        per = json.loads(pjson)
        colors = ['orange','green','magenta','red','blue']
        lang = self.lang
        titles = LANGUAGES[lang]['trait_names'] + ['']
        from asociety.personality.personality_quiz import PersonalityResult
        pr = PersonalityResult(result=per)
        all = pr.all
        for i in range(0, 5):
            row = int(i / 2)
            col = i % 2
            data = all[i]
            self.axs[row, col].cla()
            self.axs[row, col].barh(data.keys(), data.values(), color=colors[i])
            self.axs[row, col].set_title(titles[i])
            self.axs[row, col].set(xlabel=LANGUAGES[lang]['age'], ylabel=LANGUAGES[lang]['score'])
        # 保证空白图的title也刷新
        for i in range(5, 6):
            row = int(i / 2)
            col = i % 2
            self.axs[row, col].set_title('')
        self.canvas.draw()
    def set_language(self, lang):
        self.lang = lang
        self.title_label.config(text=LANGUAGES[lang]['personality'])
        self.plot_empty()
    def refresh_data(self, db_path):
        import pandas as pd
        from sqlalchemy import create_engine
        engine = create_engine(f'sqlite:///{db_path}')
        df = pd.read_sql_query("select * from personality", engine)
        self.table.model.df = df
        self.table.redraw()

