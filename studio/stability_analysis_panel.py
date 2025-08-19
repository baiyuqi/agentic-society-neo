import tkinter as tk
from tkinter import ttk, messagebox
import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from scipy.spatial.distance import mahalanobis

from asociety.personality.analysis_utils import load_personality_data, calculate_mahalanobis_distance
from studio.progress_dialog import ProgressManager
class StabilityAnalysisPanel:
    def __init__(self, parent):
        self.main = ttk.Frame(parent)
        self.main.pack(fill=tk.BOTH, expand=True)

        control_frame = ttk.Frame(self.main)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        title_label = ttk.Label(control_frame, text="稳定性分析 (马氏距离)", font=("Helvetica", 14, "bold"))
        title_label.pack(side=tk.LEFT, padx=(0, 20))

        self.run_button = ttk.Button(control_frame, text="运行分析", command=self.start_analysis)
        self.run_button.pack(side=tk.LEFT)

        self.plot_frame = ttk.Frame(self.main)
        self.plot_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.fig = None
        self.canvas = None
        self.progress_manager = ProgressManager(self.main)

    def start_analysis(self):
        data_dir = "data/db/backup/samples300"
        
        db_files = sorted([f for f in os.listdir(data_dir) if f.endswith('.db')])
        if len(db_files) < 2:
            messagebox.showerror("错误", f"在 '{data_dir}' 中需要至少两个数据库文件。")
            return
            
        file1_path = os.path.join(data_dir, db_files[0])
        file2_path = os.path.join(data_dir, db_files[1])

        def analysis_task(progress_dialog):
            progress_dialog.update_message("正在加载数据...")
            df1 = load_personality_data(file1_path)
            df2 = load_personality_data(file2_path)

            if df1.empty or df2.empty:
                raise ValueError("无法从一个或两个数据库文件中加载画像。")

            progress_dialog.update_message("正在计算马氏距离...")
            distance = calculate_mahalanobis_distance(df1, df2)
            
            return {"distance": distance, "files": (db_files[0], db_files[1])}

        def on_success(results):
            if results:
                self.display_results(results)

        def on_error(error):
            messagebox.showerror("分析错误", f"发生错误: {error}")

        self.progress_manager.run_with_progress(
            analysis_task,
            title="稳定性分析",
            message="正在准备...",
            success_callback=on_success,
            error_callback=on_error
        )

    def display_results(self, results):
        try:
            if self.canvas:
                self.canvas.get_tk_widget().destroy()

            distance = results.get('distance')
            if distance is None:
                messagebox.showerror("绘图错误", "未能计算出有效的距离值。")
                return

            file1, file2 = results.get('files', ('file1', 'file2'))

            self.fig, ax = plt.subplots(figsize=(8, 6))
            
            ax.bar(['Mahalanobis Distance'], [distance], color='skyblue', width=0.4)
            
            ax.set_title(f'Stability Analysis: {file1} vs {file2}')
            ax.set_ylabel('Mahalanobis Distance')
            ax.text(0, distance, f'{distance:.4f}', ha='center', va='bottom', fontsize=12)
            
            self.fig.tight_layout()
            
            self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
            self.canvas.draw()
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        except Exception as e:
            messagebox.showerror("Display Error", f"显示结果时出错: {e}")

    def set_language(self, lang):
        pass

    def setData(self, data, update_callback):
        pass
