
import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from abc import ABC, abstractmethod
import os
from asociety.personality.personality_analysis import compute, get_personas_ana
from studio.languages import LANGUAGES
from studio import theme

class BaseCurvePanel(ABC):
    # --- Instrument surface -----------------------------------------------------------
    # The defaults reproduce the Big Five panels exactly; a panel for another instrument
    # (e.g. the Schwartz values) overrides them. `trait_order[i]` is plotted against
    # `mdata[data_index_map[i]]`, where mdata[0] is the shared dimension column (age).
    trait_order = ['Neuroticism', 'Extraversion', 'Openness', 'Agreeableness', 'Conscientiousness']
    data_index_map = [5, 3, 1, 4, 2]  # display slot -> mdata index (O,C,E,A,N)
    table_columns = ('model', 'N', 'E', 'O', 'A', 'C', 'euclidean')
    table_headings = {
        'model': 'Model', 'N': 'Neuroticism', 'E': 'Extraversion', 'O': 'Openness',
        'A': 'Agreeableness', 'C': 'Conscientiousness', 'euclidean': 'Euclidean Dist.',
    }
    human_db_path = 'data/db/personality/human.db'
    ages_to_check = np.array([20, 30, 40, 50, 60, 70])
    grid_shape = (2, 3)

    @property
    def n_traits(self):
        return len(self.trait_order)

    def __init__(self, parent):
        self.lang = 'zh'
        self.main = ttk.Frame(parent, padding=theme.PAGE_PADDING)

        self.control_frame = self.create_control_frame(self.main)
        self.control_frame.pack(side=tk.BOTTOM, pady=10)

        theme.page_header(self.main, self.get_panel_title())

        paned_window = ttk.PanedWindow(self.main, orient=tk.VERTICAL)
        paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.plot_frame = ttk.Frame(paned_window)
        paned_window.add(self.plot_frame, weight=3)

        table_frame = ttk.Frame(paned_window)
        paned_window.add(table_frame, weight=1)

        table_title = ttk.Label(table_frame, text=LANGUAGES[self.lang]['distance_table_title'])
        table_title.pack(pady=(5,5))

        self.table = ttk.Treeview(table_frame, columns=self.table_columns, show='headings')
        self.setup_table_headings()
        self.table.pack(fill=tk.BOTH, expand=True)

        self.canvas = None
        self.fig = None
        self.axs = None
        self.plot_empty()

    def setup_table_headings(self):
        for col, text in self.table_headings.items():
            self.table.heading(col, text=text)
        self.table.column('model', width=180)
        for col in self.table_columns:
            if col != 'model':
                self.table.column(col, width=100, anchor='center')

    def load_mdata(self, db_path):
        """Curve data as [dimension_column, *trait_columns]. Override for another instrument."""
        return get_personas_ana(db_path=db_path, dimension='age')

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

        # The human reference curve is optional: an instrument with no usable human sample sets
        # human_db_path = None and plots the model arms alone.
        human_db_path = self.human_db_path
        all_sources = list(model_sources)
        if human_db_path and os.path.exists(human_db_path):
            all_sources = [
                {'name': 'human', 'path': human_db_path, 'style': {'color': 'purple', 'ls': '--'}},
            ] + all_sources
        elif human_db_path:
            messagebox.showwarning("No baseline",
                                   f"Human baseline database not found, plotting without it: "
                                   f"{human_db_path}")

        # Check if all files exist
        for source in all_sources:
            if not os.path.exists(source['path']):
                messagebox.showerror("Error", f"Database file not found: {source['path']}")
                return []

        # Load data into sources
        try:
            for source in all_sources:
                source['mdata'] = self.load_mdata(source['path'])
        except Exception as e:
            messagebox.showerror("Data Loading Error", f"Failed to load data: {e}")
            return []

        # An arm whose instrument table has not been filled yet (a value DB before the PVQ
        # pipeline has run, say) loads as zero rows, which would otherwise blow up on
        # min(mdata[0]) further down. Drop it with a message instead.
        loaded, skipped = [], []
        for source in all_sources:
            if source['mdata'] and source['mdata'][0]:
                loaded.append(source)
            else:
                skipped.append(source['name'])
        if skipped:
            messagebox.showwarning("No rows",
                                   "Skipping sources with no rows: " + ", ".join(skipped))
        if not loaded:
            messagebox.showwarning("Nothing to plot", "No source holds any rows.")
            return []

        return loaded

    def run_analysis(self):
        try:
            model_sources = self.get_data_sources()
            data_sources =  self._process_data_sources(model_sources)
            if not data_sources:
                return

            # The human reference is the baseline when there is one. Without it (an instrument
            # with no human sample) the distance table has nothing to measure against and stays
            # empty rather than silently taking one model arm as the yardstick.
            baseline_source = next((s for s in data_sources if s['name'] == 'human'), None)
            
            trait_order = self.trait_order
            data_index_map = self.data_index_map
            n_traits = self.n_traits
            n_cols = self.grid_shape[1]

            for ax in self.axs.flat:
                ax.cla()

            curves = {}
            min_age, max_age = -np.inf, np.inf

            # First pass: get data and age ranges
            for source in data_sources:
                mdata = source['mdata']
                min_age = max(min_age, min(mdata[0]))
                max_age = min(max_age, max(mdata[0]))
                curves[source['name']] = [None] * n_traits

            # Second pass: plot data
            for i in range(n_traits):
                row, col = divmod(i, n_cols)
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

            legend_ax = self.axs.flat[n_traits]
            handles, labels = self.axs.flat[0].get_legend_handles_labels()
            legend_ax.legend(handles, labels, loc='center', fontsize='large')
            legend_ax.axis('off')
            self.fig.tight_layout()
            self.canvas.draw()

            self.update_distance_table(curves, baseline_source['name'] if baseline_source else None)

        except Exception as e:
            messagebox.showerror("Analysis Error", str(e))

    def update_distance_table(self, curves, baseline_name):
        for i in self.table.get_children():
            self.table.delete(i)

        ages_to_check = self.ages_to_check
        baseline_curves = curves.get(baseline_name)
        if not baseline_curves:
            return

        for model_name, model_curves in curves.items():
            if model_name == baseline_name:
                continue

            row_values = [model_name]
            trait_distances = []

            for i in range(self.n_traits):
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

        self.fig, self.axs = plt.subplots(*self.grid_shape, figsize=(12, 8))

        for i, ax in enumerate(self.axs.flat):
            if i < self.n_traits:
                ax.set_title(self.trait_order[i])
                ax.set_xlabel(LANGUAGES[self.lang]['age'])
                ax.set_ylabel(LANGUAGES[self.lang]['score'])
                ax.grid(True, linestyle='--', alpha=0.6)
            else:
                ax.set_axis_off()

        self.fig.tight_layout()
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def set_language(self, lang):
        self.lang = lang
        # Potentially update labels in control frame and plot
        self.plot_empty()

    def setData(self, appKey, updateTree):
        pass
