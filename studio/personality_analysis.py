import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from asociety.personality.personality_analysis import get_personas_ana
from studio.base_curve_panel import BaseCurvePanel
from studio.languages import LANGUAGES

class PersonalityAnalysis(BaseCurvePanel):
    def __init__(self, parent):
        self.selected_file = None
        super().__init__(parent)

    def get_panel_title(self):
        return LANGUAGES[self.lang]['plot_title']

    def create_control_frame(self, parent):
        control_frame = ttk.Frame(parent)

        self.file_label = ttk.Label(control_frame, text="Selected File: None")
        self.file_label.grid(row=0, column=0, padx=(0, 10), sticky='w')

        browse_button = ttk.Button(control_frame, text="Browse File...", command=self.browse_file)
        browse_button.grid(row=0, column=1, padx=(0, 10))


        self.submit_button = ttk.Button(control_frame, text=LANGUAGES[self.lang]['create'], command=self.trigger_analysis, state=tk.DISABLED)
        self.submit_button.grid(row=3, column=0, columnspan=2, pady=(10,0))
        
        return control_frame

    def browse_file(self):
        file_path = filedialog.askopenfilename(
            title='Select a persona DB file',
            initialdir='data/db/backup',
            filetypes=[('SQLite DB', '*.db'), ('All Files', '*.*')]
        )
        if file_path:
            self.selected_file = file_path
            self.file_label.config(text=f"Selected File: ...{os.path.basename(file_path)}")
            self.submit_button.config(state=tk.NORMAL)
            self.plot_empty()

    def trigger_analysis(self):
        if not self.selected_file:
            messagebox.showwarning("Warning", "Please select a database file first.")
            return
        self.submit_button.config(state=tk.DISABLED)
        self.main.after(100, self.run_analysis_with_data)

    def run_analysis_with_data(self):
        try:
            super().run_analysis()
        except Exception as e:
            messagebox.showerror("Analysis Error", str(e))
        finally:
            self.submit_button.config(state=tk.NORMAL)

    def get_data_sources(self):
        


        
        model_name = os.path.splitext(os.path.basename(self.selected_file))[0]

        sources = [

            {'name': model_name, 'path': self.selected_file, 'style': {'color': 'red', 'ls': '-', 'show_scatter': False}}
        ]

            
        return sources

    def set_language(self, lang):
        super().set_language(lang)
        self.submit_button.config(text=LANGUAGES[lang]['create'])

    def setData(self, appKey, updateTree):
        pass
