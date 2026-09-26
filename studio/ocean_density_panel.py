import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from asociety.personality.analysis_utils import load_personality_data
from studio import theme
from studio.progress_dialog import ProgressManager


class OceanDensityPanel:
    # --- Instrument surface -----------------------------------------------------------
    # OCEAN (Big Five) is personality-only; value/morality have different trait structures.
    traits = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']
    initialdir = 'data/db/personality'
    human_db_path = 'data/db/personality/human.db'

    dimension_labels = {
        'openness': 'Openness (开放性)',
        'conscientiousness': 'Conscientiousness (尽责性)',
        'extraversion': 'Extraversion (外向性)',
        'agreeableness': 'Agreeableness (宜人性)',
        'neuroticism': 'Neuroticism (神经质)',
    }

    def __init__(self, parent):
        self.main = ttk.Frame(parent)
        self.main.pack(fill=tk.BOTH, expand=True)

        control_frame = ttk.Frame(self.main)
        control_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(control_frame, text="OCEAN维度密度分析", font=theme.FONT_H3).pack(side=tk.LEFT, padx=(0, 20))

        self.run_button = ttk.Button(control_frame, text="运行分析", command=self.start_analysis, state=tk.DISABLED)
        self.run_button.pack(side=tk.LEFT, padx=5)

        self.show_curves = True
        self.view_toggle = ttk.Button(control_frame, text="切换为直方图", command=self.toggle_view)
        self.view_toggle.pack(side=tk.LEFT, padx=5)

        density_frame = ttk.Frame(control_frame)
        density_frame.pack(side=tk.LEFT, padx=5)
        ttk.Label(density_frame, text="密度上限:").pack(side=tk.LEFT)
        self.density_max_var = tk.StringVar(value="1.0")
        density_combo = ttk.Combobox(density_frame, textvariable=self.density_max_var,
                                     values=['0.1', '0.2', '0.3', '0.4', '0.5', '0.6', '0.7', '0.8', '0.9', '1.0'],
                                     width=5, state='readonly')
        density_combo.pack(side=tk.LEFT, padx=(5, 0))
        density_combo.bind('<<ComboboxSelected>>', self.on_density_max_change)

        self.save_button = ttk.Button(control_frame, text="Save to SVG", command=self.save_to_svg, state=tk.DISABLED)
        self.save_button.pack(side=tk.LEFT, padx=5)

        self.distance_button = ttk.Button(control_frame, text="计算距离指标", command=self.calculate_distances, state=tk.DISABLED)
        self.distance_button.pack(side=tk.LEFT, padx=5)

        file_selection_frame = ttk.Frame(self.main)
        file_selection_frame.pack(fill=tk.X, padx=10, pady=5)

        self.file_list_label = ttk.Label(file_selection_frame, text="已选文件: 无")
        self.file_list_label.pack(side=tk.LEFT, padx=(0, 10))

        add_file_button = ttk.Button(file_selection_frame, text="添加文件...", command=self.add_file)
        add_file_button.pack(side=tk.LEFT, padx=(0, 10))

        clear_files_button = ttk.Button(file_selection_frame, text="清空文件", command=self.clear_files)
        clear_files_button.pack(side=tk.LEFT, padx=(0, 10))

        self.selected_files = []

        self.plot_frame = ttk.Frame(self.main)
        self.plot_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.fig = None
        self.canvas = None
        self.progress_manager = ProgressManager(self.main)

        self.results = {}

    def add_file(self):
        file_path = filedialog.askopenfilename(
            title='选择一个画像数据库文件',
            filetypes=[('SQLite Database', '*.db')],
            initialdir=self.initialdir
        )
        if file_path and file_path not in self.selected_files:
            self.selected_files.append(file_path)
            self.update_file_list_label()
            self.run_button.config(state=tk.NORMAL if len(self.selected_files) >= 1 else tk.DISABLED)
            self.save_button.config(state=tk.DISABLED)
            self.distance_button.config(state=tk.DISABLED)
            self._clear_plot()

    def clear_files(self):
        self.selected_files = []
        self.update_file_list_label()
        self.run_button.config(state=tk.DISABLED)
        self.save_button.config(state=tk.DISABLED)
        self.distance_button.config(state=tk.DISABLED)
        self._clear_plot()

    def _clear_plot(self):
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
            self.canvas = None

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
        if len(self.selected_files) < 1:
            messagebox.showwarning("文件不足", "请至少选择 1 个文件进行分析。")
            return

        def analysis_task(progress_dialog):
            results = {}
            total_files = len(self.selected_files)

            for i, file_path in enumerate(self.selected_files):
                progress_dialog.update_message(f"正在加载 {os.path.basename(file_path)}...")
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"数据库文件不存在: {file_path}")

                df = load_personality_data(file_path, table='personality', columns=self.traits)
                ocean_data = {dim: df[dim].values for dim in self.traits}

                results[file_path] = {
                    'ocean_data': ocean_data,
                    'color': plt.cm.tab10(i % 10),
                    'label': os.path.basename(file_path).replace('.db', '')
                }
                progress_dialog.set_progress((i + 1) / total_files * 100)

            return results

        def on_success(results):
            if results:
                self.results = results
                self.display_results()

        def on_error(error):
            messagebox.showerror("分析错误", f"发生错误: {error}")

        self.progress_manager.run_with_progress(
            analysis_task,
            title="OCEAN维度分析中...",
            message="正在准备分析...",
            success_callback=on_success,
            error_callback=on_error
        )

    def display_results(self):
        try:
            if not self.results:
                return
            if self.canvas:
                self.canvas.get_tk_widget().destroy()

            self.fig, axes = plt.subplots(2, 3, figsize=(15, 10))
            self.fig.delaxes(axes[1, 2])
            axes_flat = [axes[0, 0], axes[0, 1], axes[0, 2], axes[1, 0], axes[1, 1]]

            x = np.linspace(0, 100, 1000)

            for i, dimension in enumerate(self.traits):
                ax = axes_flat[i]

                if self.show_curves:
                    from scipy.stats import gaussian_kde
                    for file_path, result in self.results.items():
                        values = result['ocean_data'][dimension]
                        if len(values) > 1:
                            kde = gaussian_kde(values)
                            y = kde(x)
                            ax.plot(x, y, color=result['color'], linewidth=2, label=result['label'])
                            ax.fill_between(x, y, alpha=0.3, color=result['color'])
                else:
                    for file_path, result in self.results.items():
                        ax.hist(result['ocean_data'][dimension], bins='auto', density=True, alpha=0.6,
                                color=result['color'], edgecolor='black', label=result['label'],
                                range=(0, 100))

                ax.set_title(self.dimension_labels[dimension], fontsize=12, fontweight='bold')
                ax.set_xlabel('Score')
                ax.set_ylabel('Probability Density')
                ax.set_xlim(0, 100)
                ax.set_ylim(0, float(self.density_max_var.get()))
                ax.grid(True, which='both', linestyle='--', linewidth=0.5)

            if self.results:
                axes_flat[0].legend()

            self.fig.suptitle(
                'OCEAN Personality Dimensions Distribution (KDE)' if self.show_curves
                else 'OCEAN Personality Dimensions Distribution (Histogram)',
                fontsize=16, fontweight='bold')
            self.fig.tight_layout(rect=[0, 0, 1, 0.96])

            self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            self.canvas.draw()

            self.save_button.config(state=tk.NORMAL)
            self.distance_button.config(state=tk.NORMAL)

        except Exception as e:
            messagebox.showerror("显示错误", f"显示结果时出错: {e}")

    def toggle_view(self):
        self.show_curves = not self.show_curves
        self.view_toggle.config(text="切换为直方图" if self.show_curves else "切换为曲线")
        if self.results:
            self.display_results()

    def on_density_max_change(self, event=None):
        if self.results:
            self.display_results()

    def calculate_distances(self):
        if not self.results:
            messagebox.showwarning("无分析结果", "请先运行分析以生成结果。")
            return
        if not os.path.exists(self.human_db_path):
            messagebox.showwarning("未找到 human.db", f"human.db 不存在于: {self.human_db_path}")
            return

        def distance_task(progress_dialog):
            from scipy.stats import wasserstein_distance
            from sklearn.metrics.pairwise import cosine_similarity

            progress_dialog.update_message("正在加载 human.db 数据...")
            human_df = load_personality_data(self.human_db_path, table='personality', columns=self.traits)
            human_data = human_df[self.traits].values

            distance_results = {}
            total_files = len(self.results)

            for i, (file_path, result) in enumerate(self.results.items()):
                progress_dialog.update_message(f"正在计算 {result['label']} 的距离...")

                current_data = np.array([result['ocean_data'][dim] for dim in self.traits]).T

                wasserstein_distances = []
                for dim_idx in range(len(self.traits)):
                    wd = wasserstein_distance(human_data[:, dim_idx], current_data[:, dim_idx])
                    wasserstein_distances.append(wd)

                human_mean = np.mean(human_data, axis=0)
                current_mean = np.mean(current_data, axis=0)

                distances = {
                    'Wasserstein_Mean': np.mean(wasserstein_distances),
                    'Wasserstein_Std': np.std(wasserstein_distances),
                    'Sliced_Wasserstein': self._calculate_sliced_wasserstein(human_data, current_data),
                    'Frechet_Distance': self._calculate_frechet_distance(human_data, current_data),
                    'Euclidean_Mean_Distance': np.linalg.norm(human_mean - current_mean),
                    'Cosine_Similarity': cosine_similarity([human_mean], [current_mean])[0][0],
                    'MMD': self._calculate_mmd(human_data, current_data),
                    'AMW': self._calculate_amw(human_data, current_data),
                }
                distance_results[result['label']] = distances
                progress_dialog.set_progress((i + 1) / total_files * 100)

            return distance_results

        def on_success(distance_results):
            if distance_results:
                self._display_distance_results(distance_results)

        def on_error(error):
            messagebox.showerror("距离计算错误", f"计算距离时发生错误: {error}")

        self.progress_manager.run_with_progress(
            distance_task,
            title="计算距离指标中...",
            message="正在准备距离计算...",
            success_callback=on_success,
            error_callback=on_error
        )

    def _calculate_sliced_wasserstein(self, data1, data2, n_projections=100):
        from scipy.stats import wasserstein_distance
        n_dims = data1.shape[1]
        projections = np.random.randn(n_projections, n_dims)
        projections = projections / np.linalg.norm(projections, axis=1, keepdims=True)
        sw = []
        for proj in projections:
            sw.append(wasserstein_distance(data1 @ proj, data2 @ proj))
        return np.mean(sw)

    def _calculate_frechet_distance(self, data1, data2):
        from scipy.linalg import sqrtm
        if len(data1) < 2 or len(data2) < 2:
            return np.nan

        mu1 = np.mean(data1, axis=0)
        mu2 = np.mean(data2, axis=0)
        sigma1 = np.cov(data1, rowvar=False)
        sigma2 = np.cov(data2, rowvar=False)
        reg = 1e-3
        sigma1 = sigma1 + np.eye(sigma1.shape[0]) * reg
        sigma2 = sigma2 + np.eye(sigma2.shape[0]) * reg

        try:
            sigma_product = sigma1 @ sigma2
            eigenvalues = np.linalg.eigvals(sigma_product)
            if np.any(eigenvalues < 0):
                trace_term = np.trace(sigma1 + sigma2 - 2 * np.sqrt(np.abs(sigma_product)))
            else:
                trace_term = np.trace(sigma1 + sigma2 - 2 * sqrtm(sigma_product))
            mean_term = np.sum((mu1 - mu2) ** 2)
            frechet_dist = max(0, mean_term + trace_term)
            return np.sqrt(frechet_dist)
        except (np.linalg.LinAlgError, ValueError):
            mean_term = np.sum((mu1 - mu2) ** 2)
            cov_diff = np.linalg.norm(sigma1 - sigma2, 'fro')
            return np.sqrt(mean_term + cov_diff)

    def _calculate_mmd(self, data1, data2, kernel='rbf', gamma=None):
        from sklearn.metrics.pairwise import pairwise_kernels, euclidean_distances
        n1 = data1.shape[0]
        n2 = data2.shape[0]
        if gamma is None:
            if kernel == 'rbf':
                combined = np.vstack([data1, data2])
                pairwise_d = euclidean_distances(combined)
                gamma = 1.0 / (2.0 * np.median(pairwise_d) ** 2)
            else:
                gamma = 1.0 / data1.shape[1]
        K11 = pairwise_kernels(data1, metric=kernel, gamma=gamma)
        K22 = pairwise_kernels(data2, metric=kernel, gamma=gamma)
        K12 = pairwise_kernels(data1, data2, metric=kernel, gamma=gamma)
        mmd_squared = (np.sum(K11) / (n1 * n1) + np.sum(K22) / (n2 * n2) - 2 * np.sum(K12) / (n1 * n2))
        return np.sqrt(max(0, mmd_squared))

    def _calculate_amw(self, data1, data2):
        from scipy.stats import wasserstein_distance
        return np.mean([wasserstein_distance(data1[:, t], data2[:, t]) for t in range(data1.shape[1])])

    def _display_distance_results(self, distance_results):
        popup = tk.Toplevel()
        popup.title("距离指标计算结果")
        popup.geometry("900x400")

        frame = ttk.Frame(popup)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        columns = ['Dataset'] + list(next(iter(distance_results.values())).keys())
        tree = ttk.Treeview(frame, columns=columns, show='headings', height=15)

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120, anchor='center')

        for dataset, metrics in distance_results.items():
            values = [dataset] + [f"{v:.4f}" if isinstance(v, (int, float)) else str(v) for v in metrics.values()]
            tree.insert('', 'end', values=values)

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        tree.pack(fill=tk.BOTH, expand=True)

        close_button = ttk.Button(popup, text="关闭", command=popup.destroy)
        close_button.pack(pady=10)

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
