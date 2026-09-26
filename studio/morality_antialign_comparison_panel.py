import tkinter as tk
from tkinter import ttk, messagebox

from studio.morality_curve_panel import MoralityCurvePanelBase


class MoralityAntialignComparisonPanel(MoralityCurvePanelBase):
    def get_panel_title(self):
        return "Antialign vs Normal Morality Generation Curve Comparison"

    def create_control_frame(self, parent):
        control_frame = ttk.Frame(parent)
        self.run_button = ttk.Button(control_frame, text="Run Antialign Comparison Analysis", command=self.trigger_analysis)
        self.run_button.pack()
        return control_frame

    def trigger_analysis(self):
        self.run_button.config(state=tk.DISABLED)
        self.main.after(100, self.run_analysis_with_data)

    def run_analysis_with_data(self):
        try:
            super().run_analysis()
        except Exception as e:
            messagebox.showerror("Analysis Error", str(e))
        finally:
            self.run_button.config(state=tk.NORMAL)

    def get_data_sources(self):
        return [
            {'name': 'standard', 'path': 'data/db/morality/population/standard.db', 'style': {'color': 'blue', 'lw': 2.0}},
            {'name': 'antialign', 'path': 'data/db/morality/population/antialign.db', 'style': {'color': 'red', 'lw': 2.0}},
        ]
