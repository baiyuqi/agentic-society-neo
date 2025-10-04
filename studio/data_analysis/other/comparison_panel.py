# studio/comparison_panel.py

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import glob
from itertools import combinations
import markdown

from asociety.personality.analysis_utils import (
    load_profiles_from_directory,
    get_combined_and_scaled_data,
    run_pca,
    calculate_mahalanobis_distance,
    load_personality_data
)
from studio.collapsible_help_panel import CollapsibleHelpPanel
from studio.progress_dialog import ProgressManager
from studio.help_constants import helpcnstants
HELP_CONTENT = helpcnstants['comparison']

class ComparisonPanel:
    def __init__(self, parent):
        self.main = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)

        main_content_frame = ttk.Frame(self.main)
        self.main.add(main_content_frame, weight=3)

        control_frame = ttk.Frame(main_content_frame)
        control_frame.pack(fill=tk.X, padx=10, pady=10)

        self.dir_label = ttk.Label(control_frame, text="Selected Directory: None")
        self.dir_label.pack(side=tk.LEFT, padx=(0, 10))

        browse_button = ttk.Button(control_frame, text="选择目录...", command=self.browse_directory)
        browse_button.pack(side=tk.LEFT, padx=(0, 10))

        self.notebook = ttk.Notebook(main_content_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Distribution tab
        self.dist_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.dist_frame, text="目录分布对比")

        # 创建分布对比tab的水平分割
        dist_paned = ttk.PanedWindow(self.dist_frame, orient=tk.HORIZONTAL)
        dist_paned.pack(fill=tk.BOTH, expand=True)

        # 左侧：控制和结果
        dist_left_frame = ttk.Frame(dist_paned)
        dist_paned.add(dist_left_frame, weight=3)

        dist_control_frame = ttk.Frame(dist_left_frame)
        dist_control_frame.pack(fill=tk.X, padx=10, pady=10)

        self.dist_analyze_button = ttk.Button(dist_control_frame, text="运行分布分析", command=self.start_distribution_analysis, state=tk.DISABLED)
        self.dist_analyze_button.pack(side=tk.LEFT)

        self.dist_results_frame = ttk.Frame(dist_left_frame)
        self.dist_results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 右侧：可折叠帮助面板
        self.current_lang = 'zh'  # 默认中文
        help_config = {"title": "分布对比帮助", "content": HELP_CONTENT['zh']['dist']}
        self.dist_collapsible_help = CollapsibleHelpPanel(dist_paned, help_config, weight=1)

        # Heatmap tab
        self.heatmap_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.heatmap_frame, text="距离热力图")

        # 创建热力图tab的水平分割
        heatmap_paned = ttk.PanedWindow(self.heatmap_frame, orient=tk.HORIZONTAL)
        heatmap_paned.pack(fill=tk.BOTH, expand=True)

        # 左侧：控制和结果
        heatmap_left_frame = ttk.Frame(heatmap_paned)
        heatmap_paned.add(heatmap_left_frame, weight=3)

        heatmap_control_frame = ttk.Frame(heatmap_left_frame)
        heatmap_control_frame.pack(fill=tk.X, padx=10, pady=10)

        self.heatmap_analyze_button = ttk.Button(heatmap_control_frame, text="生成热力图", command=self.start_heatmap_analysis, state=tk.DISABLED)
        self.heatmap_analyze_button.pack(side=tk.LEFT)

        self.heatmap_results_frame = ttk.Frame(heatmap_left_frame)
        self.heatmap_results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 右侧：可折叠帮助面板
        help_config = {"title": "热力图帮助", "content": HELP_CONTENT['zh']['heatmap']}
        self.heatmap_collapsible_help = CollapsibleHelpPanel(heatmap_paned, help_config, weight=1)

        self.selected_directory = None
        self.dist_canvas = None
        self.heatmap_canvas = None

        # 初始化进度管理器
        self.progress_manager = ProgressManager(self.main)

    def set_language(self, lang):
        """设置语言并更新帮助内容"""
        self.current_lang = lang
        self.update_help_content()

    def update_help_content(self):
        """根据当前语言更新帮助内容"""
        # 获取语言对应的标题和内容
        if self.current_lang == 'zh':
            dist_title = "分布对比帮助"
            heatmap_title = "热力图帮助"
        else:
            dist_title = "Distribution Analysis Help"
            heatmap_title = "Heatmap Analysis Help"

        dist_content = HELP_CONTENT[self.current_lang]['dist']
        heatmap_content = HELP_CONTENT[self.current_lang]['heatmap']

        # 更新分布对比帮助内容
        if hasattr(self, 'dist_collapsible_help'):
            self._update_collapsible_help_content(
                self.dist_collapsible_help, dist_title, dist_content
            )

        # 更新热力图帮助内容
        if hasattr(self, 'heatmap_collapsible_help'):
            self._update_collapsible_help_content(
                self.heatmap_collapsible_help, heatmap_title, heatmap_content
            )

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

    def browse_directory(self):
        dir_path = filedialog.askdirectory(title='Select Directory for Comparison Analysis', initialdir='data/db/backup')
        if dir_path:
            self.selected_directory = dir_path
            self.dir_label.config(text=f"Selected Directory: {dir_path}")
            self.dist_analyze_button.config(state=tk.NORMAL)
            self.heatmap_analyze_button.config(state=tk.NORMAL)
            if self.dist_canvas:
                self.dist_canvas.get_tk_widget().destroy(); self.dist_canvas = None
            if self.heatmap_canvas:
                self.heatmap_canvas.get_tk_widget().destroy(); self.heatmap_canvas = None

    def run_distribution_analysis(self):
        if not self.selected_directory: return
        try:
            profile_dataframes, profile_names = load_profiles_from_directory(self.selected_directory)
            scaled_vectors, true_labels = get_combined_and_scaled_data(profile_dataframes)
            principal_components, explained_variance = run_pca(scaled_vectors)
            
            if self.dist_canvas: self.dist_canvas.get_tk_widget().destroy()

            fig = plt.figure(figsize=(20, 10))
            gs = fig.add_gridspec(2, 5)
            fig.suptitle('Directory Distribution Comparison', fontsize=20, weight='bold')

            all_dfs = [df.assign(Profile=name) for df, name in zip(profile_dataframes, profile_names)]
            combined_df = pd.concat(all_dfs, ignore_index=True)
            
            for i, trait in enumerate(profile_dataframes[0].columns):
                ax = fig.add_subplot(gs[0, i])
                sns.violinplot(x='Profile', y=trait, data=combined_df, ax=ax, palette="viridis")
                ax.set_title(trait.capitalize()); ax.set_xlabel(''); ax.set_ylabel('Score')
                ax.tick_params(axis='x', rotation=45)

            ax_pca = fig.add_subplot(gs[1, :])
            plot_df = pd.DataFrame({'PC1': principal_components[:, 0], 'PC2': principal_components[:, 1], 'Profile': [profile_names[label] for label in true_labels]})
            sns.scatterplot(data=plot_df, x='PC1', y='PC2', hue='Profile', s=80, alpha=0.7, palette='viridis', ax=ax_pca)
            ax_pca.set_title('Multivariate Comparison (PCA)', fontsize=14)
            ax_pca.set_xlabel(f'PC 1 ({explained_variance[0]:.1%} variance)'); ax_pca.set_ylabel(f'PC 2 ({explained_variance[1]:.1%} variance)')
            ax_pca.legend(title='Profile'); ax_pca.grid(True, linestyle='--')

            plt.tight_layout(rect=[0, 0, 1, 0.96])
            
            self.dist_canvas = FigureCanvasTkAgg(fig, master=self.dist_results_frame)
            self.dist_canvas.draw()
            self.dist_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        except Exception as e:
            messagebox.showerror("Analysis Error", f"An error occurred: {e}")

    def run_heatmap_analysis(self):
        if not self.selected_directory: return
        try:
            db_files = sorted(glob.glob(os.path.join(self.selected_directory, '*.db')))
            if len(db_files) < 2:
                messagebox.showinfo("Info", "Need at least two .db files for heatmap comparison.")
                return

            profiles = {os.path.basename(p): load_personality_data(p) for p in db_files}
            profile_names = list(profiles.keys())
            distance_matrix = pd.DataFrame(np.zeros((len(profile_names), len(profile_names))), index=profile_names, columns=profile_names)

            for (name1, df1), (name2, df2) in combinations(profiles.items(), 2):
                try:
                    dist = calculate_mahalanobis_distance(df1, df2)
                    distance_matrix.loc[name1, name2] = dist
                    distance_matrix.loc[name2, name1] = dist
                except Exception as e:
                    distance_matrix.loc[name1, name2] = np.nan
                    distance_matrix.loc[name2, name1] = np.nan

            if self.heatmap_canvas: self.heatmap_canvas.get_tk_widget().destroy()
            
            fig, ax = plt.subplots(figsize=(14, 10))
            sns.heatmap(distance_matrix, ax=ax, annot=True, fmt=".2f", cmap="viridis", linewidths=.5)
            ax.set_title('Pairwise Mahalanobis Distance Matrix', fontsize=16, weight='bold')
            ax.set_xlabel('Profile', fontsize=12); ax.set_ylabel('Profile', fontsize=12)
            plt.xticks(rotation=45, ha='right'); plt.yticks(rotation=0)
            fig.tight_layout()

            self.heatmap_canvas = FigureCanvasTkAgg(fig, master=self.heatmap_results_frame)
            self.heatmap_canvas.draw()
            self.heatmap_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        except Exception as e:
            messagebox.showerror("Analysis Error", f"An error occurred: {e}")

    def start_distribution_analysis(self):
        """启动带进度显示的分布分析"""
        if not self.selected_directory:
            return

        def analysis_task(progress_dialog):
            """实际的分布分析任务"""
            progress_dialog.update_message("正在加载画像数据...")
            profile_dataframes, profile_names = load_profiles_from_directory(self.selected_directory)

            if progress_dialog.is_cancelled():
                return None

            progress_dialog.update_message("正在处理和标准化数据...")
            scaled_vectors, true_labels = get_combined_and_scaled_data(profile_dataframes)

            if progress_dialog.is_cancelled():
                return None

            progress_dialog.update_message("正在进行PCA分析...")
            principal_components, explained_variance = run_pca(scaled_vectors)

            if progress_dialog.is_cancelled():
                return None

            progress_dialog.update_message("正在生成可视化图表...")

            fig = plt.figure(figsize=(20, 10))
            gs = fig.add_gridspec(2, 5)
            fig.suptitle('Directory Distribution Comparison', fontsize=20, weight='bold')

            all_dfs = [df.assign(Profile=name) for df, name in zip(profile_dataframes, profile_names)]
            combined_df = pd.concat(all_dfs, ignore_index=True)

            for i, trait in enumerate(profile_dataframes[0].columns):
                ax = fig.add_subplot(gs[0, i])
                sns.violinplot(x='Profile', y=trait, data=combined_df, ax=ax, palette="viridis")
                ax.set_title(trait.capitalize()); ax.set_xlabel(''); ax.set_ylabel('Score')
                ax.tick_params(axis='x', rotation=45)

            ax_pca = fig.add_subplot(gs[1, :])
            plot_df = pd.DataFrame({'PC1': principal_components[:, 0], 'PC2': principal_components[:, 1], 'Profile': [profile_names[label] for label in true_labels]})
            sns.scatterplot(data=plot_df, x='PC1', y='PC2', hue='Profile', s=80, alpha=0.7, palette='viridis', ax=ax_pca)
            ax_pca.set_title('Multivariate Comparison (PCA)', fontsize=14)
            ax_pca.set_xlabel(f'PC 1 ({explained_variance[0]:.1%} variance)'); ax_pca.set_ylabel(f'PC 2 ({explained_variance[1]:.1%} variance)')
            ax_pca.legend(title='Profile'); ax_pca.grid(True, linestyle='--')

            plt.tight_layout(rect=[0, 0, 1, 0.96])

            return fig

        def on_success(fig):
            """分析成功后的处理"""
            if fig:
                self.display_distribution_results(fig)

        def on_error(error):
            """分析出错后的处理"""
            messagebox.showerror("Analysis Error", f"An error occurred: {error}")

        # 使用进度管理器运行分析
        self.progress_manager.run_with_progress(
            analysis_task,
            title="分布分析中...",
            message="正在准备分析...",
            success_callback=on_success,
            error_callback=on_error
        )

    def display_distribution_results(self, fig):
        """显示分布分析结果"""
        try:
            if self.dist_canvas:
                self.dist_canvas.get_tk_widget().destroy()

            self.dist_canvas = FigureCanvasTkAgg(fig, master=self.dist_results_frame)
            self.dist_canvas.draw()
            self.dist_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        except Exception as e:
            messagebox.showerror("Display Error", f"An error occurred while displaying results: {e}")

    def start_heatmap_analysis(self):
        """启动带进度显示的热力图分析"""
        if not self.selected_directory:
            return

        def analysis_task(progress_dialog):
            """实际的热力图分析任务"""
            progress_dialog.update_message("正在加载画像数据...")
            db_files = sorted(glob.glob(os.path.join(self.selected_directory, '*.db')))
            if len(db_files) < 2:
                raise ValueError("Need at least two .db files for heatmap comparison.")

            profiles = {os.path.basename(p): load_personality_data(p) for p in db_files}
            profile_names = list(profiles.keys())

            if progress_dialog.is_cancelled():
                return None

            progress_dialog.update_message("正在计算马氏距离矩阵...")
            distance_matrix = pd.DataFrame(np.zeros((len(profile_names), len(profile_names))), index=profile_names, columns=profile_names)

            total_pairs = len(list(combinations(profiles.items(), 2)))
            current_pair = 0

            for (name1, df1), (name2, df2) in combinations(profiles.items(), 2):
                if progress_dialog.is_cancelled():
                    return None

                current_pair += 1
                progress_dialog.update_message(f"正在计算距离 ({current_pair}/{total_pairs})...")

                try:
                    dist = calculate_mahalanobis_distance(df1, df2)
                    distance_matrix.loc[name1, name2] = dist
                    distance_matrix.loc[name2, name1] = dist
                except Exception as e:
                    distance_matrix.loc[name1, name2] = np.nan
                    distance_matrix.loc[name2, name1] = np.nan

            if progress_dialog.is_cancelled():
                return None

            progress_dialog.update_message("正在生成热力图...")
            fig, ax = plt.subplots(figsize=(14, 10))
            sns.heatmap(distance_matrix, ax=ax, annot=True, fmt=".2f", cmap="viridis", linewidths=.5)
            ax.set_title('Pairwise Mahalanobis Distance Matrix', fontsize=16, weight='bold')
            ax.set_xlabel('Profile', fontsize=12); ax.set_ylabel('Profile', fontsize=12)
            plt.xticks(rotation=45, ha='right'); plt.yticks(rotation=0)
            fig.tight_layout()

            return fig

        def on_success(fig):
            """分析成功后的处理"""
            if fig:
                self.display_heatmap_results(fig)

        def on_error(error):
            """分析出错后的处理"""
            messagebox.showerror("Analysis Error", f"An error occurred: {error}")

        # 使用进度管理器运行分析
        self.progress_manager.run_with_progress(
            analysis_task,
            title="热力图分析中...",
            message="正在准备分析...",
            success_callback=on_success,
            error_callback=on_error
        )

    def display_heatmap_results(self, fig):
        """显示热力图分析结果"""
        try:
            if self.heatmap_canvas:
                self.heatmap_canvas.get_tk_widget().destroy()

            self.heatmap_canvas = FigureCanvasTkAgg(fig, master=self.heatmap_results_frame)
            self.heatmap_canvas.draw()
            self.heatmap_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        except Exception as e:
            messagebox.showerror("Display Error", f"An error occurred while displaying results: {e}")

    def setData(self, appKey, updateTree):
        pass


