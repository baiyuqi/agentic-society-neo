# studio/tsne_panel.py

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import markdown

from asociety.personality.analysis_utils import (
    load_profiles_from_directory, 
    get_combined_and_scaled_data,
    run_tsne
)
from asociety.generator.qwen_analyzer import save_figure_to_bytes, analyze_image_with_text
from studio.collapsible_help_panel import CollapsibleHelpPanel
from studio.progress_dialog import ProgressManager
from studio.analysis_panel_utils import show_analysis_window


HELP_CONTENT = {
    'zh': """
### 功能与用途

t-SNE 是一种强大的**非线性降维技术**，非常擅长将高维数据（如5维的性格向量）投影到2D平面上，同时尽可能保持其局部的相似性结构。

它纯粹用于**可视化探索**，帮助您直观地观察不同画像的数据点在空间中是如何分布和分离的。

### 如何使用

1.  点击“浏览目录...”并选择一个包含多个 `.db` 文件的目录。
2.  点击“运行 t-SNE”。

### 如何解读结果

-   图上的每一个点代表一次性格测试结果，颜色代表其来源文件。
-   **理想情况**：如果多个画像是高度可区分的，那么在t-SNE图上，**相同颜色的点会自然地聚集在一起，形成清晰、分离的“岛屿”或“大陆”**。
-   **混合情况**：如果不同颜色的点大量重叠、混合在一起，则说明这些画像在特征空间中非常相似，难以区分。

### 核心算法介绍

**t-分布随机邻域嵌入 (t-SNE)**：它的工作方式很精妙。

首先，它在原始高维空间中，将数据点之间的欧氏距离转化为一个条件概率，表示点A会选择点B作为其邻居的可能性（距离越近，概率越高）。

然后，它在低维空间（如2D）中也定义一个类似的概率分布（使用更“重尾”的t分布，以缓解“拥挤问题”）。

最后，它通过优化算法，不断调整低维空间中各点的位置，使得两个空间的概率分布尽可能地相似。这个过程保留了数据的局部“邻居”关系，因此非常擅长可视化高维数据的内在流形结构。

**注意**：t-SNE图上簇与簇之间的距离大小不一定具有真实的数学意义，应主要关注点簇的形成和分离情况。
""",
    'en': """
### Function and Purpose

t-SNE is a powerful **nonlinear dimensionality reduction technique** that excels at projecting high-dimensional data (such as 5-dimensional personality vectors) onto a 2D plane while preserving local similarity structures as much as possible.

It is purely used for **visualization exploration**, helping you intuitively observe how data points from different profiles are distributed and separated in space.

### How to Use

1. Click "Browse Directory..." and select a directory containing multiple `.db` files.
2. Click "Run t-SNE".

### How to Interpret Results

- Each point on the plot represents a personality test result, with color representing its source file.
- **Ideal Case**: If multiple profiles are highly distinguishable, then on the t-SNE plot, **points of the same color will naturally cluster together, forming clear, separated "islands" or "continents"**.
- **Mixed Case**: If points of different colors heavily overlap and mix together, it indicates that these profiles are very similar in the feature space and difficult to distinguish.

### Core Algorithm Introduction

**t-Distributed Stochastic Neighbor Embedding (t-SNE)**: Its working mechanism is quite sophisticated.

First, in the original high-dimensional space, it converts Euclidean distances between data points into conditional probabilities, representing the likelihood that point A would choose point B as its neighbor (closer distance means higher probability).

Then, it defines a similar probability distribution in the low-dimensional space (such as 2D) using a "heavier-tailed" t-distribution to alleviate the "crowding problem".

Finally, through optimization algorithms, it continuously adjusts the positions of points in the low-dimensional space to make the probability distributions of the two spaces as similar as possible. This process preserves the local "neighbor" relationships of the data, making it excellent at visualizing the intrinsic manifold structure of high-dimensional data.

**Note**: The distances between clusters on a t-SNE plot do not necessarily have real mathematical meaning; focus should be on cluster formation and separation.
"""
}

