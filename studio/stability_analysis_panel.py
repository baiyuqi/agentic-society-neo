import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

from asociety.personality.analysis_utils import load_personality_data, PERSONALITY_TRAITS
from studio.progress_dialog import ProgressManager


class StabilityAnalysisPanel:
    # --- Instrument surface -----------------------------------------------------------
    # The defaults reproduce the personality panel exactly; the value panel overrides them.
    traits = PERSONALITY_TRAITS
    table = 'personality'
    data_dir = "data/db/personality/individual"
    title = "稳定性分析 (马氏距离)"
    methods = ('standard', 'poor')
    color_scheme = {'standard': 'blue', 'poor': 'red'}

    def __init__(self, parent):
        self.main = ttk.Frame(parent)
        self.main.pack(fill=tk.BOTH, expand=True)

        control_frame = ttk.Frame(self.main)
        control_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(control_frame, text=self.title, font=("Helvetica", 14, "bold")).pack(side=tk.LEFT, padx=(0, 20))

        self.run_button = ttk.Button(control_frame, text="运行分析", command=self.start_analysis)
        self.run_button.pack(side=tk.LEFT, padx=5)

        # Toggle between histogram and curve view
        self.show_curves = True
        self.view_toggle = ttk.Button(control_frame, text="切换为直方图", command=self.toggle_view)
        self.view_toggle.pack(side=tk.LEFT, padx=5)

        self.save_button = ttk.Button(control_frame, text="Save to SVG", command=self.save_to_svg, state=tk.DISABLED)
        self.save_button.pack(side=tk.LEFT, padx=5)

        # Vertical paned window: plot (top) + statistics table (bottom)
        self.results_paned_window = ttk.PanedWindow(self.main, orient=tk.VERTICAL)
        self.results_paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.plot_frame = ttk.Frame(self.results_paned_window)
        self.results_paned_window.add(self.plot_frame, weight=7)

        self.table_frame = ttk.Frame(self.results_paned_window)
        self.results_paned_window.add(self.table_frame, weight=3)

        self.fig = None
        self.canvas = None
        self.data_tree = None
        self.progress_manager = ProgressManager(self.main)

        self.results_by_persona = {}
        self._plot_empty()

    def _plot_empty(self):
        self.fig, ax = plt.subplots(figsize=(8, 6))
        ax.set_title(self.title)
        ax.set_xlabel('Mahalanobis Distance')
        ax.set_ylabel('Probability Density')
        ax.grid(True, linestyle='--', alpha=0.6)
        self.fig.tight_layout()
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.canvas.draw()

    def _persona_dirs(self):
        if not os.path.isdir(self.data_dir):
            return []
        dirs = [d for d in os.listdir(self.data_dir)
                if os.path.isdir(os.path.join(self.data_dir, d)) and d.startswith('persona')]
        dirs.sort(key=lambda x: int(x.replace('persona', '')) if x.replace('persona', '').isdigit() else 0)
        return dirs

    def start_analysis(self):
        persona_dirs = self._persona_dirs()
        if not persona_dirs:
            messagebox.showerror("错误", f"在 '{self.data_dir}' 中找不到任何 persona 目录。")
            return

        def analysis_task(progress_dialog):
            total_personas = len(persona_dirs)
            results_by_persona = {}
            for i, persona_dir in enumerate(persona_dirs):
                persona_num = persona_dir.replace('persona', '')
                progress_dialog.update_message(f"正在计算 Persona {persona_num}...")
                results_by_persona[f'persona{persona_num}'] = self._calculate_persona_results(
                    persona_dir, progress_dialog, i / total_personas * 100, 100 / total_personas)
                if progress_dialog.is_cancelled():
                    return None
            return results_by_persona

        def on_success(results):
            if results:
                self.results_by_persona = results
                self.display_results()

        def on_error(error):
            messagebox.showerror("分析错误", f"发生错误: {error}")

        self.progress_manager.run_with_progress(
            analysis_task,
            title="多数据源分析中...",
            message="正在准备分析...",
            success_callback=on_success,
            error_callback=on_error
        )

    def _calculate_persona_results(self, persona_dir, progress_dialog, progress_start, progress_range):
        """Calculate Mahalanobis distances for each method of one persona, using a common
        (global) mean/covariance reference so distances are comparable across sources."""
        persona_path = os.path.join(self.data_dir, persona_dir)
        data_sources = []
        for method in self.methods:
            db_path = os.path.join(persona_path, f'{method}.db')
            if os.path.exists(db_path):
                data_sources.append((method, db_path))

        all_data = []
        all_labels = []
        total = len(data_sources)

        for i, (method, db_path) in enumerate(data_sources):
            if not os.path.exists(db_path):
                raise FileNotFoundError(f"数据库文件不存在: {db_path}")
            df = load_personality_data(db_path, table=self.table, columns=self.traits)
            vectors = df[self.traits].values
            all_data.append(vectors)
            all_labels.extend([method] * len(vectors))
            progress_dialog.set_progress(progress_start + (i + 1) / total * progress_range / 2)

        combined = np.vstack(all_data)
        global_mean = np.mean(combined, axis=0)
        global_cov = np.cov(combined, rowvar=False)
        global_inv_cov = np.linalg.pinv(global_cov)

        results = {}
        for i, ((method, db_path), data) in enumerate(zip(data_sources, all_data)):
            progress_dialog.update_message(f"正在计算 {persona_dir}/{method} 的距离...")
            delta = data - global_mean
            distances = np.sqrt(np.sum((delta @ global_inv_cov) * delta, axis=1))
            distances_clean = self._remove_outliers_iqr(distances)
            cv, kurtosis = self._calculate_statistical_metrics(distances_clean)
            results[method] = {
                'distances': distances,
                'distances_clean': distances_clean,
                'cv': cv,
                'kurtosis': kurtosis,
                'color': self.color_scheme.get(method, 'gray'),
                'label': method.capitalize(),
            }
            progress_dialog.set_progress(progress_start + 50 + (i + 1) / total * progress_range / 2)

        return results

    def _remove_outliers_iqr(self, data):
        if len(data) < 4:
            return data
        q1 = np.percentile(data, 25)
        q3 = np.percentile(data, 75)
        iqr = q3 - q1
        return data[(data >= q1 - 1.5 * iqr) & (data <= q3 + 1.5 * iqr)]

    def _calculate_statistical_metrics(self, data):
        if len(data) < 2:
            return 0.0, 0.0
        mean = float(np.mean(data))
        std = float(np.std(data))
        cv = std / mean if mean != 0 else 0.0
        if len(data) >= 4 and std > 0:
            kurtosis = float(np.mean(((data - mean) / std) ** 4) - 3)
        else:
            kurtosis = 0.0
        return cv, kurtosis

    def display_results(self):
        try:
            if not self.results_by_persona:
                return
            if self.canvas:
                self.canvas.get_tk_widget().destroy()
            if self.data_tree:
                self.data_tree.destroy()
                self.data_tree = None

            num_personas = len(self.results_by_persona)
            cols = min(3, num_personas)
            rows = (num_personas + cols - 1) // cols
            self.fig, axes = plt.subplots(rows, cols, figsize=(8 * cols, 6 * rows))
            self.fig.subplots_adjust(wspace=0.4, hspace=0.3)

            if num_personas == 1:
                axes_flat = [axes]
            elif rows == 1:
                axes_flat = list(axes)
            elif cols == 1:
                axes_flat = list(axes)
            else:
                axes_flat = [axes[i, j] for i in range(rows) for j in range(cols)]

            axes_flat = axes_flat[:num_personas]
            if hasattr(axes, 'flat'):
                for ax in axes.flat:
                    if ax not in axes_flat:
                        ax.set_visible(False)

            from scipy.stats import gaussian_kde

            for i, (persona_key, persona_results) in enumerate(self.results_by_persona.items()):
                ax = axes_flat[i]
                persona_num = persona_key.replace('persona', '')
                all_distances = np.concatenate([r['distances_clean'] for r in persona_results.values()])
                x_min = float(np.min(all_distances)) - 0.5
                x_max = float(np.max(all_distances)) + 0.5
                x = np.linspace(x_min, x_max, 1000)

                for method, result in persona_results.items():
                    distances = result['distances_clean']
                    color = result['color']
                    if self.show_curves:
                        if len(distances) > 1:
                            kde = gaussian_kde(distances)
                            ax.plot(x, kde(x), color=color, linewidth=2)
                            ax.fill_between(x, kde(x), alpha=0.3, color=color)
                    else:
                        ax.hist(distances, bins='auto', density=True, alpha=0.6,
                                color=color, edgecolor='black')
                ax.set_title(f'Persona {persona_num}')
                ax.set_xlabel('Mahalanobis Distance')
                ax.set_ylabel('Probability Density')
                ax.grid(True, which='both', linestyle='--', linewidth=0.5)

            self.fig.suptitle(
                'Mahalanobis Distance Distribution (KDE)' if self.show_curves
                else 'Mahalanobis Distance Distribution (Histogram)',
                fontsize=16, fontweight='bold')
            self._add_global_legend()

            self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            self.canvas.draw()

            self.display_statistics_table()
            self.save_button.config(state=tk.NORMAL)

        except Exception as e:
            messagebox.showerror("显示错误", f"显示结果时出错: {e}")

    def _add_global_legend(self):
        legend_elements = [Patch(facecolor=color, label=label.capitalize())
                           for label, color in self.color_scheme.items()]
        legend_elements.append(Patch(facecolor='white', label=''))
        if self.show_curves:
            legend_elements.append(Line2D([0], [0], color='black', label='KDE Curve', linewidth=2))
        else:
            legend_elements.append(Patch(facecolor='gray', alpha=0.6, label='Histogram'))
        self.fig.legend(handles=legend_elements, loc='lower center',
                        bbox_to_anchor=(0.5, 0.02), ncol=3, fontsize='small')
        self.fig.subplots_adjust(bottom=0.15)

    def display_statistics_table(self):
        cols = ['Persona', 'Data Source', 'Variation Coefficient', 'Kurtosis', 'Sample Count']
        self.data_tree = ttk.Treeview(self.table_frame, columns=cols, show='headings', height=10)
        for col in cols:
            self.data_tree.heading(col, text=col)
            self.data_tree.column(col, width=100, anchor='center')

        for persona_key, persona_results in self.results_by_persona.items():
            persona_num = persona_key.replace('persona', '')
            for method, result in persona_results.items():
                self.data_tree.insert('', 'end', values=(
                    f'Persona {persona_num}', result['label'],
                    f"{result['cv']:.4f}", f"{result['kurtosis']:.4f}",
                    len(result['distances_clean'])))

        scrollbar = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.data_tree.yview)
        self.data_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        self.data_tree.pack(fill=tk.BOTH, expand=True)

    def toggle_view(self):
        self.show_curves = not self.show_curves
        self.view_toggle.config(text="切换为直方图" if self.show_curves else "切换为曲线")
        if self.results_by_persona:
            self.display_results()

    def save_to_svg(self):
        if self.fig is None:
            messagebox.showwarning("No Plot", "Please run analysis first to generate a plot.")
            return
        file_path = filedialog.asksaveasfilename(
            title="Save Plot as SVG", defaultextension=".svg",
            filetypes=[("SVG Files", "*.svg"), ("All Files", "*.*")])
        if file_path:
            self.fig.savefig(file_path, format="svg", bbox_inches="tight")
            messagebox.showinfo("Success", f"Plot saved successfully to:\n{file_path}")

    def set_language(self, lang):
        pass

    def setData(self, data, update_callback):
        pass
