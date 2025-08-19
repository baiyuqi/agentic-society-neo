from tkinter import *
from tkinter import ttk, filedialog
import pandas as pd
from tkinter import scrolledtext
from asociety.personality.personality_analysis import calculate_personality_stats,  project_personality_2d, project_personality_1d
import os

LANGUAGES = {
    'zh': {
        'title': '性格维度统计信息',
        'refresh': '刷新统计数据',
        'summary': '统计摘要',
        'trait_names': ['开放性', '尽责性', '外向性', '宜人性', '神经质'],
        'columns': ('性格维度', '均值', '方差', '标准差', '样本数'),
        'summary_head': '性格维度统计摘要：',
        'insight': '统计洞察：',
        'max_mean': '• 平均分最高的维度',
        'min_mean': '• 平均分最低的维度',
        'error': '获取统计数据时出错：',
    },
    'en': {
        'title': 'Personality Dimension Statistics',
        'refresh': 'Refresh',
        'summary': 'Summary',
        'trait_names': ['Openness', 'Conscientiousness', 'Extraversion', 'Agreeableness', 'Neuroticism'],
        'columns': ('Trait', 'Mean', 'Variance', 'Std', 'N'),
        'summary_head': 'Personality Dimension Summary:',
        'insight': 'Insights:',
        'max_mean': '• Highest mean',
        'min_mean': '• Lowest mean',
        'error': 'Error fetching statistics:',
    }
}

