
import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from abc import ABC, abstractmethod
import os
from asociety.personality.personality_analysis import compute
from studio.languages import LANGUAGES

class BaseCurvePanel(ABC):
    def __init__(self, parent):
        self.lang = 'zh'
        self.main = ttk.Frame(parent)
        
        self.control_frame = self.create_control_frame(self.main)
        self.control_frame.pack(side=tk.BOTTOM, pady=10)

        title_label = ttk.Label(self.main, text=self.get_panel_title(), font=("Helvetica", 16, "bold"))
        title_label.pack(pady=(5, 5), side=tk.TOP)

        paned_window = ttk.PanedWindow(self.main, orient=tk.VERTICAL)
        paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.plot_frame = ttk.Frame(paned_window, relief=tk.SUNKEN)
        paned_window.add(self.plot_frame, weight=3)

        table_frame = ttk.Frame(paned_window)
        paned_window.add(table_frame, weight=1)
        
        table_title = ttk.Label(table_frame, text=LANGUAGES[self.lang]['distance_table_title'], font=("Helvetica", 12))
        table_title.pack(pady=(5,5))

        self.table_columns = ('model', 'N', 'E', 'O', 'A', 'C', 'euclidean')
        self.table = ttk.Treeview(table_frame, columns=self.table_columns, show='headings')
        self.setup_table_headings()
        self.table.pack(fill=tk.BOTH, expand=True)

        self.canvas = None
        self.fig = None
        self.axs = None
        self.plot_empty()

    def setup_table_headings(self):
        self.table.heading('model', text='Model')
        self.table.heading('N', text='Neuroticism')
        self.table.heading('E', text='Extraversion')
        self.table.heading('O', text='Openness')
        self.table.heading('A', text='Agreeableness')
        self.table.heading('C', text='Conscientiousness')
        self.table.heading('euclidean', text='Euclidean Dist.')
        self.table.column('model', width=180)
        for col in ('N', 'E', 'O', 'A', 'C', 'euclidean'):
            self.table.column(col, width=100, anchor='center')

    @abstractmethod
    def get_panel_title(self):
        """Return the main title for the panel."""
        pass

    @abstractmethod
    def create_control_frame(self, parent):
        """Create and return the specific control frame for the subclass."""
        pass

    @abstractmethod
    def get_data_sources(self):
        """Return a list of data source dictionaries.
        Each dict should contain: 'name', 'path', 'style' (dict with color, lw, ls, etc.),
        and other necessary metadata like 'sex_filter'.
        The first source is expected to be the baseline (e.g., human).
        """
        pass

    def _process_data_sources(self, model_sources):
        """
        Process a list of model data sources, add the human baseline,
        check for file existence, and load the analysis data.
        """
        if not model_sources:
            return []

        human_db_path = 'data/db/backup/human.db'
        if not os.path.exists(human_db_path):
            messagebox.showerror("Error", f"Human baseline database not found: {human_db_path}")
            return []

        all_sources = [
            {'name': 'human', 'path': human_db_path, 'style': {'color': 'purple', 'ls': '--'}},
        ] + model_sources

        # Check if all files exist
        for source in all_sources:
            if not os.path.exists(source['path']):
                messagebox.showerror("Error", f"Database file not found: {source['path']}")
                return []

        # Load data into sources
        try:
            from asociety.personality.personality_analysis import get_personas_ana
            for source in all_sources:
                source['mdata'] = get_personas_ana(db_path=source['path'], dimension='age')
        except Exception as e:
            messagebox.showerror("Data Loading Error", f"Failed to load data: {e}")
            return []
            
        return all_sources

    def run_analysis(self):
        try:
            model_sources = self.get_data_sources()
            data_sources =  self._process_data_sources(model_sources)
            if not data_sources:
                return

            # The first data source is the baseline
            baseline_source = data_sources[0]
            
            trait_order = ['Neuroticism', 'Extraversion', 'Openness', 'Agreeableness', 'Conscientiousness']
            data_index_map = [5, 3, 1, 4, 2] # O,C,E,A,N -> N,E,O,A,C

            for ax in self.axs.flat:
                ax.cla()

            curves = {}
            min_age, max_age = -np.inf, np.inf

            # First pass: get data and age ranges
            for source in data_sources:
                mdata = source['mdata']
                min_age = max(min_age, min(mdata[0]))
                max_age = min(max_age, max(mdata[0]))
                curves[source['name']] = [None] * 5

            # Second pass: plot data
            for i in range(5):
                row, col = int(i / 3), i % 3
                ax = self.axs[row, col]
                data_idx = data_index_map[i]

                for source in data_sources:
                    mdata = source['mdata']
                    x_scatter, y_scatter, x_curve, y_curve = compute(mdata[0], mdata[data_idx])
                    
                    if x_curve.size > 0:
                        curves[source['name']][i] = (x_curve, y_curve)
                        style = source.get('style', {})
                        ax.plot(x_curve, y_curve, 
                                color=style.get('color'), 
                                label=source['name'], 
                                linewidth=style.get('lw', 1), 
                                linestyle=style.get('ls', '-'))
                        
                        if style.get('show_scatter', False):
                             ax.plot(x_scatter, y_scatter, style.get('marker', '*'), color=style.get('color'))

                ax.set_title(trait_order[i])
                ax.set_xlabel(LANGUAGES[self.lang]['age'])
                ax.set_ylabel(LANGUAGES[self.lang]['score'])
                ax.grid(True, linestyle='--', alpha=0.6)
                ax.set_xlim(min_age, max_age)

            handles, labels = self.axs[0, 0].get_legend_handles_labels()
            self.axs[1, 2].legend(handles, labels, loc='center', fontsize='large')
            self.axs[1, 2].axis('off')
            self.fig.tight_layout()
            self.canvas.draw()

            self.update_distance_table(curves, baseline_source['name'])

        except Exception as e:
            messagebox.showerror("Analysis Error", str(e))

    def update_distance_table(self, curves, baseline_name):
        for i in self.table.get_children():
            self.table.delete(i)

        ages_to_check = np.array([20, 30, 40, 50, 60, 70])
        baseline_curves = curves.get(baseline_name)
        if not baseline_curves:
            return

        for model_name, model_curves in curves.items():
            if model_name == baseline_name:
                continue

            row_values = [model_name]
            trait_distances = []

            for i in range(5):
                if baseline_curves[i] is not None and model_curves[i] is not None:
                    h_x, h_y = baseline_curves[i]
                    m_x, m_y = model_curves[i]
                    
                    baseline_scores = np.interp(ages_to_check, h_x, h_y)
                    model_scores = np.interp(ages_to_check, m_x, m_y)
                    
                    avg_dist = np.mean(np.abs(baseline_scores - model_scores))
                    row_values.append(f"{avg_dist:.2f}")
                    trait_distances.append(avg_dist)
                else:
                    row_values.append("N/A")
                    trait_distances.append(np.nan)

            if not np.isnan(trait_distances).any():
                euclidean_dist = np.linalg.norm(trait_distances)
                row_values.append(f"{euclidean_dist:.2f}")
            else:
                row_values.append("N/A")

            self.table.insert("", "end", values=tuple(row_values))

    def plot_empty(self):
        if self.canvas:
            self.canvas.get_tk_widget().destroy()

        self.fig, self.axs = plt.subplots(2, 3, figsize=(12, 8))
        self.axs[1, 2].set_axis_off()

        trait_order = ['Neuroticism', 'Extraversion', 'Openness', 'Agreeableness', 'Conscientiousness', '']
        for i, ax in enumerate(self.axs.flat):
            if i < 5:
                ax.set_title(trait_order[i])
                ax.set_xlabel(LANGUAGES[self.lang]['age'])
                ax.set_ylabel(LANGUAGES[self.lang]['score'])
                ax.grid(True, linestyle='--', alpha=0.6)

        self.fig.tight_layout()
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def set_language(self, lang):
        self.lang = lang
        # Potentially update labels in control frame and plot
        self.plot_empty()

    def setData(self, appKey, updateTree):
        pass
