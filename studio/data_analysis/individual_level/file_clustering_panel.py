# studio/manual_clustering_panel.py

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import markdown
import json
from scipy.spatial.distance import pdist, squareform
from tkhtmlview import HTMLScrolledText

from asociety.personality.analysis_utils import (
    load_personality_data,
    get_combined_and_scaled_data,
    run_kmeans_analysis,
    run_pca
)
from asociety.generator.qwen_analyzer import analyze_image_with_text, save_figure_to_bytes
from studio.collapsible_help_panel import CollapsibleHelpPanel
from studio.progress_dialog import ProgressManager
from studio.analysis_panel_utils import show_analysis_window

from studio.help_constants import helpcnstants

class FileClusteringPanel:
    def __init__(self, parent):
        self.main = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)
        self.fig = None
        self.analysis_results = {}
        self.selected_files = []

        main_content_frame = ttk.Frame(self.main)
        self.main.add(main_content_frame, weight=3)

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

        self.analyze_button = ttk.Button(analysis_frame, text="Run Clustering", command=self.start_analysis, state=tk.DISABLED)
        self.analyze_button.pack(side=tk.LEFT, padx=(0, 10))

        self.qwen_button = ttk.Button(analysis_frame, text="结果解析 (AI)", command=self.start_qwen_analysis, state=tk.DISABLED)
        self.qwen_button.pack(side=tk.LEFT, padx=(0, 10))

        self.copy_button = ttk.Button(analysis_frame, text="Copy Data (JSON)", command=self.copy_analysis_data_to_clipboard, state=tk.DISABLED)
        self.copy_button.pack(side=tk.LEFT, padx=(0, 10))

        self.progress_manager = ProgressManager(self.main)

        # Vertical PanedWindow for plot and data table
        self.results_paned_window = ttk.PanedWindow(main_content_frame, orient=tk.VERTICAL)
        self.results_paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.plot_frame = ttk.Frame(self.results_paned_window)
        self.results_paned_window.add(self.plot_frame, weight=3)

        self.data_frame = ttk.Frame(self.results_paned_window)
        self.results_paned_window.add(self.data_frame, weight=1)

        self.canvas = None
        self.metrics_tree = None

        self.current_lang = 'zh'
        help_config = {"title": "手动聚类分析帮助", "content": helpcnstants['manual_clustering']['zh']}
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
            self.analyze_button.config(state=tk.NORMAL if len(self.selected_files) >= 2 else tk.DISABLED)
            self.qwen_button.config(state=tk.DISABLED)
            self.copy_button.config(state=tk.DISABLED)
            if self.canvas:
                self.canvas.get_tk_widget().destroy()
                self.canvas = None
            if self.metrics_tree:
                self.metrics_tree.destroy()
                self.metrics_tree = None

    def clear_files(self):
        self.selected_files = []
        self.update_file_list_label()
        self.analyze_button.config(state=tk.DISABLED)
        self.qwen_button.config(state=tk.DISABLED)
        self.copy_button.config(state=tk.DISABLED)
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
            self.canvas = None
        if self.metrics_tree:
            self.metrics_tree.destroy()
            self.metrics_tree = None

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
        if len(self.selected_files) < 2:
            messagebox.showwarning("Insufficient Files", "Please select at least 2 files for clustering analysis.")
            return

        self.qwen_button.config(state=tk.DISABLED)
        self.copy_button.config(state=tk.DISABLED)

        def analysis_task(progress_dialog):
            progress_dialog.update_message("正在加载画像数据...")
            profile_dataframes = []
            profile_names = []

            for file_path in self.selected_files:
                try:
                    df = load_personality_data(file_path)
                    profile_dataframes.append(df)
                    profile_names.append(os.path.basename(file_path))
                except Exception as e:
                    raise Exception(f"Error loading {file_path}: {e}")

            if progress_dialog.is_cancelled(): return None

            progress_dialog.update_message("正在处理和标准化数据...")
            scaled_vectors, true_labels = get_combined_and_scaled_data(profile_dataframes)

            if progress_dialog.is_cancelled(): return None

            progress_dialog.update_message("正在运行K-Means聚类分析...")
            num_profiles = len(profile_dataframes)
            kmeans, predicted_labels, ari_score = run_kmeans_analysis(scaled_vectors, true_labels, num_profiles, return_model=True)

            if progress_dialog.is_cancelled(): return None

            progress_dialog.update_message("正在进行PCA降维...")
            principal_components, explained_variance = run_pca(scaled_vectors)

            if progress_dialog.is_cancelled(): return None

            progress_dialog.update_message("正在计算聚类中心距离...")
            centroids = kmeans.cluster_centers_

            centroid_distances_condensed = pdist(centroids, 'euclidean')

            centroid_distance_matrix = squareform(centroid_distances_condensed)

            avg_dist = np.mean(centroid_distances_condensed) if centroid_distances_condensed.size > 0 else 0
            min_dist = np.min(centroid_distances_condensed) if centroid_distances_condensed.size > 0 else 0
            max_dist = np.max(centroid_distances_condensed) if centroid_distances_condensed.size > 0 else 0

            progress_dialog.update_message("正在生成可视化图表...")
            return {
                'profile_names': profile_names,
                'ari_score': ari_score,
                'principal_components': principal_components,
                'explained_variance': explained_variance.tolist(),
                'true_labels': true_labels,
                'predicted_labels': predicted_labels,
                'centroid_distance_matrix': centroid_distance_matrix.tolist(),
                'average_centroid_distance': avg_dist,
                'min_centroid_distance': min_dist,
                'max_centroid_distance': max_dist
            }

        def on_success(result):
            if result:
                self.analysis_results = result
                self.display_results(result)

        def on_error(error):
            messagebox.showerror("Analysis Error", f"An error occurred: {error}")

        self.progress_manager.run_with_progress(
            analysis_task,
            title="聚类分析中...",
            message="正在准备分析...",
            success_callback=on_success,
            error_callback=on_error
        )

    def display_results(self, result):
        try:
            # --- Plotting ---
            plot_df = pd.DataFrame({
                'PC1': result['principal_components'][:, 0],
                'PC2': result['principal_components'][:, 1],
                'True Profile': [result['profile_names'][label] for label in result['true_labels']],
                'Predicted Cluster': [f'Cluster {label + 1}' for label in result['predicted_labels']]
            })

            self.fig, ax = plt.subplots(figsize=(10, 6))
            sns.scatterplot(
                data=plot_df, x='PC1', y='PC2', hue='Predicted Cluster',
                style='True Profile', s=100, alpha=0.7, palette='tab10', ax=ax
            )
            ax.set_title('K-Means Clustering Results vs. True Profile Labels (PCA)')
            ax.set_xlabel(f"Principal Component 1 ({result['explained_variance'][0]:.1%} variance)")
            ax.set_ylabel(f"Principal Component 2 ({result['explained_variance'][1]:.1%} variance)")
            ax.legend(title='Legend'); ax.grid(True, which='both', linestyle='--', linewidth=0.5)

            if self.canvas:
                self.canvas.get_tk_widget().destroy()

            self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
            self.canvas.draw()
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            # --- Metrics Table ---
            self.display_metrics_table(result)

            self.qwen_button.config(state=tk.NORMAL)
            self.copy_button.config(state=tk.NORMAL)

        except Exception as e:
            messagebox.showerror("Result Display Error", f"An error occurred: {e}")
            self.qwen_button.config(state=tk.DISABLED)
            self.copy_button.config(state=tk.DISABLED)

    def display_metrics_table(self, results):
        if self.metrics_tree:
            self.metrics_tree.destroy()

        self.metrics_tree = ttk.Treeview(self.data_frame, columns=('Metric', 'Value'), show='headings')
        self.metrics_tree.heading('Metric', text='Metric')
        self.metrics_tree.heading('Value', text='Value')
        self.metrics_tree.column('Metric', width=200)
        self.metrics_tree.column('Value', width=500)

        # Populate with key metrics
        self.metrics_tree.insert('', 'end', values=('Adjusted Rand Index (ARI)', f"{results.get('ari_score', 0):.4f}"))
        self.metrics_tree.insert('', 'end', values=('Average Centroid Distance', f"{results.get('average_centroid_distance', 0):.4f}"))
        self.metrics_tree.insert('', 'end', values=('Min Centroid Distance', f"{results.get('min_centroid_distance', 0):.4f}"))
        self.metrics_tree.insert('', 'end', values=('Max Centroid Distance', f"{results.get('max_centroid_distance', 0):.4f}"))

        pca_variance = results.get('explained_variance', [0, 0])
        self.metrics_tree.insert('', 'end', values=('PCA Explained Variance', f"PC1: {pca_variance[0]:.2%}, PC2: {pca_variance[1]:.2%}"))

        # Add the distance matrix in a readable format
        dist_matrix = results.get('centroid_distance_matrix', [])
        matrix_str = "\n" + pd.DataFrame(dist_matrix).to_string(float_format="%.4f")
        self.metrics_tree.insert('', 'end', values=('Centroid Distance Matrix', matrix_str))

        self.metrics_tree.pack(fill=tk.BOTH, expand=True)

    def copy_analysis_data_to_clipboard(self):
        if not self.analysis_results:
            messagebox.showwarning("No Data", "There is no analysis data to copy. Please run the analysis first.")
            return

        try:
            # Prepare data for JSON export
            data_to_export = {
                "adjusted_rand_index": self.analysis_results.get('ari_score'),
                "pca_explained_variance_ratio": self.analysis_results.get('explained_variance'),
                "cluster_separation_metrics": {
                    "average_centroid_distance": self.analysis_results.get('average_centroid_distance'),
                    "min_centroid_distance": self.analysis_results.get('min_centroid_distance'),
                    "max_centroid_distance": self.analysis_results.get('max_centroid_distance'),
                    "centroid_distance_matrix": self.analysis_results.get('centroid_distance_matrix')
                },
                "profile_names": self.analysis_results.get('profile_names'),
                "selected_files": self.selected_files
            }

            json_data = json.dumps(data_to_export, indent=4)

            self.main.clipboard_clear()
            self.main.clipboard_append(json_data)

            messagebox.showinfo("Copied", "Analysis data has been copied to the clipboard in JSON format.")

        except Exception as e:
            messagebox.showerror("Copy Error", f"An error occurred while copying data: {e}")

    def start_qwen_analysis(self):
        if self.fig is None or not self.analysis_results:
            messagebox.showwarning("无结果", "请先运行聚类分析。" )
            return

        def analysis_task(progress_dialog):
            progress_dialog.update_message("正在准备图片数据...")
            image_bytes = save_figure_to_bytes(self.fig)

            if progress_dialog.is_cancelled(): return None

            progress_dialog.update_message("正在构建分析提示...")
            prompt = self._build_clustering_prompt()

            progress_dialog.update_message("正在调用AI API进行分析...")
            analysis_result = analyze_image_with_text(image_bytes, prompt)
            return analysis_result

        def on_success(result):
            if result:
                show_analysis_window(self.main, result)

        def on_error(error):
            messagebox.showerror("AI 分析错误", f"发生错误: {error}")

        self.progress_manager.run_with_progress(
            analysis_task,
            title="AI结果解析",
            message="正在连接AI...",
            success_callback=on_success,
            error_callback=on_error
        )

    def _build_clustering_prompt(self):
        ari_score = self.analysis_results.get('ari_score', 'N/A')
        profile_names = self.analysis_results.get('profile_names', [])

        return f"""
你是一位专业的数据科学家，你的任务是解读K-Means聚类分析的结果。
下面是一张PCA降维后的散点图和相应的"调整兰德指数"(ARI)。

**背景信息:**
- **目标**: 评估多个AI智能体画像的可区分性。我们想知道这些画像在性格测试结果上是否表现出独有的、可被算法识别的特征。实验设计是：对几个persona反复进行性格测试，然后使用K-Means聚类算法来判断这些画像的性格是否可以被成功区分。
- **数据点**: 图中的每个点代表一个人物画像驱动的AI智能体的一次性格测试结果。实验中对每个智能体进行多次人物性格测试，每次测试形成一个点
- **点的形状 (True Profile)**: 代表这个智能体真实的来源画像文件。总共有 {len(profile_names)} 个不同的来源画像: {', '.join(profile_names)}.
- **点的颜色 (Predicted Cluster)**: 代表K-Means算法在不知道真实来源的情况下，将它分配到的簇。
- **实验结果**: {self.analysis_results}

**如何解读ARI:**
- ARI = 1.0: 完美匹配。算法找到的簇与真实来源完全对应，意味着画像之间**极易区分**。
- ARI ≈ 0.0: 随机分配。算法的聚类结果和瞎猜差不多，意味着画像**几乎无法区分**。
- ARI < 0.0: 比随机还差。

**你的任务:**
1.  **综合评估**: 根据ARI分数和图表，对这些画像的可区分性给出一个总体评价。
2.  **解读图表**: 详细描述图中的聚类情况。例如，哪些画像（形状）被很好地分开了？哪些画像被混在了一起？是否存在一个簇包含了多种不同来源的画像？
3.  **提出洞见**: 基于你的分析，提出可能的洞见或结论。例如，这是否说明模型在生成人格时具有多样性？或者说明模型生成的人格比较趋同？

请用清晰、结构化的方式给出你的分析。
"""

    def set_language(self, lang):
        self.current_lang = lang
        self.update_help_content()

    def update_help_content(self):
        title = "手动聚类分析帮助" if self.current_lang == 'zh' else "Manual Clustering Analysis Help"
        content = helpcnstants['manual_clustering'][self.current_lang]

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
                html_content = markdown.markdown(content)
                help_panel.html_widget.set_html(html_content)

    def setData(self, appKey, updateTree):
        pass