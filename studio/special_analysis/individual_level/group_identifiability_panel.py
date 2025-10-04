import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

from asociety.personality.analysis_utils import (
    load_personality_data,
    get_combined_and_scaled_data,
    run_kmeans_analysis,
    run_pca
)
from studio.progress_dialog import ProgressManager

class GroupIdentifiabilityPanel:
    def __init__(self, parent):
        self.main = ttk.Frame(parent)
        self.main.pack(fill=tk.BOTH, expand=True)

        # --- Top Control Frame ---
        control_frame = ttk.Frame(self.main)
        control_frame.pack(fill=tk.X, padx=10, pady=10)

        title_label = ttk.Label(control_frame, text="Group Identifiability Analysis: Poor vs Standard Dataset Clustering", font=("Helvetica", 14, "bold"))
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

        # Single figure with subplots for poor and standard
        self.fig, (self.ax_poor, self.ax_standard) = plt.subplots(1, 2, figsize=(14, 6))
        self.ax_poor.set_aspect("auto")
        self.ax_standard.set_aspect("auto")
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.fig.set_constrained_layout(True)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # --- Table Frame (Bottom 30%) ---
        self.table_frame = ttk.Frame(self.main_paned)
        self.main_paned.add(self.table_frame, weight=3)
        self.data_tree = None

        self.progress_manager = ProgressManager(self.main)

    def start_analysis(self):
        # Get all persona directories
        persona_dirs = self._get_persona_directories()

        if not persona_dirs:
            messagebox.showerror("Error", "No valid persona directories found in individual directory.")
            return

        # --- Analysis Task Definition ---
        def analysis_task(progress_dialog):
            # Load poor datasets from all personas
            progress_dialog.update_message("Loading poor datasets...")
            poor_results = self._load_and_analyze_group(persona_dirs, 'poor', progress_dialog, 0, 50)
            if progress_dialog.is_cancelled(): return None

            # Load standard datasets from all personas
            progress_dialog.update_message("Loading standard datasets...")
            standard_results = self._load_and_analyze_group(persona_dirs, 'standard', progress_dialog, 50, 50)
            if progress_dialog.is_cancelled(): return None

            return {
                'poor': poor_results,
                'standard': standard_results
            }

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
            title="Group Identifiability Analysis",
            message="Preparing...",
            success_callback=on_success,
            error_callback=on_error
        )

    def _get_persona_directories(self):
        """Get all persona directories from individual directory"""
        individual_dir = "data/db/backup/individual"
        persona_dirs = []

        if os.path.exists(individual_dir):
            for item in os.listdir(individual_dir):
                item_path = os.path.join(individual_dir, item)
                if os.path.isdir(item_path) and item.startswith('persona'):
                    persona_dirs.append(item)

        # Sort persona directories numerically
        persona_dirs.sort(key=lambda x: int(x.replace('persona', '')) if x.replace('persona', '').isdigit() else 0)
        return persona_dirs

    def _load_and_analyze_group(self, persona_dirs, dataset_type, progress_dialog, progress_start, progress_range):
        """Load and analyze a group of datasets (poor or standard) from all personas"""
        profile_dataframes = []
        profile_names = []

        total_personas = len(persona_dirs)

        for i, persona_dir in enumerate(persona_dirs):
            persona_num = persona_dir.replace('persona', '')
            persona_path = os.path.join("data/db/backup/individual", persona_dir)

            # Find the database file for the specified dataset type
            db_file = None
            if os.path.exists(persona_path):
                for file in os.listdir(persona_path):
                    if file.endswith('.db') and file.replace('.db', '') == dataset_type:
                        db_file = os.path.join(persona_path, file)
                        break

            if db_file and os.path.exists(db_file):
                try:
                    df = load_personality_data(db_file)
                    profile_dataframes.append(df)
                    profile_names.append(f"Persona {persona_num}")
                except Exception as e:
                    print(f"Error loading {db_file}: {e}")

            progress = progress_start + (i + 1) / total_personas * progress_range
            progress_dialog.set_progress(progress)

        if not profile_dataframes:
            raise ValueError(f"No {dataset_type} datasets found")

        # Run the analysis
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
            'predicted_labels': predicted_labels,
            'dataset_type': dataset_type,
            'num_personas': num_profiles
        }

    def display_results(self, results):
        """Display results for poor and standard groups"""
        # Clear previous plot and table
        if hasattr(self, 'canvas') and self.canvas:
            self.canvas.get_tk_widget().destroy()
        if self.data_tree:
            self.data_tree.destroy()
            self.data_tree = None

        # Create new figure
        self.fig, (self.ax_poor, self.ax_standard) = plt.subplots(1, 2, figsize=(14, 6))

        # Plot poor results
        poor_results = results['poor']
        self._plot_single_result(poor_results, self.ax_poor, "Poor Dataset Clustering")

        # Plot standard results
        standard_results = results['standard']
        self._plot_single_result(standard_results, self.ax_standard, "Standard Dataset Clustering")

        # Set main title
        self.fig.suptitle('Group Identifiability Analysis: Poor vs Standard Dataset Clustering', fontsize=16, fontweight='bold')

        # Add global legend based on actual number of personas
        num_personas = len(results['poor']['profile_names'])  # Use poor results to get persona count
        self._add_global_legend(num_personas)

        # Create new canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Display statistics table
        self.display_statistics_table(results)

    def _plot_single_result(self, result, ax, title):
        """Plot a single analysis result on the given axis"""
        ax.clear()

        plot_df = pd.DataFrame({
            'PC1': result['principal_components'][:, 0],
            'PC2': result['principal_components'][:, 1],
            'True Profile': [result['profile_names'][label] for label in result['true_labels']],
            'Predicted Cluster': [f'Cluster {label + 1}' for label in result['predicted_labels']]
        })

        # Use different markers for each persona
        markers = ['o', '^', 's', 'D', 'v', '<', '>', 'p', '*', 'h']
        plot_df['Marker'] = [markers[label % len(markers)] for label in result['true_labels']]

        # Use cluster colors
        cluster_colors = plt.cm.tab10(range(result['num_personas']))

        for cluster_num in set(plot_df['Predicted Cluster']):
            cluster_idx = int(cluster_num.replace('Cluster ', '')) - 1
            cluster_data = plot_df[plot_df['Predicted Cluster'] == cluster_num]

            for marker in set(plot_df['Marker']):
                marker_data = cluster_data[cluster_data['Marker'] == marker]
                if len(marker_data) > 0:
                    ax.scatter(marker_data['PC1'], marker_data['PC2'],
                             c=[cluster_colors[cluster_idx]], s=80, alpha=0.7,
                             edgecolors='black', linewidths=0.5, marker=marker)

        ax.set_title(f"{title}\nARI: {result['ari_score']:.4f}")
        ax.set_xlabel('PC 1')
        ax.set_ylabel('PC 2')
        ax.grid(True, which='both', linestyle='--', linewidth=0.5)

    def _add_global_legend(self, num_personas):
        """Add a global legend to the figure based on actual number of personas"""
        # Create legend elements
        legend_elements = []

        # Persona markers legend - only show markers for actual personas
        markers = ['o', '^', 's', 'D', 'v', '<', '>', 'p', '*', 'h', 'X', 'd']
        for i in range(min(num_personas, len(markers))):
            legend_elements.append(Line2D([0], [0], marker=markers[i], color='black',
                                         label=f'Persona {i+1}', markersize=8, linestyle='None'))

        # Add separator
        legend_elements.append(Patch(facecolor='white', label=''))

        # Cluster colors legend - only show clusters for actual personas
        cluster_colors = plt.cm.tab10(range(min(num_personas, 10)))
        for i in range(min(num_personas, 10)):
            legend_elements.append(Patch(facecolor=cluster_colors[i], label=f'Cluster {i+1}'))

        # Calculate optimal column layout
        total_items = min(num_personas, len(markers)) + min(num_personas, 10) + 1  # +1 for separator

        # For small numbers (1-3 personas), use 2 columns to group personas and clusters together
        if num_personas <= 3:
            ncol = 2
        # For medium numbers (4-6 personas), use 3 columns
        elif num_personas <= 6:
            ncol = 3
        # For larger numbers, use 4 columns maximum
        else:
            ncol = 4

        # Add legend to figure with optimized column layout
        self.fig.legend(handles=legend_elements, loc='lower center',
                       bbox_to_anchor=(0.5, 0.02), ncol=ncol, fontsize='small')
        # Adjust layout to accommodate legend
        self.fig.subplots_adjust(bottom=0.15 + 0.02 * ncol)

    def display_statistics_table(self, results):
        """Display group identifiability analysis results in a table"""
        # Clear previous table
        if self.data_tree:
            self.data_tree.destroy()

        # Define columns
        columns = ['Dataset Type', 'ARI Score', 'PC1 Variance', 'PC2 Variance',
                  'Sample Count', 'Persona Count']

        self.data_tree = ttk.Treeview(self.table_frame, columns=columns, show='headings', height=10)

        # Configure column headings
        for col in columns:
            self.data_tree.heading(col, text=col)

        # Set column widths
        self.data_tree.column('Dataset Type', width=100)
        self.data_tree.column('ARI Score', width=100)
        self.data_tree.column('PC1 Variance', width=100)
        self.data_tree.column('PC2 Variance', width=100)
        self.data_tree.column('Sample Count', width=100)
        self.data_tree.column('Persona Count', width=100)

        # Populate table with results
        for dataset_type in ['poor', 'standard']:
            result = results[dataset_type]
            self.data_tree.insert('', 'end', values=(
                dataset_type.capitalize(),
                f"{result['ari_score']:.4f}",
                f"{result['explained_variance'][0]:.2%}",
                f"{result['explained_variance'][1]:.2%}",
                len(result['true_labels']),
                result['num_personas']
            ))

        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.data_tree.yview)
        self.data_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        self.data_tree.pack(fill=tk.BOTH, expand=True)

    def save_to_svg(self):
        """Save the matplotlib figure as SVG vector image"""
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
        pass

    def setData(self, data, update_callback):
        # Panel is self-contained, does not need external data
        pass