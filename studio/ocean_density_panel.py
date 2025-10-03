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

        # Distance metrics button
        self.distance_button = ttk.Button(analysis_frame, text="Calculate Distances", command=self.calculate_distances, state=tk.DISABLED)
        self.distance_button.pack(side=tk.LEFT, padx=5)

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
            self.distance_button.config(state=tk.DISABLED)
            if self.canvas:
                self.canvas.get_tk_widget().destroy()
                self.canvas = None

    def clear_files(self):
        self.selected_files = []
        self.update_file_list_label()
        self.run_button.config(state=tk.DISABLED)
        self.save_button.config(state=tk.DISABLED)
        self.distance_button.config(state=tk.DISABLED)
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
        self.distance_button.config(state=tk.DISABLED)

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

            # Enable SVG export and distance calculation
            self.save_button.config(state=tk.NORMAL)
            self.distance_button.config(state=tk.NORMAL)

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

    def calculate_distances(self):
        """Calculate distance metrics between datasets and human.db"""
        if not self.results:
            messagebox.showwarning("No Analysis Results", "Please run analysis first to generate results.")
            return

        # Check if human.db exists
        human_db_path = "data/db/backup/human.db"
        if not os.path.exists(human_db_path):
            messagebox.showwarning("Human DB Not Found", f"human.db not found at: {human_db_path}")
            return

        def distance_task(progress_dialog):
            from asociety.personality.analysis_utils import load_personality_data
            import numpy as np
            from scipy.stats import wasserstein_distance
            from sklearn.metrics.pairwise import cosine_similarity

            # Load human data
            progress_dialog.update_message("正在加载 human.db 数据...")
            human_df = load_personality_data(human_db_path)
            human_data = human_df[self.ocean_dimensions].values

            distance_results = {}
            total_files = len(self.results)

            for i, (file_path, result) in enumerate(self.results.items()):
                progress_dialog.update_message(f"正在计算 {result['label']} 的距离...")

                # Get current dataset data
                current_data = []
                for dimension in self.ocean_dimensions:
                    current_data.append(result['ocean_data'][dimension])
                current_data = np.array(current_data).T  # Transpose to get samples x dimensions

                distances = {}

                # Calculate Wasserstein distance for each dimension
                wasserstein_distances = []
                for dim_idx, dimension in enumerate(self.ocean_dimensions):
                    human_dim = human_data[:, dim_idx]
                    current_dim = current_data[:, dim_idx]
                    wd = wasserstein_distance(human_dim, current_dim)
                    wasserstein_distances.append(wd)
                distances['Wasserstein_Mean'] = np.mean(wasserstein_distances)
                distances['Wasserstein_Std'] = np.std(wasserstein_distances)

                # Calculate Sliced Wasserstein approximation
                sliced_wasserstein = self._calculate_sliced_wasserstein(human_data, current_data)
                distances['Sliced_Wasserstein'] = sliced_wasserstein

                # Calculate Fréchet distance approximation
                frechet_distance = self._calculate_frechet_distance(human_data, current_data)
                distances['Fréchet_Distance'] = frechet_distance

                # Calculate Euclidean distance between means
                human_mean = np.mean(human_data, axis=0)
                current_mean = np.mean(current_data, axis=0)
                distances['Euclidean_Mean_Distance'] = np.linalg.norm(human_mean - current_mean)

                # Calculate cosine similarity
                cosine_sim = cosine_similarity([human_mean], [current_mean])[0][0]
                distances['Cosine_Similarity'] = cosine_sim

                # Calculate Maximum Mean Discrepancy (MMD)
                mmd_distance = self._calculate_mmd(human_data, current_data)
                distances['MMD'] = mmd_distance

                # Calculate Averaged Monotonic Wasserstein (AMW)
                amw_distance = self._calculate_amw(human_data, current_data)
                distances['AMW'] = amw_distance

                distance_results[result['label']] = distances

                progress = (i + 1) / total_files * 100
                progress_dialog.set_progress(progress)

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
        """Calculate Sliced Wasserstein distance approximation"""
        import numpy as np
        from scipy.stats import wasserstein_distance

        n_dims = data1.shape[1]
        projections = np.random.randn(n_projections, n_dims)
        projections = projections / np.linalg.norm(projections, axis=1, keepdims=True)

        sw_distances = []
        for proj in projections:
            proj_data1 = data1 @ proj
            proj_data2 = data2 @ proj
            wd = wasserstein_distance(proj_data1, proj_data2)
            sw_distances.append(wd)

        return np.mean(sw_distances)

    def _calculate_frechet_distance(self, data1, data2):
        """Calculate Fréchet distance approximation between two multivariate distributions"""
        import numpy as np
        from scipy.linalg import sqrtm

        # Calculate means and covariances
        mu1 = np.mean(data1, axis=0)
        mu2 = np.mean(data2, axis=0)

        # Ensure we have enough samples for covariance calculation
        if len(data1) < 2 or len(data2) < 2:
            return np.nan

        sigma1 = np.cov(data1, rowvar=False)
        sigma2 = np.cov(data2, rowvar=False)

        # Add stronger regularization for numerical stability
        reg = 1e-3
        sigma1 += np.eye(sigma1.shape[0]) * reg
        sigma2 += np.eye(sigma2.shape[0]) * reg

        try:
            # Calculate matrix square root using scipy's sqrtm with error handling
            sigma_product = sigma1 @ sigma2

            # Check if matrix is positive definite
            eigenvalues = np.linalg.eigvals(sigma_product)
            if np.any(eigenvalues < 0):
                # If not positive definite, use alternative approach
                trace_term = np.trace(sigma1 + sigma2 - 2 * np.sqrt(np.abs(sigma_product)))
            else:
                # Use proper matrix square root
                sqrt_sigma_product = sqrtm(sigma_product)
                trace_term = np.trace(sigma1 + sigma2 - 2 * sqrt_sigma_product)

            # Calculate mean term
            mean_term = np.sum((mu1 - mu2) ** 2)

            # Fréchet distance approximation
            frechet_dist = mean_term + trace_term

            # Ensure result is non-negative
            frechet_dist = max(0, frechet_dist)

            return np.sqrt(frechet_dist)

        except (np.linalg.LinAlgError, ValueError):
            # Fallback: use simplified distance if matrix operations fail
            mean_term = np.sum((mu1 - mu2) ** 2)
            cov_diff = np.linalg.norm(sigma1 - sigma2, 'fro')
            return np.sqrt(mean_term + cov_diff)

    def _calculate_mmd(self, data1, data2, kernel='rbf', gamma=None):
        """Calculate Maximum Mean Discrepancy (MMD) between two datasets"""
        import numpy as np
        from sklearn.metrics.pairwise import pairwise_kernels

        n1 = data1.shape[0]
        n2 = data2.shape[0]

        # Set default gamma if not provided
        if gamma is None:
            # Use median heuristic for RBF kernel
            if kernel == 'rbf':
                from sklearn.metrics.pairwise import euclidean_distances
                combined_data = np.vstack([data1, data2])
                pairwise_distances = euclidean_distances(combined_data)
                gamma = 1.0 / (2.0 * np.median(pairwise_distances) ** 2)
            else:
                gamma = 1.0 / data1.shape[1]  # Default to 1/dimensions

        # Calculate kernel matrices
        K11 = pairwise_kernels(data1, metric=kernel, gamma=gamma)
        K22 = pairwise_kernels(data2, metric=kernel, gamma=gamma)
        K12 = pairwise_kernels(data1, data2, metric=kernel, gamma=gamma)

        # Calculate MMD^2
        mmd_squared = (np.sum(K11) / (n1 * n1) +
                      np.sum(K22) / (n2 * n2) -
                      2 * np.sum(K12) / (n1 * n2))

        # Ensure non-negativity and return MMD
        mmd = np.sqrt(max(0, mmd_squared))

        return mmd

    def _calculate_amw(self, data1, data2):
        """Calculate Averaged Monotonic Wasserstein (AMW) distance"""
        import numpy as np
        from scipy.stats import wasserstein_distance

        n_traits = data1.shape[1]

        # Calculate 1D Wasserstein-1 distance for each trait
        wasserstein_distances = []
        for trait_idx in range(n_traits):
            trait_data1 = data1[:, trait_idx]
            trait_data2 = data2[:, trait_idx]

            # Calculate 1D Wasserstein-1 distance
            wd = wasserstein_distance(trait_data1, trait_data2)
            wasserstein_distances.append(wd)

        # AMW is the average of 1D Wasserstein distances across all traits
        amw = np.mean(wasserstein_distances)

        return amw

    def _display_distance_results(self, distance_results):
        """Display distance results in a popup window"""
        import tkinter as tk
        from tkinter import ttk

        # Create popup window
        popup = tk.Toplevel()
        popup.title("距离指标计算结果")
        popup.geometry("800x400")

        # Create frame for table
        frame = ttk.Frame(popup)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create treeview
        columns = ['Dataset'] + list(next(iter(distance_results.values())).keys())
        tree = ttk.Treeview(frame, columns=columns, show='headings', height=15)

        # Configure columns
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120, anchor='center')

        # Add data
        for dataset, metrics in distance_results.items():
            values = [dataset] + [f"{value:.4f}" if isinstance(value, (int, float)) else str(value)
                                for value in metrics.values()]
            tree.insert('', 'end', values=values)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        tree.pack(fill=tk.BOTH, expand=True)

        # Add close button
        close_button = ttk.Button(popup, text="关闭", command=popup.destroy)
        close_button.pack(pady=10)