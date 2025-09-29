# studio/single_density_panel.py

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

from asociety.personality.analysis_utils import calculate_single_profile_mahalanobis
from studio.progress_dialog import ProgressManager
from studio.collapsible_help_panel import CollapsibleHelpPanel
from studio.help_constants import helpcnstants

class SingleDensityPanel:
    def __init__(self, parent):
        self.main = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)

        main_content_frame = ttk.Frame(self.main)
        self.main.add(main_content_frame, weight=3)

        # Control frame
        control_frame = ttk.Frame(main_content_frame)
        control_frame.pack(fill=tk.X, padx=10, pady=10)

        # File selection controls
        file_selection_frame = ttk.Frame(control_frame)
        file_selection_frame.pack(fill=tk.X, pady=5)

        self.file_list_label = ttk.Label(file_selection_frame, text="Selected Files: None")
        self.file_list_label.pack(side=tk.LEFT, padx=(0, 10))

        add_file_button = ttk.Button(file_selection_frame, text="Add File...", command=self.add_file)
        add_file_button.pack(side=tk.LEFT, padx=(0, 10))

        clear_files_button = ttk.Button(file_selection_frame, text="Clear Files", command=self.clear_files)
        clear_files_button.pack(side=tk.LEFT, padx=(0, 10))

        # Analysis controls
        analysis_frame = ttk.Frame(control_frame)
        analysis_frame.pack(fill=tk.X, pady=5)

        self.run_button = ttk.Button(analysis_frame, text="Run Analysis", command=self.start_analysis, state=tk.DISABLED)
        self.run_button.pack(side=tk.LEFT, padx=5)

        # Toggle between histogram and curve view
        self.show_curves = True  # Default to curves
        self.view_toggle = ttk.Button(analysis_frame, text="Switch to Histogram", command=self.toggle_view)
        self.view_toggle.pack(side=tk.LEFT, padx=5)

        # SVG export button
        self.save_button = ttk.Button(analysis_frame, text="Save to SVG", command=self.save_to_svg, state=tk.DISABLED)
        self.save_button.pack(side=tk.LEFT, padx=5)

        self.selected_files = []

        # Create paned window for plot and table
        self.results_paned_window = ttk.PanedWindow(main_content_frame, orient=tk.VERTICAL)
        self.results_paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Plot frame (top 70%)
        self.plot_frame = ttk.Frame(self.results_paned_window)
        self.results_paned_window.add(self.plot_frame, weight=7)

        # Table frame (bottom 30%)
        self.table_frame = ttk.Frame(self.results_paned_window)
        self.results_paned_window.add(self.table_frame, weight=3)

        self.fig = None
        self.canvas = None
        self.data_tree = None
        self.progress_manager = ProgressManager(self.main)

        self.results = {}

        self.current_lang = 'zh'
        help_config = {"title": "单图密度分析帮助", "content": helpcnstants['single_density']['zh']}
        self.collapsible_help = CollapsibleHelpPanel(self.main, help_config, weight=1)

    def add_file(self):
        file_path = filedialog.askopenfilename(
            title='Select a persona database file',
            filetypes=[('SQLite Database', '*.db')],
            initialdir='data/db/backup'
        )
        if file_path and file_path not in self.selected_files:
            self.selected_files.append(file_path)
            self.update_file_list_label()
            self.run_button.config(state=tk.NORMAL if len(self.selected_files) >= 1 else tk.DISABLED)
            self.save_button.config(state=tk.DISABLED)
            if self.canvas:
                self.canvas.get_tk_widget().destroy()
                self.canvas = None
            if self.data_tree:
                self.data_tree.destroy()
                self.data_tree = None

    def clear_files(self):
        self.selected_files = []
        self.update_file_list_label()
        self.run_button.config(state=tk.DISABLED)
        self.save_button.config(state=tk.DISABLED)
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
            self.canvas = None
        if self.data_tree:
            self.data_tree.destroy()
            self.data_tree = None

    def update_file_list_label(self):
        if not self.selected_files:
            self.file_list_label.config(text="Selected Files: None")
        else:
            file_names = [os.path.basename(f) for f in self.selected_files]
            if len(file_names) <= 3:
                display_text = f"Selected Files: {', '.join(file_names)}"
            else:
                display_text = f"Selected Files: {len(file_names)} files ({', '.join(file_names[:3])}...)"
            self.file_list_label.config(text=display_text)

    def start_analysis(self):
        if len(self.selected_files) < 1:
            messagebox.showwarning("Insufficient Files", "Please select at least 1 file for analysis.")
            return

        self.save_button.config(state=tk.DISABLED)

        def analysis_task(progress_dialog):
            results = {}
            total_files = len(self.selected_files)

            # First load all data to calculate common statistics
            all_data = []
            all_labels = []

            progress_dialog.update_message("正在加载所有数据...")
            for i, file_path in enumerate(self.selected_files):
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"数据库文件不存在: {file_path}")

                # Load personality data
                from asociety.personality.analysis_utils import load_personality_data
                df = load_personality_data(file_path)
                trait_columns = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']
                vectors = df[trait_columns].values

                all_data.append(vectors)
                all_labels.append(os.path.basename(file_path))

                progress = (i + 1) / total_files * 50  # 50% for loading
                progress_dialog.set_progress(progress)

            # Combine all data and calculate common statistics
            combined_data = np.vstack(all_data)
            global_mean = np.mean(combined_data, axis=0)
            global_cov = np.cov(combined_data, rowvar=False)

            # Add regularization to ensure invertibility
            regularization = 1e-6
            global_cov += np.eye(global_cov.shape[0]) * regularization
            global_inv_cov = np.linalg.inv(global_cov)

            # Now calculate Mahalanobis distances using common reference
            for i, (file_path, data) in enumerate(zip(self.selected_files, all_data)):
                progress_dialog.update_message(f"正在计算 {os.path.basename(file_path)} 的距离...")

                if progress_dialog.is_cancelled():
                    return None

                # Calculate Mahalanobis distances relative to global distribution
                delta = data - global_mean
                mahalanobis_sq_dist = np.sum((delta @ global_inv_cov) * delta, axis=1)
                distances = np.sqrt(mahalanobis_sq_dist)

                # Remove outliers and calculate statistics
                distances_clean = self._remove_outliers_iqr(distances)
                cv, kurtosis = self._calculate_statistical_metrics(distances_clean)

                # Generate color based on file index
                color = plt.cm.tab10(i % 10)

                # Use full file path as key to handle duplicate filenames
                results[file_path] = {
                    'distances': distances,
                    'distances_clean': distances_clean,
                    'cv': cv,
                    'kurtosis': kurtosis,
                    'color': color,
                    'label': os.path.basename(file_path).replace('.db', ''),
                    'file_path': file_path  # Store full path for reference
                }

                progress = 50 + (i + 1) / total_files * 50  # Remaining 50% for calculation
                progress_dialog.set_progress(progress)

            return results

        def on_success(results):
            if results:
                self.results = results
                self.display_results()

        def on_error(error):
            messagebox.showerror("分析错误", f"发生错误: {error}")

        self.progress_manager.run_with_progress(
            analysis_task,
            title="单图密度分析中...",
            message="正在准备分析...",
            success_callback=on_success,
            error_callback=on_error
        )

    def display_results(self):
        try:
            # Check if we have results to display
            if not self.results:
                return

            # Clear previous plot
            if self.canvas:
                self.canvas.get_tk_widget().destroy()
            if self.data_tree:
                self.data_tree.destroy()

            # Create single figure
            self.fig, ax = plt.subplots(figsize=(12, 8))

            if self.show_curves:
                # Plot smooth distribution curves for all files in one plot
                from scipy.stats import gaussian_kde

                # Determine common x-range for curves
                all_distances = np.concatenate([result['distances_clean'] for result in self.results.values()])
                x_min = np.min(all_distances) - 0.5
                x_max = np.max(all_distances) + 0.5
                x = np.linspace(x_min, x_max, 1000)

                for file_path, result in self.results.items():
                    distances = result['distances_clean']
                    color = result['color']
                    label = result['label']

                    # Create kernel density estimate for smooth curve
                    if len(distances) > 1:
                        kde = gaussian_kde(distances)
                        y = kde(x)

                        # Plot smooth curve
                        ax.plot(x, y, color=color, linewidth=2, label=label)

                        # Fill under curve for better visibility
                        ax.fill_between(x, y, alpha=0.3, color=color)

                ax.set_title('Mahalanobis Distance Distribution (KDE)', fontsize=16, fontweight='bold')
            else:
                # Plot histograms for all files in one plot
                for file_path, result in self.results.items():
                    distances = result['distances_clean']
                    color = result['color']
                    label = result['label']

                    # Plot histogram
                    counts, bin_edges, _ = ax.hist(
                        distances, bins='auto', density=True, alpha=0.6,
                        color=color, edgecolor='black', label=label
                    )

                ax.set_title('Mahalanobis Distance Distribution (Histogram)', fontsize=16, fontweight='bold')

            # Configure plot
            ax.set_xlabel('Mahalanobis Distance')
            ax.set_ylabel('Probability Density')
            ax.grid(True, which='both', linestyle='--', linewidth=0.5)
            ax.legend()

            # Create canvas
            self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
            self.canvas.draw()
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            # Create statistics table
            self.display_statistics_table()

            # Enable SVG export
            self.save_button.config(state=tk.NORMAL)

        except Exception as e:
            messagebox.showerror("显示错误", f"显示结果时出错: {e}")

    def display_statistics_table(self):
        """Display statistics table with variation coefficient and kurtosis."""
        cols = ['File Name', 'Variation Coefficient', 'Kurtosis', 'Sample Count']
        self.data_tree = ttk.Treeview(self.table_frame, columns=cols, show='headings', height=10)

        for col in cols:
            self.data_tree.heading(col, text=col)
            self.data_tree.column(col, width=120, anchor='center')

        # Add data for each file
        for file_path, result in self.results.items():
            self.data_tree.insert('', 'end', values=(
                result['label'],
                f"{result['cv']:.4f}",
                f"{result['kurtosis']:.4f}",
                len(result['distances_clean'])
            ))

        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.data_tree.yview)
        self.data_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        self.data_tree.pack(fill=tk.BOTH, expand=True)

    def _remove_outliers_iqr(self, data):
        """Remove outliers using Interquartile Range method."""
        if len(data) < 4:
            return data

        q1 = np.percentile(data, 25)
        q3 = np.percentile(data, 75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        return data[(data >= lower_bound) & (data <= upper_bound)]

    def _calculate_statistical_metrics(self, data):
        """Calculate variation coefficient and kurtosis."""
        if len(data) < 2:
            return 0.0, 0.0

        mean = np.mean(data)
        std = np.std(data)

        # Variation coefficient
        cv = std / mean if mean != 0 else 0.0

        # Kurtosis (Fisher's definition)
        if len(data) >= 4 and std > 0:
            kurtosis = np.mean(((data - mean) / std) ** 4) - 3
        else:
            kurtosis = 0.0

        return cv, kurtosis

    def toggle_view(self):
        """Toggle between curve and histogram view"""
        self.show_curves = not self.show_curves
        if self.show_curves:
            self.view_toggle.config(text="Switch to Histogram")
        else:
            self.view_toggle.config(text="Switch to Curves")

        # Redisplay results with new view mode
        if self.results:
            self.display_results()

    def save_to_svg(self):
        """Save the current matplotlib figure as SVG vector image"""
        if self.fig is None:
            messagebox.showwarning("No Plot", "Please run analysis first to generate a plot.")
            return

        file_path = filedialog.asksaveasfilename(
            title="Save Plot as SVG",
            defaultextension=".svg",
            filetypes=[("SVG Files", "*.svg"), ("All Files", "*.*")]
        )

        if file_path:
            self.fig.savefig(file_path, format="svg", bbox_inches="tight")
            messagebox.showinfo("Success", f"Plot saved successfully to:\n{file_path}")

    def set_language(self, lang):
        self.current_lang = lang
        self.update_help_content()

    def update_help_content(self):
        title = "单图密度分析帮助" if self.current_lang == 'zh' else "Single Density Analysis Help"
        content = helpcnstants['single_density'][self.current_lang]

        if hasattr(self, 'collapsible_help'):
            self._update_collapsible_help_content(self.collapsible_help, title, content)

    def _update_collapsible_help_content(self, collapsible_help, title, content):
        if hasattr(collapsible_help, 'help_panel'):
            help_panel = collapsible_help.help_panel
            for child in help_panel.winfo_children():
                if isinstance(child, ttk.Label):
                    child.config(text=title)
                    break
            if hasattr(help_panel, 'html_widget'):
                import markdown
                html_content = markdown.markdown(content)
                help_panel.html_widget.set_html(html_content)

    def setData(self, appKey, updateTree):
        pass