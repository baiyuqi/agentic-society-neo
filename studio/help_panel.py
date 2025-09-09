# studio/help_panel.py
import tkinter as tk
from tkinter import ttk
import markdown
from tkhtmlview import HTMLScrolledText
import re

class MarkdownRenderer:
    """简单的Markdown渲染器，支持基本的Markdown语法"""

    @staticmethod
    def render_to_text_widget(text_widget, markdown_content):
        """将markdown内容渲染到Text widget中"""
        text_widget.config(state=tk.NORMAL)
        text_widget.delete(1.0, tk.END)

        # 配置文本样式
        text_widget.tag_configure("h1", font=("Helvetica", 16, "bold"), spacing1=10, spacing3=5)
        text_widget.tag_configure("h2", font=("Helvetica", 14, "bold"), spacing1=8, spacing3=4)
        text_widget.tag_configure("h3", font=("Helvetica", 12, "bold"), spacing1=6, spacing3=3)
        text_widget.tag_configure("bold", font=("Helvetica", 11, "bold"))
        text_widget.tag_configure("italic", font=("Helvetica", 11, "italic"))
        text_widget.tag_configure("code", font=("Courier", 10), background="#f0f0f0")
        text_widget.tag_configure("bullet", lmargin1=20, lmargin2=40)
        text_widget.tag_configure("normal", font=("Helvetica", 11))

        lines = markdown_content.split('\n')
        for line in lines:
            MarkdownRenderer._render_line(text_widget, line)

        text_widget.config(state=tk.DISABLED)

    @staticmethod
    def _render_line(text_widget, line):
        """渲染单行markdown"""
        line = line.rstrip()

        # 标题
        if line.startswith('### '):
            text_widget.insert(tk.END, line[4:] + '\n', "h3")
        elif line.startswith('## '):
            text_widget.insert(tk.END, line[3:] + '\n', "h2")
        elif line.startswith('# '):
            text_widget.insert(tk.END, line[2:] + '\n', "h1")
        # 列表项
        elif line.startswith('-   ') or line.startswith('*   '):
            content = line[4:]
            text_widget.insert(tk.END, "• ", "bullet")
            MarkdownRenderer._render_inline(text_widget, content)
            text_widget.insert(tk.END, '\n', "bullet")
        # 空行
        elif line.strip() == '':
            text_widget.insert(tk.END, '\n', "normal")
        # 普通文本
        else:
            MarkdownRenderer._render_inline(text_widget, line)
            text_widget.insert(tk.END, '\n', "normal")

    @staticmethod
    def _render_inline(text_widget, text):
        """渲染行内markdown元素"""
        # 处理粗体 **text**
        parts = re.split(r'(\*\*.*?\*\*)', text)
        for part in parts:
            if part.startswith('**') and part.endswith('**'):
                text_widget.insert(tk.END, part[2:-2], "bold")
            else:
                # 处理行内代码 `code`
                code_parts = re.split(r'(`.*?`)', part)
                for code_part in code_parts:
                    if code_part.startswith('`') and code_part.endswith('`'):
                        text_widget.insert(tk.END, code_part[1:-1], "code")
                    else:
                        text_widget.insert(tk.END, code_part, "normal")

class HelpPanel(ttk.Frame):
    """
    A reusable side panel for displaying help text.
    It includes a title and a scrollable, read-only text area.
    """
    def __init__(self, parent, title="帮助 (Help)", content=""):
        # Set a fixed width for the panel
        super().__init__(parent, width=300)
        # Prevent the frame from shrinking to its content's size, maintaining the fixed width
        self.pack_propagate(False)

        # --- Title ---
        title_label = ttk.Label(self, text=title, font=("Helvetica", 13, "bold"))
        title_label.pack(pady=(5, 10), padx=10, anchor='n')

        # --- Separator ---
        separator = ttk.Separator(self, orient='horizontal')
        separator.pack(fill='x', padx=10, pady=0)

        # --- Scrollable HTML Text Area ---
        text_frame = ttk.Frame(self)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 将markdown转换为HTML
        html_content = markdown.markdown(content)

        # 创建HTML显示组件，通过参数调整显示效果
        self.html_widget = HTMLScrolledText(
            text_frame,
            html=html_content,
            background="#ffffff",
            foreground="#333333",
            font=("Microsoft YaHei", 9),  # 减小字体大小
            wrap="word",
            padx=12,  # 减小内边距
            pady=12,
            spacing1=3,  # 减小段落前间距
            spacing2=1,  # 减小行间距
            spacing3=3   # 减小段落后间距
        )
        self.html_widget.pack(fill=tk.BOTH, expand=True)
