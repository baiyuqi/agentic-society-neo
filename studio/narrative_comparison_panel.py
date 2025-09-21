import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
from asociety.personality.personality_analysis import get_personas_ana
from studio.base_curve_panel import BaseCurvePanel
from studio.languages import LANGUAGES

class NarrativeComparisonPanel(BaseCurvePanel):
    def get_panel_title(self):
        return "Narrative vs Antialign vs Normal Generation Curve Comparison"

    def create_control_frame(self, parent):
        control_frame = ttk.Frame(parent)
        self.run_button = ttk.Button(control_frame, text="Run Narrative Comparison Analysis", command=self.trigger_analysis)
        self.run_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.save_button = ttk.Button(control_frame, text="Save to SVG", command=self.save_to_svg, state=tk.DISABLED)
        self.save_button.pack(side=tk.LEFT)
        
        return control_frame

    def trigger_analysis(self):
        self.run_button.config(state=tk.DISABLED)
        self.main.after(100, self.run_analysis_with_data)

    def run_analysis_with_data(self):
        try:
            super().run_analysis()
            # Enable save button after successful analysis
            self.save_button.config(state=tk.NORMAL)
        except Exception as e:
            messagebox.showerror("Analysis Error", str(e))
        finally:
            self.run_button.config(state=tk.NORMAL)

    def get_data_sources(self):
        # Include all three deepseek variants for comprehensive comparison
        model_sources = [
            {'name': 'deepseek-chat', 'path': 'data/db/backup/deepseek-chat.db', 'style': {'color': 'blue', 'lw': 2.0}},
            {'name': 'deepseek-chat-antialign', 'path': 'data/db/backup/deepseek-chat-antialign.db', 'style': {'color': 'red', 'lw': 2.0}},
            {'name': 'deepseek-chat-narrative', 'path': 'data/db/backup/deepseek-chat-narrative.db', 'style': {'color': 'green', 'lw': 2.5}}
        ]
        return model_sources