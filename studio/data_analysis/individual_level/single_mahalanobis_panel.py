# studio/single_mahalanobis_panel.py

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import markdown
import json

from asociety.personality.analysis_utils import calculate_single_profile_mahalanobis
from asociety.generator.qwen_analyzer import save_figure_to_bytes, analyze_image_with_text
from studio.collapsible_help_panel import CollapsibleHelpPanel
from studio.progress_dialog import ProgressManager
from studio.analysis_panel_utils import show_analysis_window

from studio.help_constants import helpcnstants
HELP_CONTENT = helpcnstants['mahalanobis']

class SingleMahalanobisPanel:
    def __init__(self, parent):
        self.main = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)
        
        main_content_frame = ttk.Frame(self.main)
        self.main.add(main_content_frame, weight=3)

        control_frame = ttk.Frame(main_content_frame)
        control_frame.pack(fill=tk.X, padx=10, pady=10)

        self.file_label = ttk.Label(control_frame, text="Selected File: None")
        self.file_label.pack(side=tk.LEFT, padx=(0, 10))

        browse_button = ttk.Button(control_frame, text="Browse File...", command=self.browse_file)
        browse_button.pack(side=tk.LEFT, padx=(0, 10))

        self.analyze_button = ttk.Button(control_frame, text="Run Analysis", command=self.start_analysis, state=tk.DISABLED)
        self.analyze_button.pack(side=tk.LEFT, padx=(0, 10))

        self.qwen_button = ttk.Button(control_frame, text="结果解析 (AI)", command=self.start_qwen_analysis, state=tk.DISABLED)
        self.qwen_button.pack(side=tk.LEFT, padx=(0, 10))

        self.copy_button = ttk.Button(control_frame, text="Copy Data (JSON)", command=self.copy_table_data_to_clipboard, state=tk.DISABLED)
        self.copy_button.pack(side=tk.LEFT, padx=(0, 10))

        self.progress_manager = ProgressManager(self.main)

        self.fig = None
        self.distances = None

        # Vertical PanedWindow for plot and data
        self.results_paned_window = ttk.PanedWindow(main_content_frame, orient=tk.VERTICAL)
        self.results_paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.plot_frame = ttk.Frame(self.results_paned_window)
        self.results_paned_window.add(self.plot_frame, weight=3)

        self.data_frame = ttk.Frame(self.results_paned_window)
        self.results_paned_window.add(self.data_frame, weight=1)
        
        self.canvas = None
        self.selected_file = None
        self.data_tree = None

        self.current_lang = 'zh'
        help_config = {"title": "马氏距离分析帮助", "content": HELP_CONTENT['zh']}
        self.collapsible_help = CollapsibleHelpPanel(self.main, help_config, weight=1)

    def browse_file(self):
        file_path = filedialog.askopenfilename(
            title='Select a single persona DB file',
            initialdir='data/db/backup',
            filetypes=[('SQLite DB', '*.db'), ('All Files', '*.*')]
        )
        if file_path:
            self.selected_file = file_path
            self.file_label.config(text=f"Selected File: ...{os.path.basename(file_path)}")
            self.analyze_button.config(state=tk.NORMAL)
            self.qwen_button.config(state=tk.DISABLED)
            self.copy_button.config(state=tk.DISABLED)
            if self.canvas:
                self.canvas.get_tk_widget().destroy()
                self.canvas = None
            if self.data_tree:
                self.data_tree.destroy()
                self.data_tree = None

    def start_analysis(self):
        if not self.selected_file:
            return

        def analysis_task(progress_dialog):
            progress_dialog.update_message("正在加载画像数据...")
            if progress_dialog.is_cancelled(): return None
            progress_dialog.update_message("正在计算马氏距离...")
            distances, data_df = calculate_single_profile_mahalanobis(self.selected_file, return_df=True)
            if progress_dialog.is_cancelled(): return None
            progress_dialog.update_message("正在生成分布图表...")
            return distances, data_df

        def on_success(result):
            if result:
                distances, data_df = result
                self.display_results(distances, data_df)

        def on_error(error):
            messagebox.showerror("Analysis Error", f"An error occurred: {error}")

        self.progress_manager.run_with_progress(
            analysis_task,
            title="马氏距离分析中...",
            message="正在准备分析...",
            success_callback=on_success,
            error_callback=on_error
        )

    def display_results(self, distances, data_df):
        try:
            self.distances = distances
            self.fig, ax = plt.subplots(figsize=(10, 6))
            # Use 'auto' bins to let matplotlib decide the best number of bins
            counts, bin_edges, _ = ax.hist(distances, bins='auto', density=True, alpha=0.7, color='purple', edgecolor='black')
            
            ax.set_title('Probability Distribution of Mahalanobis Distances')
            ax.set_xlabel('Mahalanobis Distance')
            ax.set_ylabel('Probability Density')
            ax.grid(True, which='both', linestyle='--', linewidth=0.5)

            if self.canvas:
                self.canvas.get_tk_widget().destroy()

            self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
            self.canvas.draw()
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            self.qwen_button.config(state=tk.NORMAL)
            self.copy_button.config(state=tk.NORMAL)

            # Pass the calculated histogram data to the table display function
            self.display_histogram_data_table(bin_edges, counts)

        except Exception as e:
            messagebox.showerror("Display Error", f"An error occurred while displaying results: {e}")
            self.qwen_button.config(state=tk.DISABLED)
            self.copy_button.config(state=tk.DISABLED)

    def display_histogram_data_table(self, bin_edges, counts):
        """Displays the histogram data in a table, corresponding to the plot."""
        if self.data_tree:
            self.data_tree.destroy()

        # Remove outliers using IQR method before calculating statistics
        distances_no_outliers = self._remove_outliers_iqr(self.distances)
        
        # Calculate statistical metrics on cleaned data
        cv, kurtosis = self._calculate_statistical_metrics(distances_no_outliers)
        
        # Create table with statistical metrics in title
        table_title = f"Distance Distribution (CV: {cv:.3f}, Kurtosis: {kurtosis:.3f})"
        title_label = ttk.Label(self.data_frame, text=table_title, font=("Helvetica", 10, "bold"))
        title_label.pack(pady=(0, 5))

        cols = ['Distance Range', 'Count', 'Probability Density']
        self.data_tree = ttk.Treeview(self.data_frame, columns=cols, show='headings')

        for col in cols:
            self.data_tree.heading(col, text=col)
            self.data_tree.column(col, width=150, anchor='center')

        # The 'counts' from a density histogram are actually the density values.
        # To get the true count, we need to calculate it based on the total number of samples.
        total_samples = len(self.distances)
        bin_widths = np.diff(bin_edges)
        actual_counts = (counts * total_samples * bin_widths).astype(int)

        for i in range(len(counts)):
            bin_range = f"{bin_edges[i]:.4f} - {bin_edges[i+1]:.4f}"
            density_val = counts[i]
            count_val = actual_counts[i]
            
            self.data_tree.insert('', 'end', values=(bin_range, count_val, f"{density_val:.4f}"))

        # Add a scrollbar
        scrollbar = ttk.Scrollbar(self.data_frame, orient="vertical", command=self.data_tree.yview)
        self.data_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        self.data_tree.pack(fill=tk.BOTH, expand=True)

    def _remove_outliers_iqr(self, data):
        """Remove outliers using Interquartile Range method."""
        if len(data) < 4:  # Need at least 4 points for IQR
            return data
            
        q1 = np.percentile(data, 25)
        q3 = np.percentile(data, 75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        # Filter out outliers
        filtered_data = data[(data >= lower_bound) & (data <= upper_bound)]
        return filtered_data

    def _calculate_statistical_metrics(self, data):
        """Calculate variation coefficient and kurtosis."""
        if len(data) < 2:
            return 0.0, 0.0
            
        mean = np.mean(data)
        std = np.std(data)
        
        # Variation coefficient (avoid division by zero)
        cv = std / mean if mean != 0 else 0.0
        
        # Kurtosis (using Fisher's definition, normal distribution = 0)
        if len(data) >= 4 and std > 0:
            kurtosis = np.mean(((data - mean) / std) ** 4) - 3
        else:
            kurtosis = 0.0
            
        return cv, kurtosis

    def copy_table_data_to_clipboard(self):
        """Copies the data from the histogram table to the clipboard in JSON format."""
        if not self.data_tree:
            messagebox.showwarning("No Data", "There is no data to copy. Please run the analysis first.")
            return

        try:
            data_to_copy = []
            columns = self.data_tree['columns']
            
            for item_id in self.data_tree.get_children():
                row_values = self.data_tree.item(item_id, 'values')
                row_dict = {columns[i]: row_values[i] for i in range(len(columns))}
                data_to_copy.append(row_dict)

            if not data_to_copy:
                messagebox.showwarning("No Data", "The table is empty.")
                return

            json_data = json.dumps(data_to_copy, indent=4, ensure_ascii=False)

            self.main.clipboard_clear()
            self.main.clipboard_append(json_data)
            
            messagebox.showinfo("Copied", "Table data has been copied to the clipboard in JSON format.")

        except Exception as e:
            messagebox.showerror("Copy Error", f"An error occurred while copying data: {e}")

    def start_qwen_analysis(self):
        if self.fig is None:
            messagebox.showwarning("无结果", "请先运行分析.")
            return

        def analysis_task(progress_dialog):
            progress_dialog.update_message("正在准备图片数据...")
            image_bytes = save_figure_to_bytes(self.fig)
            
            if progress_dialog.is_cancelled(): return None

            progress_dialog.update_message("正在构建分析提示...")
            prompt = self._build_mahalanobis_prompt()

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

    def _build_mahalanobis_prompt(self):
        profile_name = os.path.basename(self.selected_file)
        return f"""
你是一位专业的数据科学家，你的任务是解读单个AI画像的马氏距离分布直方图.

**背景信息:**
- **目标**: 评估画像 `{profile_name}` 的内部一致性. 我们想知道这个画像在多次性格测试中是否表现出稳定、集中的特征.实验设计是对同一个画像进行多次性格测试，然后分析测试结果的分布情况.实验结果都是针对同一个画像的测试结果.
- **数据点**: 每个数据点都是画像 `{profile_name}` 的一次性格测试结果.
- **马氏距离**: 该距离衡量了每个数据点到数据集中心的“统计学距离”，它考虑了特征间的相关性并且对量纲不敏感，是异常检测的黄金标准.
- **直方图**: 图表显示了所有数据点马氏距离的概率分布.

**如何解读直方图:**
- **理想形态**: 一个高度一致、稳定的画像，其数据点应该紧密围绕中心分布. 这在直方图上表现为**强烈的右偏分布**（positively skewed）. 即，绝大多数数据点的马氏距离都很小（在左侧形成高峰），只有极少数异常点的距离较大（形成一个长长的右尾）.
- **异常形态**:
    - **双峰或多峰**: 可能表示画像内部存在两个或多个不同的子群体，性格表现不统一.
    - **接近对称或正态分布**: 表示数据点比较分散，一致性较差.
    - **左偏分布**: 非常罕见，可能表示数据存在某种结构性问题.

**你的任务:**
1.  **描述分布形态**: 详细描述你从直方图中看到的分布形状. 它是右偏的、对称的、双峰的，还是其他形态？
2.  **评估一致性**: 基于分布形态，对画像 `{profile_name}` 的内部一致性给出一个明确的评价. 它是高度一致、中等一致，还是不一致？
3.  **提出洞见**: 根据你的分析，这个分布形态可能暗示了什么？例如，这是否说明模型在模拟该人格时非常稳定？或者说明该人格本身就很多变？

请用清晰、结构化的方式给出你的分析.
"""

    def set_language(self, lang):
        self.current_lang = lang
        self.update_help_content()

    def update_help_content(self):
        title = "马氏距离分析帮助" if self.current_lang == 'zh' else "Mahalanobis Distance Analysis Help"
        content = HELP_CONTENT[self.current_lang]

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