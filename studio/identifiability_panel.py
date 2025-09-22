import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

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

        # --- Combined Plot Frame ---
        self.plot_frame = ttk.Frame(self.main)
        self.plot_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

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

        self.progress_manager = ProgressManager(self.main)

    def start_analysis(self):
        dir_samples = "data/db/backup/samples300"
        dir_poor = "data/db/backup/poor300"

        if not os.path.isdir(dir_samples) or not os.path.isdir(dir_poor):
            messagebox.showerror("Error", "Required data directories 'samples300' or 'poor300' not found.")
            return

        # --- Analysis Task Definition ---
        def analysis_task(progress_dialog):
            results = {}
            # Analyze Standard Samples
            progress_dialog.update_message("Analyzing Standard Samples (samples300)...")
            results['samples'] = self._run_single_analysis(dir_samples)
            if progress_dialog.is_cancelled(): return None

            # Analyze Poor Samples
            progress_dialog.update_message("Analyzing Poor Samples (poor300)...")
            results['poor'] = self._run_single_analysis(dir_poor)
            if progress_dialog.is_cancelled(): return None

            return results

        # --- Callbacks ---
        def on_success(results):
            if results:
                if results.get('samples'):
                    self.display_results(
                        results['samples'], self.ax_samples,
                        self.ari_label_samples, "Standard Samples (Samples 300)"
                    )
                if results.get('poor'):
                    self.display_results(
                        results['poor'], self.ax_poor,
                        self.ari_label_poor, "Poor Samples (Poor 300)"
                    )
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

    def display_results(self, result, ax, ari_label, title):
        """Displays the results on the given matplotlib axis."""
        ax.clear()
        
        ari_score = result['ari_score']
        ari_label.config(text=f"Adjusted Rand Index (ARI): {ari_score:.4f}")

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
