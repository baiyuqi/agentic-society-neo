import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from scipy.spatial.distance import euclidean

from asociety.personality.analysis_utils import (
    load_profiles_from_directory,
    get_combined_and_scaled_data,
    run_kmeans_analysis,
    run_pca
)
from studio.progress_dialog import ProgressManager

class SingleIdentifiabilityPanel:
    def __init__(self, parent):
        self.main = ttk.Frame(parent)
        self.main.pack(fill=tk.BOTH, expand=True)

        # --- Top Control Frame ---
        control_frame = ttk.Frame(self.main)
        control_frame.pack(fill=tk.X, padx=10, pady=10)

        title_label = ttk.Label(control_frame, text="Single Identifiability Analysis: Poor vs Standard Clustering Comparison", font=("Helvetica", 14, "bold"))
        title_label.pack(side=tk.LEFT, padx=(0, 20))

        # Persona directory selection
        selection_frame = ttk.Frame(self.main)
        selection_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(selection_frame, text="Select First Persona Directory:").pack(side=tk.LEFT, padx=(0, 10))
        self.persona1_path = tk.StringVar()
        ttk.Entry(selection_frame, textvariable=self.persona1_path, width=50).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(selection_frame, text="Browse", command=self.select_persona1).pack(side=tk.LEFT)

        ttk.Label(selection_frame, text="Select Second Persona Directory:").pack(side=tk.LEFT, padx=(20, 10))
        self.persona2_path = tk.StringVar()
        ttk.Entry(selection_frame, textvariable=self.persona2_path, width=50).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(selection_frame, text="Browse", command=self.select_persona2).pack(side=tk.LEFT)

        self.run_button = ttk.Button(control_frame, text="Run Analysis", command=self.start_analysis)
        self.run_button.pack(side=tk.LEFT, padx=(0, 10))

        self.save_button = ttk.Button(control_frame, text="Save SVG", command=self.save_to_svg, state=tk.DISABLED)
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

        self.ari_label_samples = ttk.Label(ari_frame, text="Standard Clustering ARI: -", font=("Helvetica", 10, "bold"))
        self.ari_label_samples.pack(side=tk.LEFT, padx=(0, 20))

        self.ari_label_poor = ttk.Label(ari_frame, text="Poor Clustering ARI: -", font=("Helvetica", 10, "bold"))
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

    def select_persona1(self):
        """Select first persona directory"""
        directory = filedialog.askdirectory(
            title="Select First Persona Directory",
            initialdir="data/db/backup/individual"
        )
        if directory:
            self.persona1_path.set(directory)

    def select_persona2(self):
        """Select second persona directory"""
        directory = filedialog.askdirectory(
            title="Select Second Persona Directory",
            initialdir="data/db/backup/individual"
        )
        if directory:
            self.persona2_path.set(directory)

    def start_analysis(self):
        # Check if persona directories are selected
        persona1_dir = self.persona1_path.get()
        persona2_dir = self.persona2_path.get()

        if not persona1_dir or not persona2_dir:
            messagebox.showerror("Error", "Please select both Persona directories first")
            return

        # Check if required database files exist
        persona1_poor = os.path.join(persona1_dir, "poor.db")
        persona1_standard = os.path.join(persona1_dir, "standard.db")
        persona2_poor = os.path.join(persona2_dir, "poor.db")
        persona2_standard = os.path.join(persona2_dir, "standard.db")

        missing_files = []
        for file_path, desc in [
            (persona1_poor, "First Persona's poor.db"),
            (persona1_standard, "First Persona's standard.db"),
            (persona2_poor, "Second Persona's poor.db"),
            (persona2_standard, "Second Persona's standard.db")
        ]:
            if not os.path.exists(file_path):
                missing_files.append(desc)

        if missing_files:
            messagebox.showerror("Error", f"The following database files do not exist:\n" + "\n".join(missing_files))
            return

        # --- Analysis Task Definition ---
        def analysis_task(progress_dialog):
            results = {}

            # Analyze Poor samples (poor vs poor)
            progress_dialog.update_message("Analyzing Poor sample clustering...")
            results['poor'] = self._run_poor_analysis(persona1_poor, persona2_poor)
            if progress_dialog.is_cancelled(): return None

            # Analyze Standard samples (standard vs standard)
            progress_dialog.update_message("Analyzing Standard sample clustering...")
            results['standard'] = self._run_standard_analysis(persona1_standard, persona2_standard)
            if progress_dialog.is_cancelled(): return None

            return results

        # --- Callbacks ---
        def on_success(results):
            if results:
                if results.get('standard'):
                    self.display_results(
                        results['standard'], self.ax_samples,
                        self.ari_label_samples, "Standard vs Standard Clustering"
                    )
                if results.get('poor'):
                    self.display_results(
                        results['poor'], self.ax_poor,
                        self.ari_label_poor, "Poor vs Poor Clustering"
                    )
                # Enable save button and redraw canvas
                self.save_button.config(state=tk.NORMAL)
                self.canvas.draw()
                # Display statistics table
                self.display_statistics_table(results)

        def on_error(error):
            messagebox.showerror("Analysis Error", f"An error occurred during analysis: {error}")

        self.progress_manager.run_with_progress(
            analysis_task,
            title="Single Identifiability Analysis",
            message="Preparing...",
            success_callback=on_success,
            error_callback=on_error
        )

    def _run_poor_analysis(self, poor_db1, poor_db2):
        """Runs clustering analysis for poor vs poor."""
        from asociety.personality.analysis_utils import load_personality_data

        # Load data from both poor databases
        df1 = load_personality_data(poor_db1)
        df2 = load_personality_data(poor_db2)

        profile_dataframes = [df1, df2]
        profile_names = [f"Persona1 Poor", f"Persona2 Poor"]

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
            'centroid_distance': centroid_distance
        }

    def _run_standard_analysis(self, standard_db1, standard_db2):
        """Runs clustering analysis for standard vs standard."""
        from asociety.personality.analysis_utils import load_personality_data

        # Load data from both standard databases
        df1 = load_personality_data(standard_db1)
        df2 = load_personality_data(standard_db2)

        profile_dataframes = [df1, df2]
        profile_names = [f"Persona1 Standard", f"Persona2 Standard"]

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
            'centroid_distance': centroid_distance
        }

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

    def display_results(self, result, ax, ari_label, title):
        """Displays the results on the given matplotlib axis."""
        ax.clear()

        ari_score = result['ari_score']
        ari_label.config(text=f"ARI: {ari_score:.4f}")

        plot_df = pd.DataFrame({
            'PC1': result['principal_components'][:, 0],
            'PC2': result['principal_components'][:, 1],
            'True Profile': [result['profile_names'][label] for label in result['true_labels']],
            'Predicted Cluster': [f'Cluster {label + 1}' for label in result['predicted_labels']]
        })

        sns.scatterplot(
            data=plot_df, x='PC1', y='PC2', hue='Predicted Cluster',
            style='True Profile', s=80, alpha=0.8, palette='tab10', ax=ax
        )
        
        ax.set_title(title)
        ax.set_xlabel(f'PC 1 ({result["explained_variance"][0]:.1%} variance)')
        ax.set_ylabel(f'PC 2 ({result["explained_variance"][1]:.1%} variance)')
        ax.legend(title='Legend', fontsize='small')
        ax.grid(True, which='both', linestyle='--', linewidth=0.5)

    def set_language(self, lang):
        pass

    def setData(self, data, update_callback):
        # Panel is self-contained, does not need external data
        pass

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

        # Extract persona numbers from directory paths
        persona1_num = os.path.basename(self.persona1_path.get()).replace('persona', '')
        persona2_num = os.path.basename(self.persona2_path.get()).replace('persona', '')

        # Populate table with results
        if results.get('poor'):
            poor_results = results['poor']
            self.data_tree.insert('', 'end', values=(
                f"{persona1_num}-{persona2_num}",
                'Poor',
                f"{poor_results['ari_score']:.4f}",
                f"{poor_results.get('centroid_distance', 0):.4f}",
                f"{poor_results['explained_variance'][0]:.2%}",
                f"{poor_results['explained_variance'][1]:.2%}",
                len(poor_results['true_labels'])
            ))

        if results.get('standard'):
            standard_results = results['standard']
            self.data_tree.insert('', 'end', values=(
                f"{persona1_num}-{persona2_num}",
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
            messagebox.showwarning("No Chart", "Please run analysis first to generate charts")
            return

        file_path = filedialog.asksaveasfilename(
            title="Save Comparison Chart as SVG",
            defaultextension=".svg",
            filetypes=[("SVG Files", "*.svg"), ("All Files", "*.*")]
        )

        if file_path:
            self.fig.savefig(file_path, format="svg", bbox_inches="tight")
            messagebox.showinfo("Success", f"Comparison chart successfully saved to:\n{file_path}")