import tkinter as tk
from tkinter import *
from tkinter import ttk
from tkinter import filedialog
import os
from tkinter import font

from asociety.repository.database import set_currentdb
from studio.single_mahalanobis_panel import SingleMahalanobisPanel
from studio.clustering_panel import ClusteringPanel
from studio.tsne_panel import TSNEPanel
from studio.comparison_panel import ComparisonPanel # Import the new comparison panel
from studio.internal_consistency_panel import InternalConsistencyPanel # Import the new panel
from studio.factor_analysis_panel import FactorAnalysisPanel # Import the factor analysis panel
from studio.identifiability_panel import IdentifiabilityPanel # Import the new identifiability panel
from studio.curve_comparison_panel import CurveComparisonPanel # Import the new curve comparison panel
from studio.raw_comparison_panel import RawComparisonPanel # Import the new raw comparison panel
from studio.antialign_comparison_panel import AntialignComparisonPanel # Import the new antialign comparison panel
from studio.narrative_comparison_panel import NarrativeComparisonPanel # Import the new narrative comparison panel
from studio.stability_analysis_panel import StabilityAnalysisPanel # Import the new stability panel
from studio.cfa_panel import CFAPanel # Import the new CFA panel
from studio.multi_mahalanobis_panel import MultiMahalanobisPanel # Import the new multi Mahalanobis panel
from studio.personality_browse import PersonalityBrowser
from studio.personality_analysis import PersonalityAnalysis
from studio.personality_stats import PersonalityStats
from studio.config_panel import ConfigPanel

LANGUAGES = {
    'zh': {
        'file': '文件',
        'sampling': '抽样',
        'close': '关闭',
        'exit': '退出',
        'analysis': '分析',
        'analysis_exp': '实验分析',
        'personality': '性格',
        'personality_analysis': '性格分析',
        'personality_stats': '性格统计',
        'evaluation': '评估',
        'base': '基础',
        'persona': '角色',
        'question': '问题',
        'question_group': '问题组',
        'persona_group': '角色组',
        'experimentlist': '实验列表',
        'experiment': '实验',
        'tree_root': 'Agentic Society',
        'language': '语言',
        'menu_language': '语言/Language',
        'working_db': '工作数据库',
        'data_analysis': '数据分析',
        'mahalanobis_distance': '马氏距离分析 (单文件)',
        'multi_mahalanobis_distance': '马氏距离对比 (多数据源)',
        'clustering_analysis': '聚类分析 (多文件)',
        'tsne_analysis': 't-SNE 可视化 (多文件)',
        'comparison_analysis': '画像对比分析 (多模式)',
        'consistency_analysis': '内部一致性分析',
        'factor_analysis': '因素分析 (EFA)',
        'cfa_analysis': '验证性因素分析 (CFA)',
        'identifiability_analysis': '可识别性分析',
        'stability_analysis': '稳定性分析',
        'special_analysis': '专题分析',
        'select_db': '选择数据库文件...', 
        'run_analysis': '运行分析',
        'run_factor_analysis': '运行因素分析',
        'configuration': '配置',
        'switch_db': '切换数据库'
    },
    'en': {
        'file': 'File',
        'sampling': 'Sampling',
        'close': 'Close',
        'exit': 'Exit',
        'analysis': 'Analysis',
        'analysis_exp': 'Experiment Analysis',
        'personality': 'Personality',
        'personality_analysis': 'Personality Analysis',
        'personality_stats': 'Personality Statistics',
        'evaluation': 'Evaluation',
        'base': 'Base',
        'persona': 'Persona',
        'question': 'Question',
        'question_group': 'Question Group',
        'persona_group': 'Persona Group',
        'experimentlist': 'Experiment List',
        'experiment': 'Experiment',
        'tree_root': 'Agentic Society',
        'language': 'Language',
        'menu_language': '语言/Language',
        'working_db': 'Working Database',
        'data_analysis': 'Data Analysis',
        'mahalanobis_distance': 'Mahalanobis Dist (Single File)',
        'multi_mahalanobis_distance': 'Mahalanobis Compare (Multi-Source)',
        'clustering_analysis': 'Clustering (Multi-File)',
        'tsne_analysis': 't-SNE Visualization (Multi-File)',
        'comparison_analysis': 'Profile Comparison (Multi-Mode)',
        'consistency_analysis': 'Internal Consistency',
        'factor_analysis': 'Factor Analysis (EFA)',
        'cfa_analysis': 'Confirmatory Factor Analysis (CFA)',
        'identifiability_analysis': 'Identifiability Analysis',
        'stability_analysis': 'Stability Analysis',
        'special_analysis': 'Special Analysis',
        'select_db': 'Select Database File...', 
        'run_analysis': 'Run Analysis',
        'run_factor_analysis': 'Run Factor Analysis',
        'configuration': 'Configuration',
        'switch_db': 'Switch Database'
    }
}

