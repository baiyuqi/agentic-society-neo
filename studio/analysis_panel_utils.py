# studio/analysis_panel_utils.py
import tkinter as tk
from tkinter import ttk
import markdown
from tkhtmlview import HTMLScrolledText

def show_analysis_window(parent, analysis_text):
    """
    创建一个新窗口来显示AI分析结果。

    Args:
        parent: 父组件。
        analysis_text (str): 要显示的Markdown格式的分析文本。
    """
    top = tk.Toplevel(parent)
    top.title("AI 结果解析")
    top.geometry("800x600")

    html_frame = ttk.Frame(top)
    html_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    html_content = markdown.markdown(analysis_text)
    
    html_widget = HTMLScrolledText(
        html_frame,
        html=html_content,
        background="#ffffff",
        foreground="#333333",
        font=("Microsoft YaHei", 9),
        wrap="word",
        padx=12,
        pady=12,
        spacing1=3,
        spacing2=1,
        spacing3=3
    )
    html_widget.pack(fill=tk.BOTH, expand=True)
