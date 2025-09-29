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

        # SVG export button
        self.save_button = ttk.Button(button_frame, text="Save to SVG", command=self.save_to_svg, state=tk.DISABLED)
        self.save_button.pack(side=tk.LEFT, padx=5)
        
        self.data_source_templates = self._get_individual_data_sources()

        # Initialize data sources - all sources are already configured with full paths
        self.data_sources = self._update_data_sources_paths("")
        
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
            # Group data sources by persona
            persona_groups = {}
            for source in self.data_sources:
                persona_num = source.get('persona', 'unknown')
                if persona_num not in persona_groups:
                    persona_groups[persona_num] = []
                persona_groups[persona_num].append(source)

            # Calculate results for each persona
            results_by_persona = {}
            total_personas = len(persona_groups)

            for i, (persona_num, sources) in enumerate(persona_groups.items()):
                progress_dialog.update_message(f"正在计算Persona {persona_num}...")
                progress_start = i / total_personas * 100
                progress_range = 100 / total_personas

                results_by_persona[f'persona{persona_num}'] = self._calculate_persona_results(
                    sources, progress_dialog, progress_start, progress_range
                )

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

    def display_results(self):
        try:
            # Check if we have results to display
            if not hasattr(self, 'results_by_persona') or not self.results_by_persona:
                return

            # Clear previous plot
            if self.canvas:
                self.canvas.get_tk_widget().destroy()
            if self.data_tree:
                self.data_tree.destroy()

            # Create figure with fixed subplot sizes using GridSpec
            num_personas = len(self.results_by_persona)

            # Calculate grid dimensions
            cols = min(3, num_personas)  # Max 3 columns per row
            rows = (num_personas + cols - 1) // cols  # Ceiling division

            self.fig, axes = plt.subplots(rows, cols, figsize=(8 * cols, 6 * rows))

            # Adjust spacing between subplots to prevent text overlap
            self.fig.subplots_adjust(wspace=0.4, hspace=0.3)

            # Create flat list of axes for easier iteration
            axes_flat = []
            if rows == 1 and cols == 1:
                # Single subplot
                axes_flat = [axes]
            elif rows == 1:
                # Single row of subplots
                axes_flat = list(axes)
            elif cols == 1:
                # Single column of subplots
                axes_flat = list(axes)
            else:
                # Grid of subplots
                for i in range(rows):
                    for j in range(cols):
                        axes_flat.append(axes[i, j])

            # Remove axes beyond the number of personas and hide empty subplots
            axes_flat = axes_flat[:num_personas]

            # Hide subplots that don't have data
            for ax in axes_flat:
                ax.set_visible(True)

            # Hide empty subplots in the grid
            if hasattr(axes, 'flat'):
                for ax in axes.flat:
                    if ax not in axes_flat:
                        ax.set_visible(False)
            
            if self.show_curves:
                # Plot smooth distribution curves for each dataset
                from scipy.stats import gaussian_kde

                # Plot results for each persona
                for i, (persona_key, persona_results) in enumerate(self.results_by_persona.items()):
                    ax = axes_flat[i]
                    persona_num = persona_key.replace('persona', '')

                    # Determine common x-range for curves
                    all_distances = np.concatenate([result['distances_clean'] for result in persona_results.values()])
                    x_min = np.min(all_distances) - 0.5
                    x_max = np.max(all_distances) + 0.5
                    x = np.linspace(x_min, x_max, 1000)

                    for source_name, result in persona_results.items():
                        distances = result['distances_clean']
                        color = result['color']

                        # Create kernel density estimate for smooth curve
                        if len(distances) > 1:
                            kde = gaussian_kde(distances)
                            y = kde(x)

                            # Plot smooth curve
                            ax.plot(x, y, color=color, linewidth=2)

                            # Fill under curve for better visibility
                            ax.fill_between(x, y, alpha=0.3, color=color)

                    ax.set_title(f'Persona {persona_num}')
            else:
                # Plot histograms for each dataset
                # Plot results for each persona
                for i, (persona_key, persona_results) in enumerate(self.results_by_persona.items()):
                    ax = axes_flat[i]
                    persona_num = persona_key.replace('persona', '')

                    for source_name, result in persona_results.items():
                        distances = result['distances_clean']
                        color = result['color']

                        # Plot histogram
                        counts, bin_edges, _ = ax.hist(
                            distances, bins='auto', density=True, alpha=0.6,
                            color=color, edgecolor='black'
                        )

                    ax.set_title(f'Persona {persona_num}')
            
            # Add main title
            if self.show_curves:
                self.fig.suptitle('Mahalanobis Distance Distribution (KDE)', fontsize=16, fontweight='bold')
            else:
                self.fig.suptitle('Mahalanobis Distance Distribution (Histogram)', fontsize=16, fontweight='bold')

            # Configure all subplots
            for ax_sub in axes_flat:
                if ax_sub is not None:
                    ax_sub.set_xlabel('Mahalanobis Distance')
                    ax_sub.set_ylabel('Probability Density')
                    ax_sub.grid(True, which='both', linestyle='--', linewidth=0.5)

            
            # 添加总的图例
            self._add_global_legend()

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

        # Add data for each persona
        for persona_key, persona_results in self.results_by_persona.items():
            persona_num = persona_key.replace('persona', '')
            for source_name, result in persona_results.items():
                self.data_tree.insert('', 'end', values=(
                    f'Persona {persona_num}',
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
        if hasattr(self, 'results_by_persona') and self.results_by_persona:
            self.display_results()


    def _calculate_persona_results(self, data_sources, progress_dialog, progress_start, progress_range):
        """Calculate results for a single persona using original logic"""
        results = {}
        total_sources = len(data_sources)

        # First load all data to calculate common statistics
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

        # Combine all data and calculate common statistics
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

    def _get_individual_data_sources(self):
        """Get data sources from individual directory structure (excluding narrative)"""
        individual_dir = "data/db/backup/individual"
        data_sources = []

        # Define color scheme for different dataset types (no narrative)
        color_scheme = {
            'poor': 'red',
            'standard': 'blue'
        }

        # Find all persona subdirectories
        persona_dirs = []
        if os.path.exists(individual_dir):
            for item in os.listdir(individual_dir):
                item_path = os.path.join(individual_dir, item)
                if os.path.isdir(item_path) and item.startswith('persona'):
                    persona_dirs.append(item)

        # Sort persona directories numerically
        persona_dirs.sort(key=lambda x: int(x.replace('persona', '')) if x.replace('persona', '').isdigit() else 0)

        # Create data sources for each persona and dataset type (excluding narrative)
        for persona_dir in persona_dirs:
            persona_path = os.path.join(individual_dir, persona_dir)
            persona_num = persona_dir.replace('persona', '')

            # Find all database files in this persona directory (excluding narrative)
            for db_file in os.listdir(persona_path):
                if db_file.endswith('.db'):
                    dataset_type = db_file.replace('.db', '')
                    # Skip narrative datasets completely
                    if dataset_type == 'narrative':
                        continue

                    db_path = os.path.join(persona_path, db_file)

                    # Determine color based on dataset type
                    color = color_scheme.get(dataset_type, 'gray')

                    # Create unique name and label
                    source_name = f"{persona_dir}_{dataset_type}"
                    label = f"Persona {persona_num} - {dataset_type.capitalize()}"

                    data_sources.append({
                        'name': source_name,
                        'template': db_path,  # Use full path as template
                        'color': color,
                        'label': label,
                        'persona': persona_num,
                        'dataset_type': dataset_type
                    })

        return data_sources

    def _update_data_sources_paths(self, persona_number):
        """Update data source paths with the selected persona number"""
        updated_sources = []
        for template in self.data_source_templates:
            updated_source = template.copy()
            # For individual data sources, we already have the full path
            updated_source['path'] = template['template']
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

    def _add_global_legend(self):
        """Add a global legend to the figure"""
        # Create legend elements
        legend_elements = []

        # Dataset type color legend (no narrative)
        color_scheme = {
            'poor': 'red',
            'standard': 'blue'
        }

        for dataset_type, color in color_scheme.items():
            legend_elements.append(Patch(facecolor=color, label=dataset_type.capitalize()))

        # Add separator
        legend_elements.append(Patch(facecolor='white', label=''))

        # View mode legend
        if self.show_curves:
            legend_elements.append(Line2D([0], [0], color='black', label='KDE Curve', linewidth=2))
        else:
            legend_elements.append(Patch(facecolor='gray', alpha=0.6, label='Histogram'))

        # Add legend to figure
        self.fig.legend(handles=legend_elements, loc='lower center',
                       bbox_to_anchor=(0.5, 0.02), ncol=3, fontsize='small')
        # Adjust layout to accommodate legend
        self.fig.subplots_adjust(bottom=0.15)