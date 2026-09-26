import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from asociety.personality.analysis_utils import load_personality_data, PERSONALITY_TRAITS
from studio import theme
from studio.progress_dialog import ProgressManager


class SingleDensityPanel:
    # --- Instrument surface -----------------------------------------------------------
    # The defaults reproduce the personality panel exactly; the value/morality panels override.
    traits = PERSONALITY_TRAITS
    table = 'personality'
    initialdir = 'data/db/personality'
    title = "马氏距离分析 (多文件)"

    def __init__(self, parent):
        self.main = ttk.Frame(parent)
        self.main.pack(fill=tk.BOTH, expand=True)

        control_frame = ttk.Frame(self.main)
        control_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(control_frame, text=self.title, font=theme.FONT_H3).pack(side=tk.LEFT, padx=(0, 20))

        self.run_button = ttk.Button(control_frame, text="运行分析", command=self.start_analysis, state=tk.DISABLED)
        self.run_button.pack(side=tk.LEFT, padx=5)

        self.show_curves = True
        self.view_toggle = ttk.Button(control_frame, text="切换为直方图", command=self.toggle_view)
        self.view_toggle.pack(side=tk.LEFT, padx=5)

        self.save_button = ttk.Button(control_frame, text="Save to SVG", command=self.save_to_svg, state=tk.DISABLED)
        self.save_button.pack(side=tk.LEFT, padx=5)

        file_selection_frame = ttk.Frame(self.main)
        file_selection_frame.pack(fill=tk.X, padx=10, pady=5)

        self.file_list_label = ttk.Label(file_selection_frame, text="已选文件: 无")
        self.file_list_label.pack(side=tk.LEFT, padx=(0, 10))

        add_file_button = ttk.Button(file_selection_frame, text="添加文件...", command=self.add_file)
        add_file_button.pack(side=tk.LEFT, padx=(0, 10))

        clear_files_button = ttk.Button(file_selection_frame, text="清空文件", command=self.clear_files)
        clear_files_button.pack(side=tk.LEFT, padx=(0, 10))

        self.selected_files = []

        self.results_paned_window = ttk.PanedWindow(self.main, orient=tk.VERTICAL)
        self.results_paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.plot_frame = ttk.Frame(self.results_paned_window)
        self.results_paned_window.add(self.plot_frame, weight=7)

        self.table_frame = ttk.Frame(self.results_paned_window)
        self.results_paned_window.add(self.table_frame, weight=3)

        self.fig = None
        self.canvas = None
        self.data_tree = None
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
            self._clear_results()

    def clear_files(self):
        self.selected_files = []
        self.update_file_list_label()
        self.run_button.config(state=tk.DISABLED)
        self.save_button.config(state=tk.DISABLED)
        self._clear_results()

    def _clear_results(self):
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
            self.canvas = None
        if self.data_tree:
            self.data_tree.destroy()
            self.data_tree = None

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
            all_data = []

            progress_dialog.update_message("正在加载所有数据...")
            for i, file_path in enumerate(self.selected_files):
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"数据库文件不存在: {file_path}")
                df = load_personality_data(file_path, table=self.table, columns=self.traits)
                all_data.append(df[self.traits].values)
                progress_dialog.set_progress((i + 1) / total_files * 50)

            combined = np.vstack(all_data)
            global_mean = np.mean(combined, axis=0)
            global_cov = np.cov(combined, rowvar=False)
            global_inv_cov = np.linalg.pinv(global_cov)

            for i, (file_path, data) in enumerate(zip(self.selected_files, all_data)):
                progress_dialog.update_message(f"正在计算 {os.path.basename(file_path)} 的距离...")
                if progress_dialog.is_cancelled():
                    return None

                delta = data - global_mean
                mahalanobis_sq = np.sum((delta @ global_inv_cov) * delta, axis=1)
                distances = np.sqrt(mahalanobis_sq)
                distances_clean = self._remove_outliers_iqr(distances)
                cv, kurtosis = self._calculate_statistical_metrics(distances_clean)

                results[file_path] = {
                    'distances': distances,
                    'distances_clean': distances_clean,
                    'cv': cv,
                    'kurtosis': kurtosis,
                    'color': plt.cm.tab10(i % 10),
                    'label': os.path.basename(file_path).replace('.db', '')
                }
                progress_dialog.set_progress(50 + (i + 1) / total_files * 50)

            return results

        def on_success(results):
            if results:
                self.results = results
                self.display_results()

        def on_error(error):
            messagebox.showerror("分析错误", f"发生错误: {error}")

        self.progress_manager.run_with_progress(
            analysis_task,
            title="马氏距离分析中...",
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
            if self.data_tree:
                self.data_tree.destroy()
                self.data_tree = None

            self.fig, ax = plt.subplots(figsize=(12, 8))

            all_distances = np.concatenate([r['distances_clean'] for r in self.results.values()])
            x_min = float(np.min(all_distances)) - 0.5
            x_max = float(np.max(all_distances)) + 0.5
            x = np.linspace(x_min, x_max, 1000)

            if self.show_curves:
                from scipy.stats import gaussian_kde
                for file_path, result in self.results.items():
                    distances = result['distances_clean']
                    if len(distances) > 1:
                        kde = gaussian_kde(distances)
                        y = kde(x)
                        ax.plot(x, y, color=result['color'], linewidth=2, label=result['label'])
                        ax.fill_between(x, y, alpha=0.3, color=result['color'])
                ax.set_title('Mahalanobis Distance Distribution (KDE)', fontsize=16, fontweight='bold')
            else:
                for file_path, result in self.results.items():
                    ax.hist(result['distances_clean'], bins='auto', density=True, alpha=0.6,
                            color=result['color'], edgecolor='black', label=result['label'])
                ax.set_title('Mahalanobis Distance Distribution (Histogram)', fontsize=16, fontweight='bold')

            ax.set_xlabel('Mahalanobis Distance')
            ax.set_ylabel('Probability Density')
            ax.grid(True, which='both', linestyle='--', linewidth=0.5)
            ax.legend()

            self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            self.canvas.draw()

            self.display_statistics_table()
            self.save_button.config(state=tk.NORMAL)

        except Exception as e:
            messagebox.showerror("显示错误", f"显示结果时出错: {e}")

    def display_statistics_table(self):
        cols = ['文件名', '变异系数', '峰度', '样本数']
        self.data_tree = ttk.Treeview(self.table_frame, columns=cols, show='headings', height=10)

        for col in cols:
            self.data_tree.heading(col, text=col)
            self.data_tree.column(col, width=120, anchor='center')

        for file_path, result in self.results.items():
            self.data_tree.insert('', 'end', values=(
                result['label'],
                f"{result['cv']:.4f}",
                f"{result['kurtosis']:.4f}",
                len(result['distances_clean'])
            ))

        scrollbar = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.data_tree.yview)
        self.data_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        self.data_tree.pack(fill=tk.BOTH, expand=True)

    def _remove_outliers_iqr(self, data):
        if len(data) < 4:
            return data
        q1 = np.percentile(data, 25)
        q3 = np.percentile(data, 75)
        iqr = q3 - q1
        return data[(data >= q1 - 1.5 * iqr) & (data <= q3 + 1.5 * iqr)]

    def _calculate_statistical_metrics(self, data):
        if len(data) < 2:
            return 0.0, 0.0
        mean = float(np.mean(data))
        std = float(np.std(data))
        cv = std / mean if mean != 0 else 0.0
        if len(data) >= 4 and std > 0:
            kurtosis = float(np.mean(((data - mean) / std) ** 4) - 3)
        else:
            kurtosis = 0.0
        return cv, kurtosis

    def toggle_view(self):
        self.show_curves = not self.show_curves
        self.view_toggle.config(text="切换为直方图" if self.show_curves else "切换为曲线")
        if self.results:
            self.display_results()

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
