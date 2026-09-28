import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from matplotlib.gridspec import GridSpec
from scipy.spatial.distance import euclidean

from asociety.personality.analysis_utils import (
    load_personality_data,
    get_combined_and_scaled_data,
    run_kmeans_analysis,
    run_pca,
    PERSONALITY_TRAITS
)
from studio import theme
from studio.progress_dialog import ProgressManager


class IdentifiabilityPanel:
    # --- Instrument surface -----------------------------------------------------------
    # The defaults reproduce the personality panel exactly; the value/morality panels override.
    traits = PERSONALITY_TRAITS
    table = 'personality'
    data_dir = 'data/db/personality/individual'
    title = "可识别性分析：画像两两对比"

    def loader(self, db_path):
        return load_personality_data(db_path, table=self.table, columns=self.traits)

    def __init__(self, parent):
        self.main = ttk.Frame(parent)
        self.main.pack(fill=tk.BOTH, expand=True)

        # --- Top Control Frame ---
        control_frame = ttk.Frame(self.main)
        control_frame.pack(fill=tk.X, padx=10, pady=10)

        title_label = ttk.Label(control_frame, text=self.title, font=theme.FONT_H3)
        title_label.pack(side=tk.LEFT, padx=(0, 20))

        self.run_button = ttk.Button(control_frame, text="运行分析", command=self.start_analysis)
        self.run_button.pack(side=tk.LEFT, padx=(0, 10))

        self.save_button = ttk.Button(control_frame, text="Save to SVG", command=self.save_to_svg, state=tk.DISABLED)
        self.save_button.pack(side=tk.LEFT)

        # --- Main Paned Window for Plot and Table ---
        self.main_paned = ttk.PanedWindow(self.main, orient=tk.VERTICAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.plot_frame = ttk.Frame(self.main_paned)
        self.main_paned.add(self.plot_frame, weight=7)

        self.fig = plt.figure(figsize=(12, 8))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.table_frame = ttk.Frame(self.main_paned)
        self.main_paned.add(self.table_frame, weight=3)
        self.data_tree = None

        self.progress_manager = ProgressManager(self.main)

    def start_analysis(self):
        persona_pairs = self._get_persona_pairs()
        if not persona_pairs:
            messagebox.showerror("错误", "在 individual 目录下没有找到有效的画像目录。")
            return

        def analysis_task(progress_dialog):
            results = {}
            total_pairs = len(persona_pairs)

            for i, (persona1, persona2) in enumerate(persona_pairs):
                progress_dialog.update_message(f"正在分析画像对 {persona1}-{persona2}...")

                poor_results = self._run_pair_analysis(persona1, persona2, 'poor')
                if progress_dialog.is_cancelled():
                    return None

                standard_results = self._run_pair_analysis(persona1, persona2, 'standard')
                if progress_dialog.is_cancelled():
                    return None

                results[f"{persona1}_{persona2}"] = {
                    'poor': poor_results,
                    'standard': standard_results
                }
                progress_dialog.set_progress((i + 1) / total_pairs * 100)

            return results

        def on_success(results):
            if results:
                self.display_results(results)
                self.save_button.config(state=tk.NORMAL)
                self.canvas.draw()

        def on_error(error):
            messagebox.showerror("分析错误", f"发生错误: {error}")

        self.progress_manager.run_with_progress(
            analysis_task,
            title="可识别性分析",
            message="正在准备...",
            success_callback=on_success,
            error_callback=on_error
        )

    def _get_persona_pairs(self):
        """Enumerate cyclic adjacent persona pairs: (1,2), (2,3), ..., (n,1)."""
        persona_nums = []
        if os.path.exists(self.data_dir):
            for item in os.listdir(self.data_dir):
                item_path = os.path.join(self.data_dir, item)
                if os.path.isdir(item_path) and item.startswith('persona'):
                    num = item.replace('persona', '')
                    if num.isdigit():
                        persona_nums.append(int(num))
        persona_nums.sort()

        if len(persona_nums) < 2:
            return []

        pairs = []
        for i in range(len(persona_nums)):
            persona1 = persona_nums[i]
            persona2 = persona_nums[(i + 1) % len(persona_nums)]
            pairs.append((persona1, persona2))
        return pairs

    def _run_pair_analysis(self, persona1, persona2, dataset_type):
        """K=2 clustering of two personas for one dataset type (poor/standard)."""
        dir1 = os.path.join(self.data_dir, f"persona{persona1}")
        dir2 = os.path.join(self.data_dir, f"persona{persona2}")

        db_files = []
        for dir_path in [dir1, dir2]:
            if os.path.exists(dir_path):
                for file in os.listdir(dir_path):
                    if file.endswith('.db') and file.replace('.db', '') == dataset_type:
                        db_files.append(os.path.join(dir_path, file))

        if len(db_files) != 2:
            raise ValueError(f"找不到画像 {persona1} 与 {persona2} 的 {dataset_type} 数据库")

        profile_dataframes = []
        profile_names = []
        for i, db_file in enumerate(db_files):
            df = self.loader(db_file)
            profile_dataframes.append(df)
            profile_names.append(f"Persona {persona1 if i == 0 else persona2}")

        scaled_vectors, true_labels = get_combined_and_scaled_data(profile_dataframes)
        num_profiles = len(profile_dataframes)
        kmeans, predicted_labels, ari_score = run_kmeans_analysis(
            scaled_vectors, true_labels, num_profiles, return_model=True)
        principal_components, explained_variance = run_pca(scaled_vectors)

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
        if hasattr(self, 'canvas') and self.canvas:
            self.canvas.get_tk_widget().destroy()
        if self.data_tree:
            self.data_tree.destroy()
            self.data_tree = None

        all_pc1, all_pc2 = [], []
        for pair_results in results.values():
            all_pc1.extend(pair_results['poor']['principal_components'][:, 0])
            all_pc1.extend(pair_results['standard']['principal_components'][:, 0])
            all_pc2.extend(pair_results['poor']['principal_components'][:, 1])
            all_pc2.extend(pair_results['standard']['principal_components'][:, 1])

        global_xmin, global_xmax = min(all_pc1), max(all_pc1)
        global_ymin, global_ymax = min(all_pc2), max(all_pc2)
        margin_x = (global_xmax - global_xmin) * 0.05
        margin_y = (global_ymax - global_ymin) * 0.05
        self.global_xlim = (global_xmin - margin_x, global_xmax + margin_x)
        self.global_ylim = (global_ymin - margin_y, global_ymax + margin_y)

        num_pairs = len(results)
        cols = min(5, num_pairs)
        rows = (num_pairs + cols - 1) // cols

        self.fig = plt.figure(figsize=(6 * cols, 8 * rows))
        gs = GridSpec(rows * 2, cols, figure=self.fig, hspace=0.1, wspace=0.1)

        for i, (pair_key, pair_results) in enumerate(results.items()):
            persona1, persona2 = pair_key.split('_')
            row_pair = i // cols
            col_pair = i % cols

            poor_ax = self.fig.add_subplot(gs[row_pair * 2, col_pair])
            show_labels = (i == 0 and row_pair == 0 and col_pair == 0)
            self._plot_single_result(pair_results['poor'], poor_ax, f"Pair {persona1}-{persona2} - Poor", show_labels=show_labels)

            standard_ax = self.fig.add_subplot(gs[row_pair * 2 + 1, col_pair])
            self._plot_single_result(pair_results['standard'], standard_ax, f"Pair {persona1}-{persona2} - Standard", show_labels=False)

        self.fig.suptitle('可识别性分析：画像两两对比', fontsize=16, fontweight='bold')
        self._add_global_legend()

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.display_statistics_table(results)

    def _plot_single_result(self, result, ax, title, show_labels=True):
        ax.clear()

        plot_df = pd.DataFrame({
            'PC1': result['principal_components'][:, 0],
            'PC2': result['principal_components'][:, 1],
            'True Profile': [result['profile_names'][label] for label in result['true_labels']],
            'Predicted Cluster': [f'Cluster {label + 1}' for label in result['predicted_labels']]
        })

        markers = ['o' if label == 0 else '+' for label in result['true_labels']]
        plot_df['Marker'] = markers

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

        ax.set_title(f"{title}", pad=10)

        if show_labels:
            ax.set_xlabel('PC 1', labelpad=5)
            ax.set_ylabel('PC 2', labelpad=5)
        else:
            ax.set_xlabel('')
            ax.set_ylabel('')
            ax.tick_params(axis='both', which='both', bottom=False, top=False,
                           left=False, right=False, labelbottom=False, labelleft=False)

        ax.grid(True, which='both', linestyle='--', linewidth=0.5)
        ax.set_xlim(self.global_xlim)
        ax.set_ylim(self.global_ylim)
        ax.set_aspect(1.0, adjustable='box')

    def _add_global_legend(self):
        legend_elements = []

        cluster_colors = plt.cm.tab10(range(2))
        for i in range(2):
            legend_elements.append(Patch(facecolor=cluster_colors[i], label=f'Cluster {i+1}'))

        legend_elements.append(Patch(facecolor='white', label=''))

        legend_elements.append(Line2D([0], [0], marker='o', color='black', label='Persona 1',
                                      markersize=8, linestyle='None'))
        legend_elements.append(Line2D([0], [0], marker='+', color='black', label='Persona 2',
                                      markersize=8, linestyle='None'))

        self.fig.legend(handles=legend_elements, loc='lower center',
                        bbox_to_anchor=(0.5, 0.01), ncol=2, fontsize='small')
        self.fig.subplots_adjust(bottom=0.10, top=0.95, left=0.05, right=0.95)

    def display_statistics_table(self, results):
        if self.data_tree:
            self.data_tree.destroy()

        columns = ['画像对', '数据集类型', 'ARI', '质心距离', 'PC1 方差', 'PC2 方差', '样本数']
        self.data_tree = ttk.Treeview(self.table_frame, columns=columns, show='headings', height=10)

        for col in columns:
            self.data_tree.heading(col, text=col)
            self.data_tree.column(col, width=110, anchor='center')

        for pair_key, pair_results in results.items():
            persona1, persona2 = pair_key.split('_')

            for dataset_type, label in [('poor', '贫乏'), ('standard', '标准')]:
                r = pair_results[dataset_type]
                self.data_tree.insert('', 'end', values=(
                    f"{persona1}-{persona2}",
                    label,
                    f"{r['ari_score']:.4f}",
                    f"{r.get('centroid_distance', 0):.4f}",
                    f"{r['explained_variance'][0]:.2%}",
                    f"{r['explained_variance'][1]:.2%}",
                    len(r['true_labels'])
                ))

        scrollbar = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.data_tree.yview)
        self.data_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        self.data_tree.pack(fill=tk.BOTH, expand=True)

    def save_to_svg(self):
        if self.fig is None:
            messagebox.showwarning("无图表", "请先运行分析以生成图表。")
            return

        file_path = filedialog.asksaveasfilename(
            title="保存组合图表为 SVG",
            defaultextension=".svg",
            filetypes=[("SVG Files", "*.svg"), ("All Files", "*.*")]
        )
        if file_path:
            self.fig.savefig(file_path, format="svg", bbox_inches="tight")
            messagebox.showinfo("成功", f"图表已保存到:\n{file_path}")

    def set_language(self, lang):
        pass

    def setData(self, data, update_callback):
        pass
