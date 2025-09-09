
import tkinter as tk
from tkinter import ttk, messagebox
import os
from asociety.personality.personality_analysis import get_personas_ana
from studio.base_curve_panel import BaseCurvePanel
from studio.languages import LANGUAGES

class CurveComparisonPanel(BaseCurvePanel):
    def get_panel_title(self):
        return "LLM vs Human Age-Personality Curve Comparison"

    def create_control_frame(self, parent):
        control_frame = ttk.Frame(parent)
        self.run_button = ttk.Button(control_frame, text="Run Comparison Analysis", command=self.trigger_analysis)
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
        model_sources = [
            {'name': 'deepseek-chat', 'path': 'data/db/backup/deepseek-chat.db', 'style': {'color': 'blue', 'lw': 0.8}},
            {'name': 'deepseek-chat-antialign', 'path': 'data/db/backup/deepseek-chat-antialign.db', 'style': {'color': 'red', 'lw': 0.8}},
            {'name': 'deepseek-chat-narrative', 'path': 'data/db/backup/deepseek-chat-narrative.db', 'style': {'color': 'green', 'lw': 2.5}},
            {'name': 'wiki-fiction', 'path': 'data/db/backup/wiki/wiki-fiction.db', 'style': {'color': 'orange', 'ls': '-.'}}
        ]
        return model_sources
