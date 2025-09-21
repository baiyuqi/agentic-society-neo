import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Patch

from asociety.personality.analysis_utils import calculate_single_profile_mahalanobis
from studio.progress_dialog import ProgressManager

class MultiMahalanobisPanel:
    def __init__(self, parent):
        self.main = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)
        
        main_content_frame = ttk.Frame(self.main)
        self.main.add(main_content_frame, weight=3)
        
        # Control frame
        control_frame = ttk.Frame(main_content_frame)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        title_label = ttk.Label(control_frame, text="多数据源马氏距离对比分析", font=("Helvetica", 14, "bold"))
        title_label.pack(pady=10)
        
        # Create horizontal frame for buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(pady=5)
        
        self.run_button = ttk.Button(button_frame, text="运行分析", command=self.start_analysis)
        self.run_button.pack(side=tk.LEFT, padx=5)
        
        # Toggle between histogram and curve view
        self.show_curves = True  # Default to curves
        self.view_toggle = ttk.Button(button_frame, text="切换为直方图", command=self.toggle_view)
        self.view_toggle.pack(side=tk.LEFT, padx=5)
        
        # Toggle Narrative dataset display
        self.show_narrative = True  # Default to showing narrative
        self.narrative_toggle = ttk.Button(button_frame, text="隐藏 Narrative", command=self.toggle_narrative)
        self.narrative_toggle.pack(side=tk.LEFT, padx=5)
        
        # SVG export button
        self.save_button = ttk.Button(button_frame, text="Save to SVG", command=self.save_to_svg, state=tk.DISABLED)
        self.save_button.pack(side=tk.LEFT, padx=5)
        
        self.data_source_templates = [
            {
                'name': 'poor300',
                'template': 'data/db/backup/poor300/deepseek-chat-single-poor-{}-300.db',
                'color': 'red',
                'label': 'Poor Quality'
            },
            {
                'name': 'samples300', 
                'template': 'data/db/backup/samples300/deepseek-chat-single-{}-300.db',
                'color': 'blue',
                'label': 'Standard Sample'
            },
            {
                'name': 'narrative300',
                'template': 'data/db/backup/samples-narrative300/deepseek-chat-single-{}-300-narra.db',
                'color': 'green', 
                'label': 'Narrative'
            }
        ]
        
        # Initialize data sources with current persona
        # Initialize data sources for both personas separately
        self.data_sources_persona1 = self._update_data_sources_paths("1")
        self.data_sources_persona2 = self._update_data_sources_paths("2")
        self.data_sources = self.data_sources_persona1 + self.data_sources_persona2
        
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

    def start_analysis(self):
        def analysis_task(progress_dialog):
            results_persona1 = {}
            results_persona2 = {}

            # Calculate for persona1 using original logic (all data sources including narrative)
            progress_dialog.update_message("正在计算Persona 1...")
            results_persona1 = self._calculate_persona_results(self.data_sources_persona1, progress_dialog, 0, 50)

            # Calculate for persona2 using original logic (all data sources including narrative)
            progress_dialog.update_message("正在计算Persona 2...")
            results_persona2 = self._calculate_persona_results(self.data_sources_persona2, progress_dialog, 50, 50)

            return {'persona1': results_persona1, 'persona2': results_persona2}

        def on_success(results):
            if results:
                self.results_persona1 = results['persona1']
                self.results_persona2 = results['persona2']
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

    def display_results(self):
        try:
            # Check if we have results to display
            if not hasattr(self, 'results_persona1') or not self.results_persona1 or not hasattr(self, 'results_persona2') or not self.results_persona2:
                return

            # Clear previous plot
            if self.canvas:
                self.canvas.get_tk_widget().destroy()
            if self.data_tree:
                self.data_tree.destroy()

            # Create figure with 2 subplots
            self.fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
            
            if self.show_curves:
                # Plot smooth distribution curves for each dataset
                from scipy.stats import gaussian_kde

                # Plot persona1 results on first subplot
                filtered_results_p1 = {}
                for source_name, result in self.results_persona1.items():
                    if self.show_narrative or 'narrative' not in source_name.lower():
                        filtered_results_p1[source_name] = result

                # Determine common x-range for persona1 curves
                all_distances_p1 = np.concatenate([result['distances_clean'] for result in filtered_results_p1.values()])
                x_min_p1 = np.min(all_distances_p1) - 0.5
                x_max_p1 = np.max(all_distances_p1) + 0.5
                x_p1 = np.linspace(x_min_p1, x_max_p1, 1000)

                for source_name, result in filtered_results_p1.items():
                    distances = result['distances_clean']
                    color = result['color']
                    label = result['label']

                    # Create kernel density estimate for smooth curve
                    if len(distances) > 1:
                        kde = gaussian_kde(distances)
                        y = kde(x_p1)

                        # Plot smooth curve
                        ax1.plot(x_p1, y, color=color, linewidth=2, label=label)

                        # Fill under curve for better visibility
                        ax1.fill_between(x_p1, y, alpha=0.3, color=color)

                ax1.set_title('Persona 1 - Mahalanobis Distance Distribution (KDE)')
                ax1.legend()

                # Plot persona2 results on second subplot
                filtered_results_p2 = {}
                for source_name, result in self.results_persona2.items():
                    if self.show_narrative or 'narrative' not in source_name.lower():
                        filtered_results_p2[source_name] = result

                # Determine common x-range for persona2 curves
                all_distances_p2 = np.concatenate([result['distances_clean'] for result in filtered_results_p2.values()])
                x_min_p2 = np.min(all_distances_p2) - 0.5
                x_max_p2 = np.max(all_distances_p2) + 0.5
                x_p2 = np.linspace(x_min_p2, x_max_p2, 1000)

                for source_name, result in filtered_results_p2.items():
                    distances = result['distances_clean']
                    color = result['color']
                    label = result['label']

                    # Create kernel density estimate for smooth curve
                    if len(distances) > 1:
                        kde = gaussian_kde(distances)
                        y = kde(x_p2)

                        # Plot smooth curve
                        ax2.plot(x_p2, y, color=color, linewidth=2, label=label)

                        # Fill under curve for better visibility
                        ax2.fill_between(x_p2, y, alpha=0.3, color=color)

                ax2.set_title('Persona 2 - Mahalanobis Distance Distribution (KDE)')
                ax2.legend()
            else:
                # Plot histograms for each dataset
                legend_elements_p1 = []
                legend_elements_p2 = []

                # Plot persona1 histograms on first subplot
                filtered_results_p1 = {}
                for source_name, result in self.results_persona1.items():
                    if self.show_narrative or 'narrative' not in source_name.lower():
                        filtered_results_p1[source_name] = result

                for source_name, result in filtered_results_p1.items():
                    distances = result['distances_clean']
                    color = result['color']
                    label = result['label']

                    # Plot histogram
                    counts, bin_edges, _ = ax1.hist(
                        distances, bins='auto', density=True, alpha=0.6,
                        color=color, edgecolor='black', label=label
                    )

                    legend_elements_p1.append(Patch(color=color, label=label))

                ax1.set_title('Persona 1 - Mahalanobis Distance Distribution (Histogram)')
                ax1.legend(handles=legend_elements_p1)

                # Plot persona2 histograms on second subplot
                filtered_results_p2 = {}
                for source_name, result in self.results_persona2.items():
                    if self.show_narrative or 'narrative' not in source_name.lower():
                        filtered_results_p2[source_name] = result

                for source_name, result in filtered_results_p2.items():
                    distances = result['distances_clean']
                    color = result['color']
                    label = result['label']

                    # Plot histogram
                    counts, bin_edges, _ = ax2.hist(
                        distances, bins='auto', density=True, alpha=0.6,
                        color=color, edgecolor='black', label=label
                    )

                    legend_elements_p2.append(Patch(color=color, label=label))

                ax2.set_title('Persona 2 - Mahalanobis Distance Distribution (Histogram)')
                ax2.legend(handles=legend_elements_p2)
            
            # Configure both subplots
            for ax_sub in [ax1, ax2]:
                ax_sub.set_xlabel('Mahalanobis Distance')
                ax_sub.set_ylabel('Probability Density')
                ax_sub.grid(True, which='both', linestyle='--', linewidth=0.5)
            
            # Add statistical annotations for persona1
            stats_text_p1 = []
            for source_name, result in self.results_persona1.items():
                if self.show_narrative or 'narrative' not in source_name.lower():
                    stats_text_p1.append(
                        f"{result['label']}: CV={result['cv']:.3f}, Kurtosis={result['kurtosis']:.3f}"
                    )

            # Add text box with statistics for persona1
            stats_str_p1 = '\n'.join(stats_text_p1)
            ax1.text(0.02, 0.98, stats_str_p1, transform=ax1.transAxes, fontsize=8,
                   verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

            # Add statistical annotations for persona2
            stats_text_p2 = []
            for source_name, result in self.results_persona2.items():
                if self.show_narrative or 'narrative' not in source_name.lower():
                    stats_text_p2.append(
                        f"{result['label']}: CV={result['cv']:.3f}, Kurtosis={result['kurtosis']:.3f}"
                    )

            # Add text box with statistics for persona2
            stats_str_p2 = '\n'.join(stats_text_p2)
            ax2.text(0.02, 0.98, stats_str_p2, transform=ax2.transAxes, fontsize=8,
                   verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
            
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
        cols = ['Persona', 'Data Source', 'Variation Coefficient', 'Kurtosis', 'Sample Count']
        self.data_tree = ttk.Treeview(self.table_frame, columns=cols, show='headings', height=10)

        for col in cols:
            self.data_tree.heading(col, text=col)
            self.data_tree.column(col, width=100, anchor='center')

        # Add data for persona1 (respect narrative toggle)
        for source_name, result in self.results_persona1.items():
            if self.show_narrative or 'narrative' not in source_name.lower():
                self.data_tree.insert('', 'end', values=(
                    'Persona 1',
                    result['label'],
                    f"{result['cv']:.4f}",
                    f"{result['kurtosis']:.4f}",
                    len(result['distances_clean'])
                ))

        # Add data for persona2 (respect narrative toggle)
        for source_name, result in self.results_persona2.items():
            if self.show_narrative or 'narrative' not in source_name.lower():
                self.data_tree.insert('', 'end', values=(
                    'Persona 2',
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
            self.view_toggle.config(text="切换为直方图")
        else:
            self.view_toggle.config(text="切换为曲线")
        
        # Redisplay results with new view mode
        if (hasattr(self, 'results_persona1') and self.results_persona1 and
            hasattr(self, 'results_persona2') and self.results_persona2):
            self.display_results()

    def toggle_narrative(self):
        """Toggle Narrative dataset display"""
        self.show_narrative = not self.show_narrative
        if self.show_narrative:
            self.narrative_toggle.config(text="隐藏 Narrative")
        else:
            self.narrative_toggle.config(text="显示 Narrative")

        # Redisplay results with new narrative setting
        if (hasattr(self, 'results_persona1') and self.results_persona1 and
            hasattr(self, 'results_persona2') and self.results_persona2):
            self.display_results()

    def _calculate_persona_results(self, data_sources, progress_dialog, progress_start, progress_range):
        """Calculate results for a single persona using original logic"""
        results = {}
        total_sources = len(data_sources)

        # First load all data to calculate common statistics (including narrative)
        all_data = []
        all_labels = []

        for i, source in enumerate(data_sources):
            if not os.path.exists(source['path']):
                raise FileNotFoundError(f"数据库文件不存在: {source['path']}")

            # Load personality data
            from asociety.personality.analysis_utils import load_personality_data
            df = load_personality_data(source['path'])
            trait_columns = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']
            vectors = df[trait_columns].values

            all_data.append(vectors)
            all_labels.extend([source['label']] * len(vectors))

            progress = progress_start + (i + 1) / total_sources * progress_range / 2  # 50% for loading
            progress_dialog.set_progress(progress)

        # Combine all data and calculate common statistics (including narrative)
        combined_data = np.vstack(all_data)
        global_mean = np.mean(combined_data, axis=0)
        global_cov = np.cov(combined_data, rowvar=False)

        # Add regularization to ensure invertibility
        regularization = 1e-6
        global_cov += np.eye(global_cov.shape[0]) * regularization
        global_inv_cov = np.linalg.inv(global_cov)

        # Now calculate Mahalanobis distances using common reference
        for i, (source, data) in enumerate(zip(data_sources, all_data)):
            progress_dialog.update_message(f"正在计算 {source['label']} 的距离...")

            if progress_dialog.is_cancelled():
                return None

            # Calculate Mahalanobis distances relative to global distribution
            delta = data - global_mean
            mahalanobis_sq_dist = np.sum((delta @ global_inv_cov) * delta, axis=1)
            distances = np.sqrt(mahalanobis_sq_dist)

            # Remove outliers and calculate statistics
            distances_clean = self._remove_outliers_iqr(distances)
            cv, kurtosis = self._calculate_statistical_metrics(distances_clean)

            results[source['name']] = {
                'distances': distances,
                'distances_clean': distances_clean,
                'cv': cv,
                'kurtosis': kurtosis,
                'color': source['color'],
                'label': source['label']
            }

            progress = progress_start + 50 + (i + 1) / total_sources * progress_range / 2  # Remaining 50% for calculation
            progress_dialog.set_progress(progress)

        return results

    def _update_data_sources_paths(self, persona_number):
        """Update data source paths with the selected persona number"""
        updated_sources = []
        for template in self.data_source_templates:
            updated_source = template.copy()
            updated_source['path'] = template['template'].format(persona_number)
            updated_sources.append(updated_source)
        return updated_sources

    def set_language(self, lang):
        pass

    def setData(self, data, update_callback):
        pass

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