# studio/ocean_density_panel.py

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from asociety.personality.analysis_utils import load_personality_data
from studio.progress_dialog import ProgressManager
from studio.collapsible_help_panel import CollapsibleHelpPanel

class OceanDensityPanel:
    def __init__(self, parent):
        self.main = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)

        main_content_frame = ttk.Frame(self.main)
        self.main.add(main_content_frame, weight=3)

        # Control frame
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

        self.run_button = ttk.Button(analysis_frame, text="Run Analysis", command=self.start_analysis, state=tk.DISABLED)
        self.run_button.pack(side=tk.LEFT, padx=5)

        # Toggle between histogram and curve view
        self.show_curves = True  # Default to curves
        self.view_toggle = ttk.Button(analysis_frame, text="Switch to Histogram", command=self.toggle_view)
        self.view_toggle.pack(side=tk.LEFT, padx=5)

        # Density axis maximum selector
        density_frame = ttk.Frame(analysis_frame)
        density_frame.pack(side=tk.LEFT, padx=5)

        ttk.Label(density_frame, text="Density Max:").pack(side=tk.LEFT)
        self.density_max_var = tk.StringVar(value="1.0")
        density_combo = ttk.Combobox(density_frame, textvariable=self.density_max_var,
                                    values=['0.1', '0.2', '0.3', '0.4', '0.5', '0.6', '0.7', '0.8', '0.9', '1.0'],
                                    width=5, state='readonly')
        density_combo.pack(side=tk.LEFT, padx=(5, 0))
        density_combo.bind('<<ComboboxSelected>>', self.on_density_max_change)

        # SVG export button
        self.save_button = ttk.Button(analysis_frame, text="Save to SVG", command=self.save_to_svg, state=tk.DISABLED)
        self.save_button.pack(side=tk.LEFT, padx=5)

        self.selected_files = []

        # Create plot frame
        self.plot_frame = ttk.Frame(main_content_frame)
        self.plot_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.fig = None
        self.canvas = None
        self.progress_manager = ProgressManager(self.main)

        self.results = {}
        self.ocean_dimensions = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']
        self.dimension_labels = {
            'openness': 'Openness',
            'conscientiousness': 'Conscientiousness',
            'extraversion': 'Extraversion',
            'agreeableness': 'Agreeableness',
            'neuroticism': 'Neuroticism'
        }

        self.current_lang = 'zh'
        help_config = {"title": "OCEAN维度密度分析帮助", "content": self._get_help_content()}
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
            self.run_button.config(state=tk.NORMAL if len(self.selected_files) >= 1 else tk.DISABLED)
            self.save_button.config(state=tk.DISABLED)
            if self.canvas:
                self.canvas.get_tk_widget().destroy()
                self.canvas = None

    def clear_files(self):
        self.selected_files = []
        self.update_file_list_label()
        self.run_button.config(state=tk.DISABLED)
        self.save_button.config(state=tk.DISABLED)
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
            self.canvas = None

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
        if len(self.selected_files) < 1:
            messagebox.showwarning("Insufficient Files", "Please select at least 1 file for analysis.")
            return

        self.save_button.config(state=tk.DISABLED)

        def analysis_task(progress_dialog):
            results = {}
            total_files = len(self.selected_files)

            # Load data for each file
            for i, file_path in enumerate(self.selected_files):
                progress_dialog.update_message(f"正在加载 {os.path.basename(file_path)}...")

                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"数据库文件不存在: {file_path}")

                # Load personality data
                df = load_personality_data(file_path)

                # Extract OCEAN dimensions (use raw values, no standardization)
                ocean_data = {}
                for dimension in self.ocean_dimensions:
                    ocean_data[dimension] = df[dimension].values

                # Generate color based on file index
                color = plt.cm.tab10(i % 10)

                # Store results with full file path as key
                results[file_path] = {
                    'ocean_data': ocean_data,
                    'color': color,
                    'label': os.path.basename(file_path).replace('.db', ''),
                    'file_path': file_path
                }

                progress = (i + 1) / total_files * 100
                progress_dialog.set_progress(progress)

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
            # Check if we have results to display
            if not self.results:
                return

            # Clear previous plot
            if self.canvas:
                self.canvas.get_tk_widget().destroy()

            # Create figure with 5 subplots for OCEAN dimensions
            self.fig, axes = plt.subplots(2, 3, figsize=(15, 10))
            # Remove the last subplot (we only need 5 for OCEAN)
            self.fig.delaxes(axes[1, 2])
            axes_flat = [axes[0, 0], axes[0, 1], axes[0, 2], axes[1, 0], axes[1, 1]]

            # Plot each dimension
            for i, dimension in enumerate(self.ocean_dimensions):
                ax = axes_flat[i]

                if self.show_curves:
                    # Plot smooth distribution curves
                    from scipy.stats import gaussian_kde

                    # Set fixed x-range for OCEAN dimensions (0 to 100)
                    x_min = 0
                    x_max = 100
                    x = np.linspace(x_min, x_max, 1000)

                    for file_path, result in self.results.items():
                        values = result['ocean_data'][dimension]
                        color = result['color']
                        label = result['label']

                        # Create kernel density estimate for smooth curve
                        if len(values) > 1:
                            kde = gaussian_kde(values)
                            y = kde(x)

                            # Plot smooth curve
                            ax.plot(x, y, color=color, linewidth=2, label=label)

                            # Fill under curve for better visibility
                            ax.fill_between(x, y, alpha=0.3, color=color)

                else:
                    # Plot histograms with fixed range 0-100
                    for file_path, result in self.results.items():
                        values = result['ocean_data'][dimension]
                        color = result['color']
                        label = result['label']

                        # Plot histogram with fixed range
                        counts, bin_edges, _ = ax.hist(
                            values, bins='auto', density=True, alpha=0.6,
                            color=color, edgecolor='black', label=label,
                            range=(0, 100)
                        )

                # Configure subplot
                ax.set_title(f'{self.dimension_labels[dimension]}', fontsize=12, fontweight='bold')
                ax.set_xlabel('Score')
                ax.set_ylabel('Probability Density')
                ax.set_xlim(0, 100)  # Set fixed x-axis range for OCEAN dimensions

                # Set fixed y-axis range for density using selected maximum
                density_max = float(self.density_max_var.get())
                ax.set_ylim(0, density_max)

                ax.grid(True, which='both', linestyle='--', linewidth=0.5)

            # Add legend to the first subplot
            if len(self.results) > 0:
                first_file_path = list(self.results.keys())[0]
                first_result = self.results[first_file_path]
                axes_flat[0].legend()

            # Add main title
            if self.show_curves:
                self.fig.suptitle('OCEAN Personality Dimensions Distribution (KDE)', fontsize=16, fontweight='bold')
            else:
                self.fig.suptitle('OCEAN Personality Dimensions Distribution (Histogram)', fontsize=16, fontweight='bold')

            # Adjust layout
            self.fig.tight_layout(rect=[0, 0, 1, 0.96])

            # Create canvas
            self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
            self.canvas.draw()
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            # Enable SVG export
            self.save_button.config(state=tk.NORMAL)

        except Exception as e:
            messagebox.showerror("显示错误", f"显示结果时出错: {e}")

    def toggle_view(self):
        """Toggle between curve and histogram view"""
        self.show_curves = not self.show_curves
        if self.show_curves:
            self.view_toggle.config(text="Switch to Histogram")
        else:
            self.view_toggle.config(text="Switch to Curves")

        # Redisplay results with new view mode
        if self.results:
            self.display_results()

    def on_density_max_change(self, event=None):
        """Handle density axis maximum value change"""
        # Redisplay results with new density axis range
        if self.results:
            self.display_results()

    def save_to_svg(self):
        """Save the current matplotlib figure as SVG vector image"""
        if self.fig is None:
            messagebox.showwarning("No Plot", "Please run analysis first to generate a plot.")
            return

        file_path = filedialog.asksaveasfilename(
            title="Save Plot as SVG",
            defaultextension=".svg",
            filetypes=[("SVG Files", "*.svg"), ("All Files", "*.*")]
        )

        if file_path:
            self.fig.savefig(file_path, format="svg", bbox_inches="tight")
            messagebox.showinfo("Success", f"Plot saved successfully to:\n{file_path}")

    def _get_help_content(self):
        """Generate help content for this panel"""
        return """
### 功能与用途

此工具用于在**五个子图中分别绘制OCEAN人格维度的密度分布**，便于直观比较不同数据源在各个维度上的分布特征。

与马氏距离分析不同，此工具使用**欧几里得距离（一维标量）**，直接使用原始人格得分，不进行标准化处理，规避了高维空间的可视化问题。

### 如何使用

1.  点击"添加文件..."按钮，选择您想要分析的 `.db` 文件。
2.  重复步骤1，添加多个文件（至少需要1个文件）。
3.  点击"运行分析"进行分析。
4.  使用"切换为直方图/切换为曲线"按钮在两种视图模式间切换。
5.  分析完成后，可以查看五个维度的分布图表。
6.  点击"保存为SVG"将图表保存为矢量图像。
7.  点击"清除文件"可以清空已选择的文件列表。

### 如何解读结果

-   **五个子图**: 分别对应OCEAN人格模型的五个维度：
    -   **Openness (开放性)**: 对新体验的开放程度 (0-100分)
    -   **Conscientiousness (尽责性)**: 组织性和责任感 (0-100分)
    -   **Extraversion (外向性)**: 社交活跃度和能量水平 (0-100分)
    -   **Agreeableness (宜人性)**: 合作性和同情心 (0-100分)
    -   **Neuroticism (神经质)**: 情绪不稳定性和焦虑倾向 (0-100分)

-   **曲线模式 (KDE)**: 显示平滑的概率密度曲线，便于观察分布形状
-   **直方图模式**: 显示传统的直方图，便于观察数据分布
-   **坐标范围**: 所有维度的x轴都固定为0-100分，便于跨维度比较

### 核心算法说明

此分析使用**原始人格得分**，不进行任何标准化或转换。每个维度的分析都是独立的一维分析，使用欧几里得距离的概念（在单维度上等同于绝对值距离）。这种方法避免了高维空间的复杂性，让每个维度的分布特征更加清晰直观。

### 适用场景

- 当您想要分别分析OCEAN五个维度的分布特征时
- 当您需要比较不同数据源在特定人格维度上的差异时
- 当您希望避免高维空间可视化复杂性时
- 当您关注单个维度的具体分布形态时
"""

    def set_language(self, lang):
        self.current_lang = lang
        self.update_help_content()

    def update_help_content(self):
        title = "OCEAN维度密度分析帮助" if self.current_lang == 'zh' else "OCEAN Dimension Density Analysis Help"
        content = self._get_help_content()

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
                import markdown
                html_content = markdown.markdown(content)
                help_panel.html_widget.set_html(html_content)

    def setData(self, appKey, updateTree):
        pass