import tkinter as tk
from tkinter import ttk, messagebox
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
        
        title_label = ttk.Label(control_frame, text="可识别性分析：比较标准样本与贫乏样本", font=("Helvetica", 14, "bold"))
        title_label.pack(side=tk.LEFT, padx=(0, 20))

        self.run_button = ttk.Button(control_frame, text="运行分析", command=self.start_analysis)
        self.run_button.pack(side=tk.LEFT)

        # --- Main Paned Window for Side-by-Side Comparison ---
        paned_window = ttk.PanedWindow(self.main, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)

        # --- Left Panel (Standard Samples) ---
        self.frame_samples = ttk.Frame(paned_window)
        self.ari_label_samples = ttk.Label(self.frame_samples, text="ARI: -", font=("Helvetica", 12, "bold"))
        self.ari_label_samples.pack(pady=5, padx=10, anchor='w')
        self.fig_samples, self.ax_samples = plt.subplots(figsize=(6, 5))
        self.canvas_samples = FigureCanvasTkAgg(self.fig_samples, master=self.frame_samples)
        self.canvas_samples.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        paned_window.add(self.frame_samples, weight=1)

        # --- Right Panel (Poor Samples) ---
        self.frame_poor = ttk.Frame(paned_window)
        self.ari_label_poor = ttk.Label(self.frame_poor, text="ARI: -", font=("Helvetica", 12, "bold"))
        self.ari_label_poor.pack(pady=5, padx=10, anchor='w')
        self.fig_poor, self.ax_poor = plt.subplots(figsize=(6, 5))
        self.canvas_poor = FigureCanvasTkAgg(self.fig_poor, master=self.frame_poor)
        self.canvas_poor.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        paned_window.add(self.frame_poor, weight=1)

        self.progress_manager = ProgressManager(self.main)

    def start_analysis(self):
        dir_samples = "data/db/backup/samples300"
        dir_poor = "data/db/backup/poor300"

        if not os.path.isdir(dir_samples) or not os.path.isdir(dir_poor):
            messagebox.showerror("错误", "找不到所需的数据目录 'samples300' 或 'poor300'。")
            return

        # --- Analysis Task Definition ---
        def analysis_task(progress_dialog):
            results = {}
            # Analyze Standard Samples
            progress_dialog.update_message("正在分析标准样本 (samples300)...")
            results['samples'] = self._run_single_analysis(dir_samples)
            if progress_dialog.is_cancelled(): return None
            
            # Analyze Poor Samples
            progress_dialog.update_message("正在分析贫乏样本 (poor300)...")
            results['poor'] = self._run_single_analysis(dir_poor)
            if progress_dialog.is_cancelled(): return None

            return results

        # --- Callbacks ---
        def on_success(results):
            if results:
                if results.get('samples'):
                    self.display_results(
                        results['samples'], self.ax_samples, self.canvas_samples, 
                        self.ari_label_samples, "标准样本 (Samples 300)"
                    )
                if results.get('poor'):
                    self.display_results(
                        results['poor'], self.ax_poor, self.canvas_poor, 
                        self.ari_label_poor, "贫乏样本 (Poor 300)"
                    )

        def on_error(error):
            messagebox.showerror("分析错误", f"发生错误: {error}")

        self.progress_manager.run_with_progress(
            analysis_task,
            title="可识别性分析",
            message="正在准备...",
            success_callback=on_success,
            error_callback=on_error
        )

    def _run_single_analysis(self, directory):
        """Runs the clustering analysis for a single directory."""
        profile_dataframes, profile_names = load_profiles_from_directory(directory)
        if not profile_dataframes:
            raise ValueError(f"在目录 {directory} 中没有找到有效的数据库文件。")
            
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

    def display_results(self, result, ax, canvas, ari_label, title):
        """Displays the results on the given matplotlib axis and canvas."""
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
        
        canvas.draw()

    def set_language(self, lang):
        pass

    def setData(self, data, update_callback):
        # Panel is self-contained, does not need external data
        pass
