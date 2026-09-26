import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from scipy.spatial.distance import euclidean

from asociety.personality.analysis_utils import (
    load_personality_data,
    get_combined_and_scaled_data,
    run_kmeans_analysis,
    run_pca,
    PERSONALITY_TRAITS
)
from studio.progress_dialog import ProgressManager


class SingleIdentifiabilityPanel:
    # --- Instrument surface -----------------------------------------------------------
    # The defaults reproduce the personality panel exactly; the value/morality panels override.
    traits = PERSONALITY_TRAITS
    table = 'personality'
    initialdir = 'data/db/personality/individual'
    title = "单一可辨识性分析：贫乏 vs 标准样本聚类对比"

    def loader(self, db_path):
        return load_personality_data(db_path, table=self.table, columns=self.traits)

    def __init__(self, parent):
        self.main = ttk.Frame(parent)
        self.main.pack(fill=tk.BOTH, expand=True)

        control_frame = ttk.Frame(self.main)
        control_frame.pack(fill=tk.X, padx=10, pady=10)

        title_label = ttk.Label(control_frame, text=self.title, font=("Helvetica", 14, "bold"))
        title_label.pack(side=tk.LEFT, padx=(0, 20))

        self.run_button = ttk.Button(control_frame, text="运行分析", command=self.start_analysis)
        self.run_button.pack(side=tk.LEFT, padx=(0, 10))

        self.save_button = ttk.Button(control_frame, text="Save to SVG", command=self.save_to_svg, state=tk.DISABLED)
        self.save_button.pack(side=tk.LEFT)

        # Persona directory selection
        selection_frame = ttk.Frame(self.main)
        selection_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(selection_frame, text="第一个画像目录:").pack(side=tk.LEFT, padx=(0, 10))
        self.persona1_path = tk.StringVar()
        ttk.Entry(selection_frame, textvariable=self.persona1_path, width=40).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(selection_frame, text="浏览", command=self.select_persona1).pack(side=tk.LEFT)

        ttk.Label(selection_frame, text="第二个画像目录:").pack(side=tk.LEFT, padx=(20, 10))
        self.persona2_path = tk.StringVar()
        ttk.Entry(selection_frame, textvariable=self.persona2_path, width=40).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(selection_frame, text="浏览", command=self.select_persona2).pack(side=tk.LEFT)

        # Main Paned Window for Plot and Table
        self.main_paned = ttk.PanedWindow(self.main, orient=tk.VERTICAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.plot_frame = ttk.Frame(self.main_paned)
        self.main_paned.add(self.plot_frame, weight=7)

        ari_frame = ttk.Frame(self.plot_frame)
        ari_frame.pack(fill=tk.X, pady=(0, 10))

        self.ari_label_samples = ttk.Label(ari_frame, text="标准样本聚类 ARI: -", font=("Helvetica", 10, "bold"))
        self.ari_label_samples.pack(side=tk.LEFT, padx=(0, 20))

        self.ari_label_poor = ttk.Label(ari_frame, text="贫乏样本聚类 ARI: -", font=("Helvetica", 10, "bold"))
        self.ari_label_poor.pack(side=tk.LEFT)

        self.fig, (self.ax_samples, self.ax_poor) = plt.subplots(1, 2, figsize=(14, 6))
        self.ax_samples.set_aspect("auto")
        self.ax_poor.set_aspect("auto")
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.fig.set_constrained_layout(True)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.table_frame = ttk.Frame(self.main_paned)
        self.main_paned.add(self.table_frame, weight=3)
        self.data_tree = None

        self.progress_manager = ProgressManager(self.main)

    def select_persona1(self):
        directory = filedialog.askdirectory(title="选择第一个画像目录", initialdir=self.initialdir)
        if directory:
            self.persona1_path.set(directory)

    def select_persona2(self):
        directory = filedialog.askdirectory(title="选择第二个画像目录", initialdir=self.initialdir)
        if directory:
            self.persona2_path.set(directory)

    def start_analysis(self):
        persona1_dir = self.persona1_path.get()
        persona2_dir = self.persona2_path.get()

        if not persona1_dir or not persona2_dir:
            messagebox.showerror("错误", "请先选择两个画像目录")
            return

        persona1_poor = os.path.join(persona1_dir, "poor.db")
        persona1_standard = os.path.join(persona1_dir, "standard.db")
        persona2_poor = os.path.join(persona2_dir, "poor.db")
        persona2_standard = os.path.join(persona2_dir, "standard.db")

        missing_files = []
        for file_path, desc in [
            (persona1_poor, "第一个画像的 poor.db"),
            (persona1_standard, "第一个画像的 standard.db"),
            (persona2_poor, "第二个画像的 poor.db"),
            (persona2_standard, "第二个画像的 standard.db")
        ]:
            if not os.path.exists(file_path):
                missing_files.append(desc)

        if missing_files:
            messagebox.showerror("错误", f"以下数据库文件不存在:\n" + "\n".join(missing_files))
            return

        def analysis_task(progress_dialog):
            results = {}
            progress_dialog.update_message("正在分析贫乏样本聚类...")
            results['poor'] = self._run_poor_analysis(persona1_poor, persona2_poor)
            if progress_dialog.is_cancelled(): return None

            progress_dialog.update_message("正在分析标准样本聚类...")
            results['standard'] = self._run_standard_analysis(persona1_standard, persona2_standard)
            if progress_dialog.is_cancelled(): return None

            return results

        def on_success(results):
            if results:
                if results.get('standard'):
                    self.display_results(
                        results['standard'], self.ax_samples,
                        self.ari_label_samples, "标准样本 vs 标准样本聚类")
                if results.get('poor'):
                    self.display_results(
                        results['poor'], self.ax_poor,
                        self.ari_label_poor, "贫乏样本 vs 贫乏样本聚类")
                self.save_button.config(state=tk.NORMAL)
                self.canvas.draw()
                self.display_statistics_table(results)

        def on_error(error):
            messagebox.showerror("分析错误", f"发生错误: {error}")

        self.progress_manager.run_with_progress(
            analysis_task,
            title="单一可识别性分析",
            message="正在准备...",
            success_callback=on_success,
            error_callback=on_error
        )

    def _run_pair_analysis(self, db1, db2, label1, label2):
        """Runs clustering analysis for two databases of the same method."""
        df1 = self.loader(db1)
        df2 = self.loader(db2)

        profile_dataframes = [df1, df2]
        profile_names = [label1, label2]

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
            'centroid_distance': centroid_distance
        }

    def _run_poor_analysis(self, poor_db1, poor_db2):
        return self._run_pair_analysis(poor_db1, poor_db2, "画像1 贫乏", "画像2 贫乏")

    def _run_standard_analysis(self, standard_db1, standard_db2):
        return self._run_pair_analysis(standard_db1, standard_db2, "画像1 标准", "画像2 标准")

    def display_results(self, result, ax, ari_label, title):
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

    def display_statistics_table(self, results):
        if self.data_tree:
            self.data_tree.destroy()

        columns = ['画像对', '数据集类型', 'ARI', '质心距离', 'PC1 方差', 'PC2 方差', '样本数']
        self.data_tree = ttk.Treeview(self.table_frame, columns=columns, show='headings', height=10)

        for col in columns:
            self.data_tree.heading(col, text=col)
            self.data_tree.column(col, width=110, anchor='center')

        persona1_num = os.path.basename(self.persona1_path.get()).replace('persona', '')
        persona2_num = os.path.basename(self.persona2_path.get()).replace('persona', '')

        for dtype, key in [('贫乏', 'poor'), ('标准', 'standard')]:
            r = results.get(key)
            if not r:
                continue
            self.data_tree.insert('', 'end', values=(
                f"{persona1_num}-{persona2_num}",
                dtype,
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
