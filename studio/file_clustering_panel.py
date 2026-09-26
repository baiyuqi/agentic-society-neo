import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from scipy.spatial.distance import pdist, squareform

from asociety.personality.analysis_utils import (
    load_personality_data,
    get_combined_and_scaled_data,
    run_kmeans_analysis,
    run_pca,
    PERSONALITY_TRAITS
)
from studio.progress_dialog import ProgressManager


class FileClusteringPanel:
    # --- Instrument surface -----------------------------------------------------------
    # The defaults reproduce the personality panel exactly; the value/morality panels override.
    traits = PERSONALITY_TRAITS
    table = 'personality'
    initialdir = 'data/db/personality'

    def loader(self, db_path):
        return load_personality_data(db_path, table=self.table, columns=self.traits)

    def __init__(self, parent):
        self.main = ttk.Frame(parent)
        self.main.pack(fill=tk.BOTH, expand=True)
        self.fig = None
        self.analysis_results = {}
        self.selected_files = []

        control_frame = ttk.Frame(self.main)
        control_frame.pack(fill=tk.X, padx=10, pady=10)

        title_label = ttk.Label(control_frame, text="选择文件聚类 (多文件)", font=("Helvetica", 14, "bold"))
        title_label.pack(side=tk.LEFT, padx=(0, 20))

        self.save_button = ttk.Button(control_frame, text="Save to SVG", command=self.save_to_svg, state=tk.DISABLED)
        self.save_button.pack(side=tk.LEFT)

        file_selection_frame = ttk.Frame(self.main)
        file_selection_frame.pack(fill=tk.X, padx=10, pady=5)

        self.file_list_label = ttk.Label(file_selection_frame, text="已选文件: 无")
        self.file_list_label.pack(side=tk.LEFT, padx=(0, 10))

        add_file_button = ttk.Button(file_selection_frame, text="添加文件...", command=self.add_file)
        add_file_button.pack(side=tk.LEFT, padx=(0, 10))

        clear_files_button = ttk.Button(file_selection_frame, text="清空文件", command=self.clear_files)
        clear_files_button.pack(side=tk.LEFT, padx=(0, 10))

        self.analyze_button = ttk.Button(file_selection_frame, text="运行聚类", command=self.start_analysis, state=tk.DISABLED)
        self.analyze_button.pack(side=tk.LEFT, padx=(0, 10))

        self.progress_manager = ProgressManager(self.main)

        self.results_paned_window = ttk.PanedWindow(self.main, orient=tk.VERTICAL)
        self.results_paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.plot_frame = ttk.Frame(self.results_paned_window)
        self.results_paned_window.add(self.plot_frame, weight=3)

        self.data_frame = ttk.Frame(self.results_paned_window)
        self.results_paned_window.add(self.data_frame, weight=1)

        self.canvas = None
        self.metrics_tree = None

    def add_file(self):
        file_path = filedialog.askopenfilename(
            title='选择一个画像数据库文件',
            filetypes=[('SQLite Database', '*.db')],
            initialdir=self.initialdir
        )
        if file_path and file_path not in self.selected_files:
            self.selected_files.append(file_path)
            self.update_file_list_label()
            self.analyze_button.config(state=tk.NORMAL if len(self.selected_files) >= 2 else tk.DISABLED)
            self.save_button.config(state=tk.DISABLED)
            self._clear_results()

    def clear_files(self):
        self.selected_files = []
        self.update_file_list_label()
        self.analyze_button.config(state=tk.DISABLED)
        self.save_button.config(state=tk.DISABLED)
        self._clear_results()

    def _clear_results(self):
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
            self.canvas = None
        if self.metrics_tree:
            self.metrics_tree.destroy()
            self.metrics_tree = None

    def update_file_list_label(self):
        if not self.selected_files:
            self.file_list_label.config(text="已选文件: 无")
        else:
            file_names = [os.path.basename(f) for f in self.selected_files]
            if len(file_names) <= 3:
                display_text = f"已选文件: {', '.join(file_names)}"
            else:
                display_text = f"已选文件: {len(file_names)} 个文件 ({', '.join(file_names[:3])}...)"
            self.file_list_label.config(text=display_text)

    def start_analysis(self):
        if len(self.selected_files) < 2:
            messagebox.showwarning("文件不足", "请至少选择 2 个文件进行聚类分析。")
            return

        def analysis_task(progress_dialog):
            progress_dialog.update_message("正在加载画像数据...")
            profile_dataframes = []
            profile_names = []

            for file_path in self.selected_files:
                try:
                    df = self.loader(file_path)
                    profile_dataframes.append(df)
                    profile_names.append(os.path.basename(file_path))
                except Exception as e:
                    raise Exception(f"加载 {file_path} 失败: {e}")

            if progress_dialog.is_cancelled(): return None

            progress_dialog.update_message("正在处理和标准化数据...")
            scaled_vectors, true_labels = get_combined_and_scaled_data(profile_dataframes)

            if progress_dialog.is_cancelled(): return None

            progress_dialog.update_message("正在运行K-Means聚类分析...")
            num_profiles = len(profile_dataframes)
            kmeans, predicted_labels, ari_score = run_kmeans_analysis(
                scaled_vectors, true_labels, num_profiles, return_model=True)

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
            messagebox.showerror("分析错误", f"发生错误: {error}")

        self.progress_manager.run_with_progress(
            analysis_task,
            title="聚类分析中...",
            message="正在准备分析...",
            success_callback=on_success,
            error_callback=on_error
        )

    def display_results(self, result):
        try:
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
            ax.set_title('K-Means 聚类结果 vs 真实画像标签 (PCA)')
            ax.set_xlabel(f"主成分 1 ({result['explained_variance'][0]:.1%} 方差)")
            ax.set_ylabel(f"主成分 2 ({result['explained_variance'][1]:.1%} 方差)")
            ax.legend(title='Legend')
            ax.grid(True, which='both', linestyle='--', linewidth=0.5)

            if self.canvas:
                self.canvas.get_tk_widget().destroy()

            self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
            self.canvas.draw()
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            self.display_metrics_table(result)
            self.save_button.config(state=tk.NORMAL)

        except Exception as e:
            messagebox.showerror("显示错误", f"显示结果时出错: {e}")

    def display_metrics_table(self, results):
        if self.metrics_tree:
            self.metrics_tree.destroy()

        self.metrics_tree = ttk.Treeview(self.data_frame, columns=('Metric', 'Value'), show='headings')
        self.metrics_tree.heading('Metric', text='指标')
        self.metrics_tree.heading('Value', text='值')
        self.metrics_tree.column('Metric', width=200)
        self.metrics_tree.column('Value', width=500)

        self.metrics_tree.insert('', 'end', values=('调整兰德指数 (ARI)', f"{results.get('ari_score', 0):.4f}"))
        self.metrics_tree.insert('', 'end', values=('平均质心距离', f"{results.get('average_centroid_distance', 0):.4f}"))
        self.metrics_tree.insert('', 'end', values=('最小质心距离', f"{results.get('min_centroid_distance', 0):.4f}"))
        self.metrics_tree.insert('', 'end', values=('最大质心距离', f"{results.get('max_centroid_distance', 0):.4f}"))

        pca_variance = results.get('explained_variance', [0, 0])
        self.metrics_tree.insert('', 'end', values=('PCA 解释方差', f"PC1: {pca_variance[0]:.2%}, PC2: {pca_variance[1]:.2%}"))

        dist_matrix = results.get('centroid_distance_matrix', [])
        matrix_str = "\n" + pd.DataFrame(dist_matrix).to_string(float_format="%.4f")
        self.metrics_tree.insert('', 'end', values=('质心距离矩阵', matrix_str))

        self.metrics_tree.pack(fill=tk.BOTH, expand=True)

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
