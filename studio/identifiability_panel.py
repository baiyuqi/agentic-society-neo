import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Patch
from scipy.spatial.distance import euclidean

from asociety.personality.analysis_utils import (
    load_profiles_from_directory,
    get_combined_and_scaled_data,
    run_kmeans_analysis,
    run_pca
)
from studio.progress_dialog import ProgressManager

class IdentifiabilityPanel:
    def __init__(self, parent):
        self.main = ttk.Frame(parent)
        self.main.pack(fill=tk.BOTH, expand=True)

        # --- Top Control Frame ---
        control_frame = ttk.Frame(self.main)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        title_label = ttk.Label(control_frame, text="Identifiability Analysis: Comparing Standard Samples vs Poor Samples", font=("Helvetica", 14, "bold"))
        title_label.pack(side=tk.LEFT, padx=(0, 20))

        self.run_button = ttk.Button(control_frame, text="Run Analysis", command=self.start_analysis)
        self.run_button.pack(side=tk.LEFT, padx=(0, 10))

        self.save_button = ttk.Button(control_frame, text="Save to SVG", command=self.save_to_svg, state=tk.DISABLED)
        self.save_button.pack(side=tk.LEFT)

        # --- Main Paned Window for Plot and Table ---
        self.main_paned = ttk.PanedWindow(self.main, orient=tk.VERTICAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # --- Plot Frame (Top 70%) ---
        self.plot_frame = ttk.Frame(self.main_paned)
        self.main_paned.add(self.plot_frame, weight=7)

        # ARI labels frame
        ari_frame = ttk.Frame(self.plot_frame)
        ari_frame.pack(fill=tk.X, pady=(0, 10))

        self.ari_label_samples = ttk.Label(ari_frame, text="Standard Samples ARI: -", font=("Helvetica", 10, "bold"))
        self.ari_label_samples.pack(side=tk.LEFT, padx=(0, 20))

        self.ari_label_poor = ttk.Label(ari_frame, text="Poor Samples ARI: -", font=("Helvetica", 10, "bold"))
        self.ari_label_poor.pack(side=tk.LEFT)

        # Single figure with subplots and proper aspect ratio
        self.fig, (self.ax_samples, self.ax_poor) = plt.subplots(1, 2, figsize=(14, 6))
        # Set aspect ratio for PCA plots - use "auto" for better visualization
        self.ax_samples.set_aspect("auto")
        self.ax_poor.set_aspect("auto")
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        # Use constrained layout to maintain proper proportions
        self.fig.set_constrained_layout(True)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # --- Table Frame (Bottom 30%) ---
        self.table_frame = ttk.Frame(self.main_paned)
        self.main_paned.add(self.table_frame, weight=3)
        self.data_tree = None

        self.progress_manager = ProgressManager(self.main)

    def start_analysis(self):
        # Get persona pairs from individual directory
        persona_pairs = self._get_persona_pairs()

        if not persona_pairs:
            messagebox.showerror("Error", "No valid persona pairs found in individual directory.")
            return

        # --- Analysis Task Definition ---
        def analysis_task(progress_dialog):
            results = {}
            total_pairs = len(persona_pairs)

            for i, (persona1, persona2) in enumerate(persona_pairs):
                progress_dialog.update_message(f"Analyzing pair {persona1}-{persona2}...")

                # Analyze poor samples for this pair
                poor_results = self._run_pair_analysis(persona1, persona2, 'poor')
                if progress_dialog.is_cancelled(): return None

                # Analyze standard samples for this pair
                standard_results = self._run_pair_analysis(persona1, persona2, 'standard')
                if progress_dialog.is_cancelled(): return None

                results[f"{persona1}_{persona2}"] = {
                    'poor': poor_results,
                    'standard': standard_results
                }

                progress_dialog.set_progress((i + 1) / total_pairs * 100)

            return results

        # --- Callbacks ---
        def on_success(results):
            if results:
                self.display_results(results)
                # Enable save button and redraw canvas
                self.save_button.config(state=tk.NORMAL)
                self.canvas.draw()

        def on_error(error):
            messagebox.showerror("Analysis Error", f"An error occurred: {error}")

        self.progress_manager.run_with_progress(
            analysis_task,
            title="Identifiability Analysis",
            message="Preparing...",
            success_callback=on_success,
            error_callback=on_error
        )

    def _run_single_analysis(self, directory):
        """Runs the clustering analysis for a single directory."""
        profile_dataframes, profile_names = load_profiles_from_directory(directory)
        if not profile_dataframes:
            raise ValueError(f"No valid database files found in directory {directory}.")
            
        scaled_vectors, true_labels = get_combined_and_scaled_data(profile_dataframes)
        num_profiles = len(profile_dataframes)
        predicted_labels, ari_score = run_kmeans_analysis(scaled_vectors, true_labels, num_profiles)
        principal_components, explained_variance = run_pca(scaled_vectors)
        
        return {
            'profile_names': profile_names,
            'ari_score': ari_score,
            'principal_components': principal_components,
            'explained_variance': explained_variance,
            'true_labels': true_labels,
            'predicted_labels': predicted_labels
        }


    def set_language(self, lang):
        pass

    def setData(self, data, update_callback):
        # Panel is self-contained, does not need external data
        pass

    def _get_persona_pairs(self):
        """Get persona pairs: (1,2), (2,3), ..., (n-1,n), (n,1)"""
        individual_dir = "data/db/backup/individual"
        persona_dirs = []

        if os.path.exists(individual_dir):
            for item in os.listdir(individual_dir):
                item_path = os.path.join(individual_dir, item)
                if os.path.isdir(item_path) and item.startswith('persona'):
                    persona_dirs.append(item)

        # Sort persona directories numerically
        persona_dirs.sort(key=lambda x: int(x.replace('persona', '')) if x.replace('persona', '').isdigit() else 0)

        if len(persona_dirs) < 2:
            return []

        # Extract persona numbers
        persona_nums = [int(p.replace('persona', '')) for p in persona_dirs]

        # Create pairs: (1,2), (2,3), ..., (n-1,n), (n,1)
        pairs = []
        for i in range(len(persona_nums)):
            persona1 = persona_nums[i]
            persona2 = persona_nums[(i + 1) % len(persona_nums)]
            pairs.append((persona1, persona2))

        return pairs

    def _run_pair_analysis(self, persona1, persona2, dataset_type):
        """Run analysis for a specific persona pair and dataset type"""
        # Load data from both personas for the given dataset type
        dir1 = f"data/db/backup/individual/persona{persona1}"
        dir2 = f"data/db/backup/individual/persona{persona2}"

        # Find the database file for the specified dataset type
        db_files = []
        for dir_path in [dir1, dir2]:
            if os.path.exists(dir_path):
                for file in os.listdir(dir_path):
                    if file.endswith('.db') and file.replace('.db', '') == dataset_type:
                        db_files.append(os.path.join(dir_path, file))

        if len(db_files) != 2:
            raise ValueError(f"Could not find {dataset_type} databases for personas {persona1} and {persona2}")

        # Load and combine data from both personas
        profile_dataframes = []
        profile_names = []

        from asociety.personality.analysis_utils import load_personality_data

        for i, db_file in enumerate(db_files):
            df = load_personality_data(db_file)
            profile_dataframes.append(df)
            profile_names.append(f"Persona {persona1 if i == 0 else persona2}")

        # Run the analysis
        scaled_vectors, true_labels = get_combined_and_scaled_data(profile_dataframes)
        num_profiles = len(profile_dataframes)
        kmeans, predicted_labels, ari_score = run_kmeans_analysis(scaled_vectors, true_labels, num_profiles, return_model=True)
        principal_components, explained_variance = run_pca(scaled_vectors)

        # Calculate centroid distance for two clusters
        centroid_distance = 0.0
        if len(kmeans.cluster_centers_) == 2:
            centroid_distance = euclidean(kmeans.cluster_centers_[0], kmeans.cluster_centers_[1])

        return {
            'profile_names': profile_names,
            'ari_score': ari_score,
            'principal_components': principal_components,
            'explained_variance': explained_variance,
            'true_labels': true_labels,
            'predicted_labels': predicted_labels,
            'persona1': persona1,
            'persona2': persona2,
            'dataset_type': dataset_type,
            'centroid_distance': centroid_distance
        }

    def display_results(self, results):
        """Display results for all persona pairs"""
        # Clear previous plot and table
        if hasattr(self, 'canvas') and self.canvas:
            self.canvas.get_tk_widget().destroy()
        if self.data_tree:
            self.data_tree.destroy()
            self.data_tree = None

        # 统计所有点的范围，用于统一坐标轴
        all_pc1, all_pc2 = [], []
        for pair_results in results.values():
            all_pc1.extend(pair_results['poor']['principal_components'][:, 0])
            all_pc1.extend(pair_results['standard']['principal_components'][:, 0])
            all_pc2.extend(pair_results['poor']['principal_components'][:, 1])
            all_pc2.extend(pair_results['standard']['principal_components'][:, 1])

        global_xmin, global_xmax = min(all_pc1), max(all_pc1)
        global_ymin, global_ymax = min(all_pc2), max(all_pc2)

        # 给个小边距，防止点贴边
        margin_x = (global_xmax - global_xmin) * 0.05
        margin_y = (global_ymax - global_ymin) * 0.05
        self.global_xlim = (global_xmin - margin_x, global_xmax + margin_x)
        self.global_ylim = (global_ymin - margin_y, global_ymax + margin_y)

        # Create new figure with increased spacing and flatter subplots
        num_pairs = len(results)
        cols = min(5, num_pairs)  # Max 5 pairs per row
        rows = (num_pairs + cols - 1) // cols  # Ceiling division

        # Use GridSpec for better control over spacing and aspect ratio
        from matplotlib.gridspec import GridSpec

        # Create figure with increased height for 5-column layout
        self.fig = plt.figure(figsize=(6 * cols, 8 * rows))

        # Create GridSpec with reduced spacing between rows
        gs = GridSpec(rows * 2, cols, figure=self.fig,
                     hspace=0.1,  # Reduced vertical spacing between subplots
                     wspace=0.1)  # Reduced horizontal spacing

        # Create axes array for easier access
        axes = []
        for i in range(rows * 2):
            row_axes = []
            for j in range(cols):
                if i < rows * 2 and j < cols:
                    ax = self.fig.add_subplot(gs[i, j])
                    row_axes.append(ax)
                else:
                    row_axes.append(None)
            axes.append(row_axes)

        # Convert to numpy array for easier indexing
        axes = np.array(axes)

        # Plot each pair
        for i, (pair_key, pair_results) in enumerate(results.items()):
            persona1, persona2 = pair_key.split('_')

            # Calculate grid position
            row_pair = i // cols  # Which pair row (0-based)
            col_pair = i % cols   # Which column (0-based)

            # Poor subplot (top row of the pair)
            poor_row = row_pair * 2
            # Handle single subplot case
            if rows == 1 and cols == 1:
                poor_ax = axes[0, 0]
            else:
                poor_ax = axes[poor_row, col_pair]
            # Only show labels for the first subplot (poor)
            show_labels = (i == 0 and row_pair == 0 and col_pair == 0)
            self._plot_single_result(pair_results['poor'], poor_ax, f"Pair {persona1}-{persona2} - Poor", show_labels=show_labels)

            # Standard subplot (bottom row of the pair)
            standard_row = row_pair * 2 + 1
            # Handle single subplot case
            if rows == 1 and cols == 1:
                standard_ax = axes[1, 0] if rows * 2 > 1 else axes[0, 0]
            else:
                standard_ax = axes[standard_row, col_pair]
            # Never show labels for standard subplots
            self._plot_single_result(pair_results['standard'], standard_ax, f"Pair {persona1}-{persona2} - Standard", show_labels=False)

        # Set main title
        self.fig.suptitle('Identifiability Analysis: Persona Pair Comparison', fontsize=16, fontweight='bold')

        # 添加总的图例
        self._add_global_legend()

        # Create new canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Display statistics table
        self.display_statistics_table(results)

    def _plot_single_result(self, result, ax, title, show_labels=True):
        """Plot a single analysis result on the given axis"""
        ax.clear()

        plot_df = pd.DataFrame({
            'PC1': result['principal_components'][:, 0],
            'PC2': result['principal_components'][:, 1],
            'True Profile': [result['profile_names'][label] for label in result['true_labels']],
            'Predicted Cluster': [f'Cluster {label + 1}' for label in result['predicted_labels']]
        })

        # 统一样式：左侧persona用圆形，右侧persona用三角形
        persona1_name = result['profile_names'][0]
        persona2_name = result['profile_names'][1]

        # 为每个点设置统一的样式
        markers = []
        for label in result['true_labels']:
            if label == 0:  # 左侧persona
                markers.append('o')  # 圆形
            else:  # 右侧persona
                markers.append('+')  # 十字花

        plot_df['Marker'] = markers

        # 使用统一的颜色和样式
        cluster_colors = plt.cm.tab10(range(2))
        for cluster_num in set(plot_df['Predicted Cluster']):
            cluster_idx = int(cluster_num.replace('Cluster ', '')) - 1
            cluster_data = plot_df[plot_df['Predicted Cluster'] == cluster_num]
            for marker_type in ['o', '+']:
                marker_data = cluster_data[cluster_data['Marker'] == marker_type]
                if len(marker_data) > 0:
                    ax.scatter(marker_data['PC1'], marker_data['PC2'],
                             c=[cluster_colors[cluster_idx]], s=27, alpha=0.7,
                             edgecolors='black', linewidths=0.5, marker=marker_type)

        ax.set_title(f"{title}", pad=10)  # Add padding to prevent overlap

        if show_labels:
            ax.set_xlabel('PC 1', labelpad=5)   # Add padding to axis labels
            ax.set_ylabel('PC 2', labelpad=5)
        else:
            # Remove axis labels and ticks to save space
            ax.set_xlabel('')
            ax.set_ylabel('')
            ax.tick_params(axis='both', which='both', bottom=False, top=False,
                          left=False, right=False, labelbottom=False, labelleft=False)

        ax.grid(True, which='both', linestyle='--', linewidth=0.5)

        # 统一坐标范围 + 锁定纵横比
        ax.set_xlim(self.global_xlim)
        ax.set_ylim(self.global_ylim)
        ax.set_aspect(1.0, adjustable='box')  # 正方形比例 (高度:宽度 = 1:1)

    def _add_global_legend(self):
        """Add a global legend to the figure"""
        # Create legend elements
        legend_elements = []

        # Cluster colors legend - only cluster1 and cluster2
        cluster_colors = plt.cm.tab10(range(2))
        for i in range(2):
            legend_elements.append(Patch(facecolor=cluster_colors[i], label=f'Cluster {i+1}'))

        # Add separator
        legend_elements.append(Patch(facecolor='white', label=''))

        # Style legend - use Line2D to properly display markers
        from matplotlib.lines import Line2D
        legend_elements.append(Line2D([0], [0], marker='o', color='black', label='Persona 1',
                                     markersize=8, linestyle='None'))
        legend_elements.append(Line2D([0], [0], marker='+', color='black', label='Persona 2',
                                     markersize=8, linestyle='None'))

        # Add legend to figure with optimized column layout
        # For 2 personas and 2 clusters, use 2 columns for better grouping
        self.fig.legend(handles=legend_elements, loc='lower center',
                       bbox_to_anchor=(0.5, 0.01), ncol=2, fontsize='small')
        # Adjust layout to reduce edge margins
        self.fig.subplots_adjust(bottom=0.10, top=0.95, left=0.05, right=0.95)

    def display_statistics_table(self, results):
        """Display identifiability analysis results in a table"""
        # Clear previous table
        if self.data_tree:
            self.data_tree.destroy()

        # Define columns for multi-pair analysis
        columns = ['Persona Pair', 'Dataset Type', 'ARI Score', 'Centroid Distance', 'PC1 Variance', 'PC2 Variance',
                  'Sample Count']

        self.data_tree = ttk.Treeview(self.table_frame, columns=columns, show='headings', height=10)

        # Configure column headings
        for col in columns:
            self.data_tree.heading(col, text=col)

        # Set column widths
        self.data_tree.column('Persona Pair', width=120)
        self.data_tree.column('Dataset Type', width=100)
        self.data_tree.column('ARI Score', width=100)
        self.data_tree.column('Centroid Distance', width=120)
        self.data_tree.column('PC1 Variance', width=100)
        self.data_tree.column('PC2 Variance', width=100)
        self.data_tree.column('Sample Count', width=100)

        # Populate table with results
        for pair_key, pair_results in results.items():
            persona1, persona2 = pair_key.split('_')

            # Poor dataset results
            poor_results = pair_results['poor']
            self.data_tree.insert('', 'end', values=(
                f"{persona1}-{persona2}",
                'Poor',
                f"{poor_results['ari_score']:.4f}",
                f"{poor_results.get('centroid_distance', 0):.4f}",
                f"{poor_results['explained_variance'][0]:.2%}",
                f"{poor_results['explained_variance'][1]:.2%}",
                len(poor_results['true_labels'])
            ))

            # Standard dataset results
            standard_results = pair_results['standard']
            self.data_tree.insert('', 'end', values=(
                f"{persona1}-{persona2}",
                'Standard',
                f"{standard_results['ari_score']:.4f}",
                f"{standard_results.get('centroid_distance', 0):.4f}",
                f"{standard_results['explained_variance'][0]:.2%}",
                f"{standard_results['explained_variance'][1]:.2%}",
                len(standard_results['true_labels'])
            ))

        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.data_tree.yview)
        self.data_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        self.data_tree.pack(fill=tk.BOTH, expand=True)

    def save_to_svg(self):
        """Save the combined matplotlib figure as SVG vector image"""
        if self.fig is None:
            messagebox.showwarning("No Plot", "Please run analysis first to generate plots.")
            return

        file_path = filedialog.asksaveasfilename(
            title="Save Combined Plot as SVG",
            defaultextension=".svg",
            filetypes=[("SVG Files", "*.svg"), ("All Files", "*.*")]
        )

        if file_path:
            self.fig.savefig(file_path, format="svg", bbox_inches="tight")
            messagebox.showinfo("Success", f"Combined plot saved successfully to:\n{file_path}")