class TSNEPanel:
    def __init__(self, parent):
        self.main = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)

        main_content_frame = ttk.Frame(self.main)
        self.main.add(main_content_frame, weight=3)

        control_frame = ttk.Frame(main_content_frame)
        control_frame.pack(fill=tk.X, padx=10, pady=10)

        self.dir_label = ttk.Label(control_frame, text="Selected Directory: None")
        self.dir_label.pack(side=tk.LEFT, padx=(0, 10))

        browse_button = ttk.Button(control_frame, text="Browse Directory...", command=self.browse_directory)
        browse_button.pack(side=tk.LEFT, padx=(0, 10))

        self.analyze_button = ttk.Button(control_frame, text="Run t-SNE", command=self.start_analysis, state=tk.DISABLED)
        self.analyze_button.pack(side=tk.LEFT, padx=(0, 10))

        self.qwen_button = ttk.Button(control_frame, text="结果解析 (AI)", command=self.start_qwen_analysis, state=tk.DISABLED)
        self.qwen_button.pack(side=tk.LEFT, padx=(0, 10))

        # 初始化进度管理器
        self.progress_manager = ProgressManager(self.main)

        self.results_frame = ttk.Frame(main_content_frame)
        self.results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.canvas = None
        self.selected_directory = None
        self.fig = None
        self.profile_names = None

        # 创建可折叠帮助面板
        self.current_lang = 'zh'  # 默认中文
        help_config = {"title": "t-SNE 可视化帮助", "content": HELP_CONTENT['zh']}
        self.collapsible_help = CollapsibleHelpPanel(self.main, help_config, weight=1)

    def browse_directory(self):
        dir_path = filedialog.askdirectory(
            title='Select a directory containing multiple persona DBs',
            initialdir='data/db/backup'
        )
        if dir_path:
            self.selected_directory = dir_path
            self.dir_label.config(text=f"Selected Directory: ...{os.path.basename(dir_path)}")
            self.analyze_button.config(state=tk.NORMAL)
            if self.canvas:
                self.canvas.get_tk_widget().destroy()
                self.canvas = None

    def start_analysis(self):
        """启动带进度显示的t-SNE分析"""
        if not self.selected_directory:
            return

        def analysis_task(progress_dialog):
            """实际的t-SNE分析任务"""
            progress_dialog.update_message("正在加载画像数据...")
            profile_dataframes, profile_names = load_profiles_from_directory(self.selected_directory)

            if progress_dialog.is_cancelled():
                return None

            progress_dialog.update_message("正在处理和标准化数据...")
            scaled_vectors, true_labels = get_combined_and_scaled_data(profile_dataframes)

            if progress_dialog.is_cancelled():
                return None

            progress_dialog.update_message("正在运行t-SNE降维分析...")
            progress_dialog.update_message("t-SNE分析可能需要较长时间，请耐心等待...")
            tsne_results = run_tsne(scaled_vectors)

            if progress_dialog.is_cancelled():
                return None

            progress_dialog.update_message("正在生成可视化图表...")
            return {
                'tsne_results': tsne_results,
                'profile_names': profile_names,
                'true_labels': true_labels
            }

        def on_success(result):
            """分析成功后的处理"""
            if result:
                self.display_results(result)

        def on_error(error):
            """分析出错后的处理"""
            from tkinter import messagebox
            messagebox.showerror("Analysis Error", f"An error occurred: {error}")

        # 使用进度管理器运行分析
        self.progress_manager.run_with_progress(
            analysis_task,
            title="t-SNE分析中...",
            message="正在准备t-SNE分析...",
            success_callback=on_success,
            error_callback=on_error
        )

    def display_results(self, result):
        """显示t-SNE分析结果"""
        try:
            tsne_results = result['tsne_results']
            self.profile_names = result['profile_names']
            true_labels = result['true_labels']

            plot_df = pd.DataFrame({
                't-SNE-1': tsne_results[:, 0],
                't-SNE-2': tsne_results[:, 1],
                'Profile': [self.profile_names[label] for label in true_labels]
            })

            self.fig, ax = plt.subplots(figsize=(12, 8))
            sns.scatterplot(
                data=plot_df, x='t-SNE-1', y='t-SNE-2', hue='Profile',
                s=80, alpha=0.7, palette='viridis', ax=ax
            )
            ax.set_title('t-SNE Visualization of Personality Profiles')
            ax.set_xlabel('t-SNE Dimension 1')
            ax.set_ylabel('t-SNE Dimension 2')
            ax.legend(title='Source Profile')
            ax.grid(True, which='both', linestyle='--', linewidth=0.5)

            if self.canvas:
                self.canvas.get_tk_widget().destroy()
            
            self.canvas = FigureCanvasTkAgg(self.fig, master=self.results_frame)
            self.canvas.draw()
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            self.qwen_button.config(state=tk.NORMAL)
        except Exception as e:
            messagebox.showerror("Analysis Error", f"An error occurred: {e}")
            self.qwen_button.config(state=tk.DISABLED)

    def start_qwen_analysis(self):
        if self.fig is None:
            return

        def analysis_task(progress_dialog):
            progress_dialog.update_message("Preparing image data...")
            image_bytes = save_figure_to_bytes(self.fig)
            if progress_dialog.is_cancelled(): return None

            progress_dialog.update_message("Building analysis prompt...")
            prompt = self._build_tsne_prompt()

            progress_dialog.update_message("Calling AI API for analysis...")
            analysis_result = analyze_image_with_text(image_bytes, prompt)
            return analysis_result

        def on_success(result):
            if result:
                show_analysis_window(self.main, result)

        def on_error(error):
            self._show_message(f"AI Analysis Error: {error}")

        self.progress_manager.run_with_progress(
            analysis_task,
            title="AI Result Analysis",
            message="Connecting to AI...",
            success_callback=on_success,
            error_callback=on_error
        )

    def _build_tsne_prompt(self):
        return f"""
You are a data scientist specializing in data visualization and exploratory data analysis. Your task is to interpret a t-SNE plot of personality profiles.

**Background Information:**
- **Goal**: To visually explore the similarities and differences between multiple AI personality profiles.
- **Technique**: t-SNE (t-Distributed Stochastic Neighbor Embedding), a non-linear technique that visualizes high-dimensional data by giving each datapoint a location in a two-dimensional map. It's particularly good at revealing the underlying structure of the data, such as clusters.
- **Profiles Analyzed**: {', '.join(self.profile_names)}

**Image Content:**
The scatter plot is a 2D representation of the personality test results from different profiles.
- Each point represents a single personality test result.
- The color of each point indicates its original source profile.

**How to Interpret t-SNE:**
- **Clusters**: Points of the same color forming a distinct group (an "island") suggests that the corresponding profile is unique and consistent.
- **Overlap**: Areas where different colors are mixed together indicate that those profiles are very similar and hard to distinguish based on their personality test results.
- **Distances**: **Important:** The relative sizes of the clusters and the distances between them in a t-SNE plot are not directly meaningful. Focus on which groups are well-separated versus which are mixed.

**Your Task:**
1.  **Overall Structure**: Describe the overall pattern you see in the plot. Do the points form distinct clusters, or are they mostly one large, mixed cloud?
2.  **Cluster Analysis**:
    -   Identify which profiles (colors) form clear, well-separated clusters. What does this imply about their uniqueness?
    -   Identify which profiles (colors) are heavily mixed or overlapping with others. What does this imply about their similarity?
3.  **Synthesize and Conclude**:
    -   Based on this visualization, what can you conclude about the distinguishability of these personality profiles?
    -   Are there any interesting patterns, such as one profile bridging two others, or one profile being much more scattered than others?

Please provide your analysis in a clear, structured format.
"""

    def set_language(self, lang):
        """设置语言并更新帮助内容"""
        self.current_lang = lang
        self.update_help_content()

    def update_help_content(self):
        """根据当前语言更新帮助内容"""
        title = "t-SNE 可视化帮助" if self.current_lang == 'zh' else "t-SNE Visualization Help"
        content = HELP_CONTENT[self.current_lang]

        if hasattr(self, 'collapsible_help'):
            self._update_collapsible_help_content(self.collapsible_help, title, content)

    def _update_collapsible_help_content(self, collapsible_help, title, content):
        """更新CollapsibleHelpPanel的内容"""
        if hasattr(collapsible_help, 'help_panel'):
            help_panel = collapsible_help.help_panel
            # 更新标题
            for child in help_panel.winfo_children():
                if isinstance(child, ttk.Label):
                    child.config(text=title)
                    break
            # 更新内容
            if hasattr(help_panel, 'html_widget'):
                html_content = markdown.markdown(content)
                help_panel.html_widget.set_html(html_content)

    def setData(self, appKey, updateTree):
        pass