class PersonalityStats:
    def __init__(self, parent) -> None:
        self.selected_file = None
        # self.lang = 'zh'  # 由主窗口控制
        self.main = ttk.Frame(parent, style='Main.TFrame')
        self.main.pack(fill=BOTH, expand=True)
        
        # 创建标题
        self.title_label = ttk.Label(self.main, font=("Helvetica", 20, "bold"), anchor=CENTER, background="#e3eefa", foreground="#2a3a4a")
        self.title_label.pack(pady=(20, 10), fill=X)
        
        # 分割线
        sep = ttk.Separator(self.main, orient=HORIZONTAL)
        sep.pack(fill=X, padx=30, pady=(0, 10))
        
        # 创建按钮框架
        button_frame = ttk.Frame(self.main, style='Main.TFrame')
        button_frame.pack(pady=10)
        
        # 创建刷新按钮
        self.refresh_button = ttk.Button(button_frame, text="刷新统计数据", command=self.refresh_stats, style='Accent.TButton')
        self.refresh_button.pack(side=LEFT, padx=10)
        # 一维投影按钮
        self.proj1d_button = ttk.Button(button_frame, text="一维投影", command=self.show_1d_projection, style='Accent.TButton')
        self.proj1d_button.pack(side=LEFT, padx=10)
        
        # --- Database Selection ---
        self.file_label = ttk.Label(button_frame, text="Selected File: None")
        self.file_label.pack(side=LEFT, padx=10)
        browse_button = ttk.Button(button_frame, text="Browse File...", command=self.browse_file)
        browse_button.pack(side=LEFT, padx=10)

        # 创建统计信息显示区域
        self.create_stats_display()
        
        # Initialize empty
        self.set_style()
        self.update_texts('zh') # Initialize texts
        self.clear_stats()      # Clear table and summary
        self.selected_file = None

    def browse_file(self):
        file_path = filedialog.askopenfilename(
            title='Select a persona DB file',
            initialdir='data/db',
            filetypes=[('SQLite DB', '*.db'), ('All Files', '*.*')]
        )
        if file_path:
            self.selected_file = file_path
            self.file_label.config(text=f"Selected File: ...{os.path.basename(file_path)}")
            self.refresh_stats()

    def refresh_data(self):
        """Called by the main window when a new DB is selected."""
        self.refresh_stats()
    
    def clear_stats(self):
        """Clears the table and summary text."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.summary_text.delete(1.0, END)
    
    def set_style(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Main.TFrame', background='#f7fafd')
        style.configure('Accent.TButton', font=('Helvetica', 13, 'bold'), foreground='#fff', background='#4a90e2', borderwidth=0, focusthickness=3, focuscolor='none', padding=8)
        style.map('Accent.TButton', background=[('active', '#357ab8')])
        style.configure('Treeview', font=('Helvetica', 12), rowheight=32, fieldbackground='#f7fafd', background='#f7fafd', borderwidth=1)
        style.configure('Treeview.Heading', font=('Helvetica', 13, 'bold'), background='#e3eefa', foreground='#2a3a4a')
        style.layout('Treeview', [('Treeview.treearea', {'sticky': 'nswe'})])
        style.configure('Summary.TLabelframe', background='#e3eefa', borderwidth=2, relief='solid')
        style.configure('Summary.TLabelframe.Label', font=('Helvetica', 13, 'bold'), background='#e3eefa', foreground='#2a3a4a')
    
    def create_stats_display(self):
        # 创建主显示框架
        display_frame = ttk.Frame(self.main, style='Main.TFrame')
        display_frame.pack(fill=BOTH, expand=True, padx=30, pady=10)
        
        self.tree = ttk.Treeview(display_frame, show='headings', height=8, style='Treeview')
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        self.scrollbar = ttk.Scrollbar(display_frame, orient=VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side=RIGHT, fill=Y)
        
        # 创建摘要信息框架
        self.summary_frame = ttk.LabelFrame(self.main, style='Summary.TLabelframe', padding=10)
        self.summary_frame.pack(fill=X, padx=30, pady=15)
        self.summary_text = scrolledtext.ScrolledText(self.summary_frame, height=7, width=60, font=("Consolas", 12), background="#f7fafd", foreground="#2a3a4a", borderwidth=0, relief=FLAT)
        self.summary_text.pack(fill=BOTH, expand=True)
    
    def set_language(self, lang):
        self.update_texts(lang)

    def update_texts(self, lang):
        # 用主窗口传递的lang刷新界面文本
        lang_dict = LANGUAGES[lang]
        self.title_label.config(text=lang_dict['title'])
        self.refresh_button.config(text=lang_dict['refresh'])
        self.summary_frame.config(text=lang_dict['summary'])
        self.tree.config(columns=lang_dict['columns'])
        for i, col in enumerate(lang_dict['columns']):
            self.tree.heading(f'#{i+1}', text=col)
            self.tree.column(f'#{i+1}', width=120, anchor=CENTER, stretch=True)
        self.refresh_stats(lang)

    def refresh_stats(self, lang=None):
        if not self.selected_file:
            self.clear_stats()
            return
        if lang is None:
            lang = 'zh'
        lang_dict = LANGUAGES[lang]
        try:
            # 获取统计数据
            stats = calculate_personality_stats(db_path=self.selected_file)
            # 清空现有数据
            for item in self.tree.get_children():
                self.tree.delete(item)
            # 获取样本数
            sample_count = len(stats.get('openness', {}).get('data', [])) if 'data' in stats.get('openness', {}) else 0
            # 插入数据到表格（斑马线效果）
            personality_traits = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']
            trait_names = lang_dict['trait_names']
            for idx, (trait, name) in enumerate(zip(personality_traits, trait_names)):
                if trait in stats:
                    values = stats[trait]
                    tag = 'evenrow' if idx % 2 == 0 else 'oddrow'
                    self.tree.insert('', 'end', values=(
                        name,
                        f"{values['mean']:.4f}",
                        f"{values['variance']:.4f}",
                        f"{values['std']:.4f}",
                        sample_count
                    ), tags=(tag,))
            self.tree.tag_configure('evenrow', background='#e3eefa')
            self.tree.tag_configure('oddrow', background='#f7fafd')
            # 更新摘要信息
            self.update_summary(stats, lang)
        except Exception as e:
            self.summary_text.delete(1.0, END)
            self.summary_text.insert(END, f"{lang_dict['error']}\n{str(e)}")

    def update_summary(self, stats, lang):
        lang_dict = LANGUAGES[lang]
        self.summary_text.delete(1.0, END)
        summary = f"{lang_dict['summary_head']}\n\n"
        personality_traits = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']
        trait_names = lang_dict['trait_names']
        for trait, name in zip(personality_traits, trait_names):
            if trait in stats:
                values = stats[trait]
                summary += f"{name}:\n"
                summary += f"  {lang_dict['columns'][1]}: {values['mean']:.4f}\n"
                summary += f"  {lang_dict['columns'][2]}: {values['variance']:.4f}\n"
                summary += f"  {lang_dict['columns'][3]}: {values['std']:.4f}\n\n"
        # 添加一些统计洞察
        summary += f"{lang_dict['insight']}\n"
        means = [stats[trait]['mean'] for trait in personality_traits if trait in stats]
        if means:
            max_mean = max(means)
            min_mean = min(means)
            max_trait = trait_names[means.index(max_mean)]
            min_trait = trait_names[means.index(min_mean)]
            summary += f"{lang_dict['max_mean']}: {max_trait} ({max_mean:.4f})\n"
            summary += f"{lang_dict['min_mean']}: {min_trait} ({min_mean:.4f})\n"
        self.summary_text.insert(END, summary)
    
    def show_1d_projection(self):
        import matplotlib
        matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'STHeiti', 'Arial Unicode MS']
        matplotlib.rcParams['axes.unicode_minus'] = False
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        import numpy as np
        from tkinter import Toplevel, BOTH
        coords_1d, sex, df = project_personality_1d()
        win = Toplevel(self.main)
        win.title("性格一维投影 (PCA)")
        win.geometry("700x400")
        fig, ax = plt.subplots(figsize=(7, 3))
        # 不同性别不同颜色
        colors = {'Male': 'blue', 'Female': 'red'}
        scatter_objs = []
        for s in np.unique(sex):
            idx = (sex == s)
            sc = ax.scatter(coords_1d[idx], np.zeros_like(coords_1d[idx]), label=s, alpha=0.7, s=40, c=colors.get(s, None))
            scatter_objs.append((sc, np.where(idx)[0]))
        ax.set_title('Personality PCA 1D Projection')
        ax.set_xlabel('PC1')
        ax.get_yaxis().set_visible(False)
        ax.legend()
        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=BOTH, expand=True)

        # 悬停浮窗
        annot = ax.annotate("", xy=(0,0), xytext=(20,20), textcoords="offset points",
                            bbox=dict(boxstyle="round", fc="w"), arrowprops=dict(arrowstyle="->"))
        annot.set_visible(False)
        summary_cols = ['id', 'age', 'sex', 'openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']
        points = np.column_stack([coords_1d, np.zeros_like(coords_1d)])

        def update_annot(ind):
            i = ind[0]
            persona_info = df.iloc[i]
            summary = '\n'.join([f"{col}: {persona_info[col]}" for col in summary_cols if col in df.columns])
            annot.xy = (coords_1d[i], 0)
            annot.set_text(summary)
            annot.get_bbox_patch().set_alpha(0.95)

        def hover(event):
            vis = annot.get_visible()
            if event.inaxes == ax:
                cont, ind = False, None
                # 计算最近点
                dists = np.abs(coords_1d - event.xdata)
                i = np.argmin(dists)
                if dists[i] < 0.05 * (coords_1d.max() - coords_1d.min()):  # 距离阈值
                    cont = True
                    ind = [i]
                if cont:
                    update_annot(ind)
                    annot.set_visible(True)
                    fig.canvas.draw_idle()
                else:
                    if vis:
                        annot.set_visible(False)
                        fig.canvas.draw_idle()
            else:
                if vis:
                    annot.set_visible(False)
                    fig.canvas.draw_idle()
        fig.canvas.mpl_connect("motion_notify_event", hover)
    
    def setData(self, item, updateTree):
        pass 