class MainWindow:
    def __init__(self, root) -> None:
        self.lang = 'zh'
        self.root = root
        root.title('AgenticSociety')
        # root.iconbitmap()   
        
        lang_frame = ttk.Frame(root)
        lang_frame.pack(anchor=NE, padx=10, pady=2)
        ttk.Label(lang_frame, text="语言/Language:", font=("Helvetica", 11)).pack(side=LEFT)
        self.lang_var = StringVar(value=self.lang)
        lang_combo = ttk.Combobox(lang_frame, textvariable=self.lang_var, values=['zh', 'en'], width=6, state='readonly')
        lang_combo.pack(side=LEFT, padx=5)
        lang_combo.bind('<<ComboboxSelected>>', self.on_lang_change)

        self.menu(root)
        self.main = ttk.Frame(root, style='TFrame')
        self.main.pack(fill=BOTH, expand=True)

        self.PW = PW = ttk.PanedWindow(self.main, orient=HORIZONTAL)
        PW.pack(fill=BOTH, expand=True)

        self.left = ttk.Frame(PW, width=250, height=300, relief=SUNKEN, style='TFrame')
        self.right = ttk.Frame(PW, width=800, height=300, relief=SUNKEN, style='TFrame')

        PW.add(self.left, weight=1)
        PW.add(self.right, weight=4)
        
        self.treeView = self.tree(self.left)
        
        # Initialize all panels
        self.panels = {
            'personality': PersonalityBrowser(self.right),
            'personality-analysis': PersonalityAnalysis(self.right),
            'personality-stats': PersonalityStats(self.right),
            'mahalanobis': SingleMahalanobisPanel(self.right),
            'multi_mahalanobis': MultiMahalanobisPanel(self.right),
            'clustering': ClusteringPanel(self.right),
            'tsne': TSNEPanel(self.right),
            'comparison': ComparisonPanel(self.right),
            'consistency': InternalConsistencyPanel(self.right),
            'factor': FactorAnalysisPanel(self.right),
            'cfa': CFAPanel(self.right),
            'identifiability': IdentifiabilityPanel(self.right),
            'curve_comparison': CurveComparisonPanel(self.right),
            'raw_comparison': RawComparisonPanel(self.right),
            'antialign_comparison': AntialignComparisonPanel(self.right),
            'narrative_comparison': NarrativeComparisonPanel(self.right),
            'stability': StabilityAnalysisPanel(self.right)
        }
        
        self.set_language(self.lang)
        # Hide all panels initially
        for panel in self.panels.values():
            panel.main.pack_forget()

    def donothing(self):
        pass

    def menu(self,root):
        menubar = Menu(root, borderwidth=20)
        root.config(menu=menubar)
        filemenu = Menu(menubar, tearoff=0, border=12)
        
        filemenu.add_command(label=LANGUAGES[self.lang].get('configuration', 'Configuration'), command=self.open_config_panel)
        filemenu.add_command(label=LANGUAGES[self.lang].get('switch_db', 'Switch Database'), command=self.open_db)
        filemenu.add_command(label=LANGUAGES[self.lang].get('close', 'Close'), command=self.donothing)
        filemenu.add_separator()
        filemenu.add_command(label=LANGUAGES[self.lang].get('exit', 'Exit'), command=root.quit)
        menubar.add_cascade(label=LANGUAGES[self.lang].get('file', 'File'), menu=filemenu)

    def open_config_panel(self):
        config_panel = ConfigPanel(self.root)
        config_panel.grab_set() # Make the config panel modal

    def open_db(self):
        file_path = filedialog.askopenfilename(
            title='选择数据库文件',
            filetypes=[('SQLite DB', '*.db'), ('All Files', '*.*')],
            initialdir='data/db/'
        )
        if file_path:
            set_currentdb(file_path)
            from tkinter import messagebox
            messagebox.showinfo('数据库切换', f'已切换到数据库：\n{file_path}')
            # Refresh relevant panels
            for key in ['personality', 'personality-analysis', 'personality-stats']:
                panel = self.panels.get(key)
                if panel:
                    try:
                        if hasattr(panel, 'refresh_data'):
                            panel.refresh_data()
                        elif hasattr(panel, 'setData'):
                            panel.setData(None, self.updateTree)
                    except Exception as e:
                        messagebox.showerror('面板刷新错误', f'切换数据库后刷新面板时出错：\n{e}')

    def tree(self, frame):
        tv = ttk.Treeview(frame, style="Treeview")
        tv.pack(fill=BOTH, expand=True)
        self.recreate(tv)
        tv.config(height=100)
        tv.bind("<<TreeviewSelect>>", self.treeSelect)
        return tv

    def updateTree(self):
        self.recreate(self.treeView)
        self.left.update()

    def recreate(self, tv):
        for i in tv.get_children():
            tv.delete(i)
        
        lang = LANGUAGES[self.lang]
        
        # Main nodes
        tv.insert('', 'end', 'working_db', text=lang['working_db'], image='')
        tv.insert('', 'end', 'data_analysis', text=lang['data_analysis'], image='')
        tv.insert('', 'end', 'special_analysis', text=lang['special_analysis'], image='')

        # Children for "Working Database"
        tv.insert('working_db', 'end', 'personality', text=lang['personality'], image='')
        tv.insert('working_db', 'end', 'personality-stats', text=lang['personality_stats'], image='')

        # Children for "Data Analysis"
        tv.insert('data_analysis', 'end', 'personality-analysis', text=lang['personality_analysis'], image='')
        tv.insert('data_analysis', 'end', 'mahalanobis', text=lang['mahalanobis_distance'], image='')
        tv.insert('data_analysis', 'end', 'clustering', text=lang['clustering_analysis'], image='')
        tv.insert('data_analysis', 'end', 'tsne', text=lang['tsne_analysis'], image='')
        tv.insert('data_analysis', 'end', 'comparison', text=lang['comparison_analysis'], image='')
        tv.insert('data_analysis', 'end', 'consistency', text=lang['consistency_analysis'], image='')
        tv.insert('data_analysis', 'end', 'factor', text=lang['factor_analysis'], image='')
        tv.insert('data_analysis', 'end', 'cfa', text=lang['cfa_analysis'], image='')
        
        # Children for "Special Analysis"
        tv.insert('special_analysis', 'end', 'stability', text=lang['stability_analysis'], image='')
        tv.insert('special_analysis', 'end', 'identifiability', text=lang['identifiability_analysis'], image='')
        tv.insert('special_analysis', 'end', 'multi_mahalanobis', text=lang['multi_mahalanobis_distance'], image='')
        tv.insert('special_analysis', 'end', 'curve_comparison', text='年龄维度曲线对比 (deepseek)', image='')
        tv.insert('special_analysis', 'end', 'raw_comparison', text='正常生成画像曲线分析', image='')
        tv.insert('special_analysis', 'end', 'antialign_comparison', text='抗对齐vs正常生成对比', image='')
        tv.insert('special_analysis', 'end', 'narrative_comparison', text='叙事vs抗对齐vs正常生成对比', image='')
        
        tv.item('working_db', open=True)
        tv.item('data_analysis', open=True)
        tv.item('special_analysis', open=True)

    def treeSelect(self, event):
        if not self.treeView.selection():
            return
            
        selected_item = self.treeView.selection()[0]
        
        # Map treeview item ID to panel key
        panel_key_map = {
            'personality': 'personality',
            'personality-analysis': 'personality-analysis',
            'personality-stats': 'personality-stats',
            'mahalanobis': 'mahalanobis',
            'multi_mahalanobis': 'multi_mahalanobis',
            'clustering': 'clustering',
            'tsne': 'tsne',
            'comparison': 'comparison',
            'consistency': 'consistency',
            'factor': 'factor',
            'cfa': 'cfa',
            'identifiability': 'identifiability',
            'curve_comparison': 'curve_comparison',
            'raw_comparison': 'raw_comparison',
            'antialign_comparison': 'antialign_comparison',
            'narrative_comparison': 'narrative_comparison',
            'stability': 'stability'
        }
        
        panel_key = panel_key_map.get(selected_item)

        if not panel_key or panel_key not in self.panels:
            # Hide all panels if a non-leaf node is selected
            for p in self.panels.values():
                p.main.pack_forget()
            return

        # Show the selected panel and hide others
        for key, p in self.panels.items():
            if key == panel_key:
                p.main.pack(fill=BOTH, expand=True)
                # Pass control methods if needed
                if hasattr(p, 'setData'):
                    p.setData(selected_item, self.updateTree)
                if hasattr(p, 'set_language'):
                    import inspect
                    sig = inspect.signature(p.set_language)
                    if len(sig.parameters) == 3: # Expects self, lang, lang_dict
                        p.set_language(self.lang, LANGUAGES[self.lang])
                    else: # Assumes old signature: self, lang
                        p.set_language(self.lang)
            else:
                p.main.pack_forget()
        
    def set_language(self, lang):
        self.lang = lang
        self.lang_var.set(lang)
        self.menu(self.root)
        self.recreate(self.treeView)
        for panel in self.panels.values():
            if hasattr(panel, 'set_language'):
                import inspect
                sig = inspect.signature(panel.set_language)
                if len(sig.parameters) == 3: # Expects self, lang, lang_dict
                    panel.set_language(lang, LANGUAGES[lang])
                else: # Assumes old signature: self, lang
                    panel.set_language(lang)
            if hasattr(panel, 'update_texts'): # For personality_stats
                panel.update_texts(lang)

    def on_lang_change(self, event=None):
        new_lang = self.lang_var.get()
        if new_lang != self.lang:
            self.set_language(new_lang)

if __name__ == "__main__":
    root = Tk()
    style = ttk.Style()

    style.theme_use('clam')
    style.configure('TFrame', background='#f0f0f0')
    style.configure('TButton', font=('Helvetica', 12), background='#e0e0e0', foreground='black')
    style.map('TButton', background=[('active', '#d0d0d0')])
    style.configure('TLabel', background='#f0f0f0', font=('Helvetica', 12), foreground='black')

    app = MainWindow(root)
    root.state('zoomed')
    
    def _quit():
        root.quit()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", _quit)
    root.mainloop()
