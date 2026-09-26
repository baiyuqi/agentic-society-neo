import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os

from studio.morality_curve_panel import MoralityCurvePanelBase
from studio.languages import LANGUAGES


class MoralityAgeCurve(MoralityCurvePanelBase):
    """Single-file age-curve browser for the MFQ-30 moral foundations."""

    initialdir = 'data/db/morality'

    def __init__(self, parent):
        self.selected_file = None
        super().__init__(parent)

    def get_panel_title(self):
        return LANGUAGES[self.lang]['morality_plot_title']

    def create_control_frame(self, parent):
        control_frame = ttk.Frame(parent)

        self.file_label = ttk.Label(control_frame, text="Selected File: None")
        self.file_label.grid(row=0, column=0, padx=(0, 10), sticky='w')

        browse_button = ttk.Button(control_frame, text="Browse File...", command=self.browse_file)
        browse_button.grid(row=0, column=1, padx=(0, 10))

        self.submit_button = ttk.Button(control_frame, text=LANGUAGES[self.lang]['create'],
                                        command=self.trigger_analysis, state=tk.DISABLED)
        self.submit_button.grid(row=3, column=0, columnspan=2, pady=(10, 0))

        self.save_button = ttk.Button(control_frame, text="Save to SVG",
                                      command=self.save_to_svg, state=tk.DISABLED)
        self.save_button.grid(row=4, column=0, columnspan=2, pady=(5, 0))

        return control_frame

    def browse_file(self):
        file_path = filedialog.askopenfilename(
            title='Select a persona DB file',
            initialdir=self.initialdir,
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
            self.save_button.config(state=tk.NORMAL)
        except Exception as e:
            messagebox.showerror("Analysis Error", str(e))
        finally:
            self.submit_button.config(state=tk.NORMAL)

    def get_data_sources(self):
        model_name = os.path.splitext(os.path.basename(self.selected_file))[0]
        return [
            {'name': model_name, 'path': self.selected_file,
             'style': {'color': 'red', 'ls': '-', 'show_scatter': False}}
        ]

    def save_to_svg(self):
        if self.fig is None:
            messagebox.showwarning("No Plot", "请先运行分析以生成图表。")
            return
        file_path = filedialog.asksaveasfilename(
            title="保存图表为 SVG",
            defaultextension=".svg",
            filetypes=[("SVG Files", "*.svg"), ("All Files", "*.*")]
        )
        if file_path:
            self.fig.savefig(file_path, format="svg", bbox_inches="tight")
            messagebox.showinfo("成功", f"图表已保存到:\n{file_path}")

    def set_language(self, lang):
        super().set_language(lang)
        self.submit_button.config(text=LANGUAGES[lang]['create'])

    def setData(self, appKey, updateTree):
        pass
