# studio/collapsible_help_panel.py

import tkinter as tk
from tkinter import ttk
from studio.help_panel import HelpPanel


class CollapsibleHelpPanel:
    """
    通用的可折叠帮助面板组件
    支持单个帮助内容或多个帮助标签页
    """
    
    def __init__(self, parent_paned_window, help_configs, weight=1):
        """
        初始化可折叠帮助面板
        
        Args:
            parent_paned_window: 父级PanedWindow组件
            help_configs: 帮助配置，可以是：
                - 单个配置: {"title": "标题", "content": "内容"}
                - 多个配置: [{"title": "标题1", "content": "内容1", "tab_text": "标签1"}, ...]
            weight: 帮助面板在PanedWindow中的权重
        """
        self.parent_paned_window = parent_paned_window
        self.weight = weight
        self.help_visible = True
        
        # 创建帮助面板容器
        self.help_container = ttk.Frame(parent_paned_window)
        
        # 创建推拉控制条
        self.sash_frame = ttk.Frame(self.help_container, width=20)
        self.sash_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.sash_frame.pack_propagate(False)

        # 推拉按钮
        self.toggle_button = ttk.Button(
            self.sash_frame,
            text="<",
            width=2,
            command=self.toggle_help_panel
        )
        self.toggle_button.pack(expand=True)
        
        # 根据配置创建帮助内容
        self._create_help_content(help_configs)
        
        # 添加到父级PanedWindow
        self.parent_paned_window.add(self.help_container, weight=self.weight)
    
    def _create_help_content(self, help_configs):
        """根据配置创建帮助内容"""
        if isinstance(help_configs, dict):
            # 单个帮助面板
            self.help_panel = HelpPanel(
                self.help_container, 
                title=help_configs["title"], 
                content=help_configs["content"]
            )
            self.help_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
            self.help_content = self.help_panel
            
        elif isinstance(help_configs, list):
            # 多个帮助标签页
            self.help_notebook = ttk.Notebook(self.help_container)
            self.help_notebook.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
            
            self.help_panels = []
            for config in help_configs:
                help_panel = HelpPanel(
                    self.help_notebook, 
                    title=config["title"], 
                    content=config["content"]
                )
                tab_text = config.get("tab_text", config["title"])
                self.help_notebook.add(help_panel, text=tab_text)
                self.help_panels.append(help_panel)
            
            self.help_content = self.help_notebook
        else:
            raise ValueError("help_configs must be a dict or list of dicts")
    
    def toggle_help_panel(self):
        """切换帮助面板的显示/隐藏状态"""
        if self.help_visible:
            self.parent_paned_window.forget(self.help_container)
            self.help_visible = False
            # 创建显示按钮在主面板右边缘
            if not hasattr(self, 'show_button_frame'):
                self.show_button_frame = ttk.Frame(self.parent_paned_window, width=20)
                self.show_button = ttk.Button(
                    self.show_button_frame,
                    text=">",
                    width=2,
                    command=self.toggle_help_panel
                )
                self.show_button.pack(expand=True)
                self.show_button_frame.pack_propagate(False)
            self.parent_paned_window.add(self.show_button_frame, weight=0)
        else:
            if hasattr(self, 'show_button_frame'):
                self.parent_paned_window.forget(self.show_button_frame)
            self.parent_paned_window.add(self.help_container, weight=self.weight)
            self.help_visible = True
            self.toggle_button.config(text="<")
    
    def get_main_container(self):
        """返回帮助容器，用于外部引用"""
        return self.help_container
    
    def is_visible(self):
        """返回帮助面板是否可见"""
        return self.help_visible
    
    def show(self):
        """显示帮助面板"""
        if not self.help_visible:
            self.toggle_help_panel()
    
    def hide(self):
        """隐藏帮助面板"""
        if self.help_visible:
            self.toggle_help_panel()
    def update_content(self, title, content):
        """更新帮助内容"""
        for child in self.help_panel.winfo_children():
                if isinstance(child, ttk.Label):
                    child.config(text=title)
                    break
            # 更新内容
        import markdown
        if hasattr(self.help_panel, 'html_widget'):
            self.html_content = markdown.markdown(content)
            self.help_panel.html_widget.set_html(self.html_content)