import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

from asociety.personality.analysis_utils import (
    load_personality_data,
    get_combined_and_scaled_data,
    run_kmeans_analysis,
    run_pca,
    PERSONALITY_TRAITS
)
from studio import theme
from studio.progress_dialog import ProgressManager


class GroupIdentifiabilityPanel:
    # --- Instrument surface -----------------------------------------------------------
    # The defaults reproduce the personality panel exactly; the value/morality panels override.
    traits = PERSONALITY_TRAITS
    table = 'personality'
    data_dir = 'data/db/personality/individual'
    title = "群体可识别性分析：贫乏 vs 标准样本聚类"

    def loader(self, db_path):
        return load_personality_data(db_path, table=self.table, columns=self.traits)

    def __init__(self, parent):
        self.main = ttk.Frame(parent)
        self.main.pack(fill=tk.BOTH, expand=True)

        control_frame = ttk.Frame(self.main)
        control_frame.pack(fill=tk.X, padx=10, pady=10)

        title_label = ttk.Label(control_frame, text=self.title, font=theme.FONT_H3)
        title_label.pack(side=tk.LEFT, padx=(0, 20))

        self.run_button = ttk.Button(control_frame, text="运行分析", command=self.start_analysis)
        self.run_button.pack(side=tk.LEFT, padx=(0, 10))

        self.save_button = ttk.Button(control_frame, text="Save to SVG", command=self.save_to_svg, state=tk.DISABLED)
        self.save_button.pack(side=tk.LEFT)

        self.main_paned = ttk.PanedWindow(self.main, orient=tk.VERTICAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.plot_frame = ttk.Frame(self.main_paned)
        self.main_paned.add(self.plot_frame, weight=7)

        self.fig, (self.ax_poor, self.ax_standard) = plt.subplots(1, 2, figsize=(14, 6))
        self.ax_poor.set_aspect("auto")
        self.ax_standard.set_aspect("auto")
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.fig.set_constrained_layout(True)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.table_frame = ttk.Frame(self.main_paned)
        self.main_paned.add(self.table_frame, weight=3)
        self.data_tree = None

        self.progress_manager = ProgressManager(self.main)

    def start_analysis(self):
        persona_dirs = self._get_persona_directories()
        if not persona_dirs:
            messagebox.showerror("错误", "在 individual 目录下没有找到有效的画像目录。")
            return

        def analysis_task(progress_dialog):
            progress_dialog.update_message("正在加载贫乏样本...")
            poor_results = self._load_and_analyze_group(persona_dirs, 'poor', progress_dialog, 0, 50)
            if progress_dialog.is_cancelled():
                return None

            progress_dialog.update_message("正在加载标准样本...")
            standard_results = self._load_and_analyze_group(persona_dirs, 'standard', progress_dialog, 50, 50)
            if progress_dialog.is_cancelled():
                return None

            return {'poor': poor_results, 'standard': standard_results}

        def on_success(results):
            if results:
                self.display_results(results)
                self.save_button.config(state=tk.NORMAL)
                self.canvas.draw()

        def on_error(error):
            messagebox.showerror("分析错误", f"发生错误: {error}")

        self.progress_manager.run_with_progress(
            analysis_task,
            title="群体可识别性分析",
            message="正在准备...",
            success_callback=on_success,
            error_callback=on_error
        )

    def _get_persona_directories(self):
        """Return persona directory names under the individual directory."""
        persona_dirs = []
        if os.path.exists(self.data_dir):
            for item in os.listdir(self.data_dir):
                item_path = os.path.join(self.data_dir, item)
                if os.path.isdir(item_path) and item.startswith('persona'):
                    persona_dirs.append(item)
        persona_dirs.sort(key=lambda x: int(x.replace('persona', '')) if x.replace('persona', '').isdigit() else 0)
        return persona_dirs

    def _load_and_analyze_group(self, persona_dirs, dataset_type, progress_dialog, progress_start, progress_range):
        profile_dataframes = []
        profile_names = []
        total_personas = len(persona_dirs)

        for i, persona_dir in enumerate(persona_dirs):
            persona_num = persona_dir.replace('persona', '')
            persona_path = os.path.join(self.data_dir, persona_dir)

            db_file = None
            if os.path.exists(persona_path):
                for file in os.listdir(persona_path):
                    if file.endswith('.db') and file.replace('.db', '') == dataset_type:
                        db_file = os.path.join(persona_path, file)
                        break

            if db_file and os.path.exists(db_file):
                try:
                    df = self.loader(db_file)
                    profile_dataframes.append(df)
                    profile_names.append(f"Persona {persona_num}")
                except Exception as e:
                    print(f"加载 {db_file} 失败: {e}")

            progress = progress_start + (i + 1) / total_personas * progress_range
            progress_dialog.set_progress(progress)

        if not profile_dataframes:
            raise ValueError(f"没有找到 {dataset_type} 数据集")

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
        if hasattr(self, 'canvas') and self.canvas:
            self.canvas.get_tk_widget().destroy()
        if self.data_tree:
            self.data_tree.destroy()
            self.data_tree = None

        self.fig, (self.ax_poor, self.ax_standard) = plt.subplots(1, 2, figsize=(14, 6))

        self._plot_single_result(results['poor'], self.ax_poor, "贫乏样本聚类")
        self._plot_single_result(results['standard'], self.ax_standard, "标准样本聚类")

        self.fig.suptitle(self.title, fontsize=16, fontweight='bold')

        num_personas = len(results['poor']['profile_names'])
        self._add_global_legend(num_personas)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.display_statistics_table(results)

    def _plot_single_result(self, result, ax, title):
        ax.clear()

        plot_df = pd.DataFrame({
            'PC1': result['principal_components'][:, 0],
            'PC2': result['principal_components'][:, 1],
            'True Profile': [result['profile_names'][label] for label in result['true_labels']],
            'Predicted Cluster': [f'Cluster {label + 1}' for label in result['predicted_labels']]
        })

        markers = ['o', '^', 's', 'D', 'v', '<', '>', 'p', '*', 'h']
        plot_df['Marker'] = [markers[label % len(markers)] for label in result['true_labels']]

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
        legend_elements = []

        markers = ['o', '^', 's', 'D', 'v', '<', '>', 'p', '*', 'h', 'X', 'd']
        for i in range(min(num_personas, len(markers))):
            legend_elements.append(Line2D([0], [0], marker=markers[i], color='black',
                                          label=f'Persona {i+1}', markersize=8, linestyle='None'))

        legend_elements.append(Patch(facecolor='white', label=''))

        cluster_colors = plt.cm.tab10(range(min(num_personas, 10)))
        for i in range(min(num_personas, 10)):
            legend_elements.append(Patch(facecolor=cluster_colors[i], label=f'Cluster {i+1}'))

        if num_personas <= 3:
            ncol = 2
        elif num_personas <= 6:
            ncol = 3
        else:
            ncol = 4

        self.fig.legend(handles=legend_elements, loc='lower center',
                        bbox_to_anchor=(0.5, 0.02), ncol=ncol, fontsize='small')
        self.fig.subplots_adjust(bottom=0.15 + 0.02 * ncol)

    def display_statistics_table(self, results):
        if self.data_tree:
            self.data_tree.destroy()

        columns = ['数据集类型', 'ARI', 'PC1 方差', 'PC2 方差', '样本数', '画像数']
        self.data_tree = ttk.Treeview(self.table_frame, columns=columns, show='headings', height=10)

        for col in columns:
            self.data_tree.heading(col, text=col)
            self.data_tree.column(col, width=110, anchor='center')

        for dataset_type in ['poor', 'standard']:
            result = results[dataset_type]
            self.data_tree.insert('', 'end', values=(
                '贫乏' if dataset_type == 'poor' else '标准',
                f"{result['ari_score']:.4f}",
                f"{result['explained_variance'][0]:.2%}",
                f"{result['explained_variance'][1]:.2%}",
                len(result['true_labels']),
                result['num_personas']
            ))

        scrollbar = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.data_tree.yview)
        self.data_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        self.data_tree.pack(fill=tk.BOTH, expand=True)

    def save_to_svg(self):
        if self.fig is None:
            messagebox.showwarning("No Plot", "请先运行分析以生成图表。")
            return
        file_path = filedialog.asksaveasfilename(
            title="保存图表为 SVG",
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
