import tkinter as tk
from tkinter import ttk, messagebox

from studio.value_curve_panel import ValueCurvePanelBase


class ValueNarrativeComparisonPanel(ValueCurvePanelBase):
    def get_panel_title(self):
        return "Narrative vs Antialign vs Normal Value Generation Curve Comparison"

    def create_control_frame(self, parent):
        control_frame = ttk.Frame(parent)
        self.run_button = ttk.Button(control_frame, text="Run Narrative Comparison Analysis", command=self.trigger_analysis)
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
            {'name': 'standard', 'path': 'data/db/value/population/standard.db', 'style': {'color': 'blue', 'lw': 2.0}},
            {'name': 'antialign', 'path': 'data/db/value/population/antialign.db', 'style': {'color': 'red', 'lw': 2.0}},
            {'name': 'narrative', 'path': 'data/db/value/population/narrative.db', 'style': {'color': 'green', 'lw': 2.5}},
        ]
