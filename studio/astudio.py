import tkinter as tk
from tkinter import *
from tkinter import ttk
from tkinter import filedialog
import os
from tkinter import font
from ttkthemes import ThemedStyle

from asociety.repository.database import set_currentdb
from studio.working_db.personality_browse import PersonalityBrowser
from studio.working_db.personality_stats import PersonalityStats
from studio.data_analysis.group_level.age_personality_curve import AgePersonalityCurve
from studio.data_analysis.individual_level.single_mahalanobis_panel import SingleMahalanobisPanel
from studio.data_analysis.individual_level.folder_clustering_panel import FolderClusteringPanel
from studio.data_analysis.individual_level.file_clustering_panel import FileClusteringPanel
from studio.data_analysis.individual_level.single_density_panel import SingleDensityPanel
from studio.data_analysis.other.ocean_density_panel import OceanDensityPanel # Import the new OCEAN density panel
from studio.data_analysis.other.tsne_panel import TSNEPanel
from studio.data_analysis.other.comparison_panel import ComparisonPanel # Import the new comparison panel
from studio.data_analysis.other.internal_consistency_panel import InternalConsistencyPanel # Import the new panel
from studio.data_analysis.other.factor_analysis_panel import FactorAnalysisPanel # Import the factor analysis panel
from studio.data_analysis.other.cfa_panel import CFAPanel # Import the new CFA panel
from studio.special_analysis.individual_level.identifiability_panel import IdentifiabilityPanel # Import the new identifiability panel
from studio.special_analysis.individual_level.single_identifiability_panel import SingleIdentifiabilityPanel # Import the single identifiability panel
from studio.special_analysis.individual_level.stability_analysis_panel import StabilityAnalysisPanel # Import the new stability analysis panel
from studio.special_analysis.individual_level.group_identifiability_panel import GroupIdentifiabilityPanel # Import the new group identifiability panel
from studio.special_analysis.group_level.curve_comparison_panel import CurveComparisonPanel # Import the new curve comparison panel
from studio.special_analysis.group_level.raw_comparison_panel import RawComparisonPanel # Import the new raw comparison panel
from studio.special_analysis.group_level.antialign_comparison_panel import AntialignComparisonPanel # Import the new antialign comparison panel
from studio.special_analysis.group_level.narrative_comparison_panel import NarrativeComparisonPanel # Import the new narrative comparison panel
from studio.config_panel import ConfigPanel

LANGUAGES = {
    'zh': {
        'file': '文件',
        'sampling': '抽样',
        'close': '关闭',
        'exit': '退出',
        'analysis': '分析',
        'analysis_exp': '实验分析',
        'personality-browse': '性格浏览',
        'age_personality_curve': '年龄性格曲线',
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
        'individual_level': '个体水平',
        'group_level': '群体水平',
        'other_analysis': '其他',
        'mahalanobis_distance': '马氏距离分析 (单文件)',
        'stability_analysis': '稳定性分析',
        'multi_mahalanobis_analysis': '马氏距离分析 (多文件)',
        'ocean_density_analysis': 'OCEAN维度密度分析',
        'folder_clustering_analysis': '选择文件夹聚类 (多文件)',
        'file_clustering_analysis': '选择文件聚类 (多文件)',
        'tsne_analysis': 't-SNE 可视化 (多文件)',
        'comparison_analysis': '画像对比分析 (多模式)',
        'consistency_analysis': '内部一致性分析',
        'factor_analysis': '因素分析 (EFA)',
        'cfa_analysis': '验证性因素分析 (CFA)',
        'identifiability_analysis': '可识别性分析',
        'group_identifiability_analysis': '群体可识别性分析',
        'single_identifiability_analysis': '单一可辨识性',
        'stability_analysis': '稳定性分析',
        'special_analysis': '专题分析',
        'select_db': '选择数据库文件...',
        'run_analysis': '运行分析',
        'run_factor_analysis': '运行因素分析',
        'configuration': '配置',
        'switch_db': '切换数据库',
        'theme': '主题',
        'menu_theme': '主题/Theme',
        'arc': 'Arc (现代)',
        'adapta': 'Adapta (绿色)',
        'equilux': 'Equilux (深色)',
        'breeze': 'Breeze (清新)',
        'clam': 'Clam (默认)',
        'vista': 'Vista (Windows)'
    },
    'en': {
        'file': 'File',
        'sampling': 'Sampling',
        'close': 'Close',
        'exit': 'Exit',
        'analysis': 'Analysis',
        'analysis_exp': 'Experiment Analysis',
        'personality': 'Personality',
        'age_personality_curve': 'Age Personality Curve',
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
        'individual_level': 'Individual Level',
        'group_level': 'Group Level',
        'other_analysis': 'Other',
        'mahalanobis_distance': 'Mahalanobis Dist (Single File)',
        'stability_analysis': 'Stability Analysis',
        'multi_mahalanobis_analysis': 'Mahalanobis Distance Analysis (Multi-File)',
        'ocean_density_analysis': 'OCEAN Dimension Density Analysis',
        'folder_clustering_analysis': 'Folder Clustering (Multi-File)',
        'file_clustering_analysis': 'File Clustering (Multi-File)',
        'tsne_analysis': 't-SNE Visualization (Multi-File)',
        'comparison_analysis': 'Profile Comparison (Multi-Mode)',
        'consistency_analysis': 'Internal Consistency',
        'factor_analysis': 'Factor Analysis (EFA)',
        'cfa_analysis': 'Confirmatory Factor Analysis (CFA)',
        'identifiability_analysis': 'Identifiability Analysis',
        'group_identifiability_analysis': 'Group Identifiability Analysis',
        'single_identifiability_analysis': 'Single Identifiability',
        'stability_analysis': 'Stability Analysis',
        'special_analysis': 'Special Analysis',
        'select_db': 'Select Database File...',
        'run_analysis': 'Run Analysis',
        'run_factor_analysis': 'Run Factor Analysis',
        'configuration': 'Configuration',
        'switch_db': 'Switch Database',
        'theme': 'Theme',
        'menu_theme': '主题/Theme',
        'arc': 'Arc (Modern)',
        'adapta': 'Adapta (Green)',
        'equilux': 'Equilux (Dark)',
        'breeze': 'Breeze (Fresh)',
        'clam': 'Clam (Default)',
        'vista': 'Vista (Windows)'
    }
}

class MainWindow:
    def __init__(self, root) -> None:
        self.lang = 'zh'
        self.current_theme = 'arc'
        self.root = root
        root.title('AgenticSociety')
        # root.iconbitmap()

        # Create themed style
        self.style = ThemedStyle(root)
        self.style.set_theme(self.current_theme)

        control_frame = ttk.Frame(root)
        control_frame.pack(anchor=NE, padx=10, pady=2)

        # Language control
        lang_frame = ttk.Frame(control_frame)
        lang_frame.pack(side=LEFT, padx=(0, 10))
        ttk.Label(lang_frame, text="语言/Language:", font=("Helvetica", 11)).pack(side=LEFT)
        self.lang_var = StringVar(value=self.lang)
        lang_combo = ttk.Combobox(lang_frame, textvariable=self.lang_var, values=['zh', 'en'], width=6, state='readonly')
        lang_combo.pack(side=LEFT, padx=5)
        lang_combo.bind('<<ComboboxSelected>>', self.on_lang_change)

        # Theme control
        theme_frame = ttk.Frame(control_frame)
        theme_frame.pack(side=LEFT)
        ttk.Label(theme_frame, text="主题/Theme:", font=("Helvetica", 11)).pack(side=LEFT)
        self.theme_var = StringVar(value=self.current_theme)
        theme_combo = ttk.Combobox(theme_frame, textvariable=self.theme_var,
                                  values=['arc', 'adapta', 'equilux', 'breeze', 'clam', 'vista'],
                                  width=12, state='readonly')
        theme_combo.pack(side=LEFT, padx=5)
        theme_combo.bind('<<ComboboxSelected>>', self.on_theme_change)

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
            'personality-browse': PersonalityBrowser(self.right),
            'age-personality-curve': AgePersonalityCurve(self.right),
            'personality-stats': PersonalityStats(self.right),
            'mahalanobis': SingleMahalanobisPanel(self.right),
            'stability_analysis': StabilityAnalysisPanel(self.right),
            'multi_mahalanobis': SingleDensityPanel(self.right),
            'ocean_density': OceanDensityPanel(self.right),  # Add the new OCEAN density panel
            'folder_clustering': FolderClusteringPanel(self.right),
            'file_clustering': FileClusteringPanel(self.right),
            'tsne': TSNEPanel(self.right),
            'comparison': ComparisonPanel(self.right),
            'consistency': InternalConsistencyPanel(self.right),
            'factor': FactorAnalysisPanel(self.right),
            'cfa': CFAPanel(self.right),
            'identifiability': IdentifiabilityPanel(self.right),
            'group_identifiability': GroupIdentifiabilityPanel(self.right),
            'single_identifiability': SingleIdentifiabilityPanel(self.right),
            'curve_comparison': CurveComparisonPanel(self.right),
            'raw_comparison': RawComparisonPanel(self.right),
            'antialign_comparison': AntialignComparisonPanel(self.right),
            'narrative_comparison': NarrativeComparisonPanel(self.right)
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

        filemenu.add_command(label=LANGUAGES[self.lang].get('close', 'Close'), command=self.donothing)
        filemenu.add_separator()

        # Theme submenu
        thememenu = Menu(filemenu, tearoff=0)
        for theme in ['arc', 'adapta', 'equilux', 'breeze', 'clam', 'vista']:
            thememenu.add_command(label=LANGUAGES[self.lang].get(theme, theme),
                                 command=lambda t=theme: self.change_theme(t))
        filemenu.add_cascade(label=LANGUAGES[self.lang].get('menu_theme', 'Theme'), menu=thememenu)

        filemenu.add_separator()
        filemenu.add_command(label=LANGUAGES[self.lang].get('exit', 'Exit'), command=root.quit)
        menubar.add_cascade(label=LANGUAGES[self.lang].get('file', 'File'), menu=filemenu)

    def open_config_panel(self):
        config_panel = ConfigPanel(self.root)
        config_panel.grab_set() # Make the config panel modal


    def tree(self, frame):
        tv = ttk.Treeview(frame, style="Treeview")
        tv.pack(fill=BOTH, expand=True)
        self.recreate(tv)
        tv.config(height=100)
        tv.bind("<<TreeviewSelect>>", self.treeSelect)

        # Configure treeview font size and row height for better readability
        style = ttk.Style()
        style.configure("Treeview", font=('Helvetica', 11), rowheight=30)
        style.configure("Treeview.Heading", font=('Helvetica', 12, 'bold'))

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
        tv.insert('working_db', 'end', 'personality-browse', text=lang['personality-browse'], image='')
        tv.insert('working_db', 'end', 'personality-stats', text=lang['personality_stats'], image='')

        # Children for "Data Analysis"
        tv.insert('data_analysis', 'end', 'individual_level', text=lang['individual_level'], image='')
        tv.insert('data_analysis', 'end', 'group_level', text=lang['group_level'], image='')
        tv.insert('data_analysis', 'end', 'ocean_density', text=lang.get('ocean_density_analysis', 'OCEAN Dimension Density Analysis'), image='')
        tv.insert('data_analysis', 'end', 'other_analysis', text=lang['other_analysis'], image='')

        # Children for "Group Level"
        tv.insert('group_level', 'end', 'age-personality-curve', text=lang['age_personality_curve'], image='')

        # Children for "Other Analysis"
        tv.insert('other_analysis', 'end', 'tsne', text=lang['tsne_analysis'], image='')
        tv.insert('other_analysis', 'end', 'comparison', text=lang['comparison_analysis'], image='')
        tv.insert('other_analysis', 'end', 'consistency', text=lang['consistency_analysis'], image='')
        tv.insert('other_analysis', 'end', 'factor', text=lang['factor_analysis'], image='')
        tv.insert('other_analysis', 'end', 'cfa', text=lang['cfa_analysis'], image='')

        # Children for "Individual Level"
        tv.insert('individual_level', 'end', 'mahalanobis', text=lang['mahalanobis_distance'], image='')
        tv.insert('individual_level', 'end', 'multi_mahalanobis', text=lang['multi_mahalanobis_analysis'], image='')
        tv.insert('individual_level', 'end', 'folder_clustering', text=lang['folder_clustering_analysis'], image='')
        tv.insert('individual_level', 'end', 'file_clustering', text=lang['file_clustering_analysis'], image='')

        # Children for "Special Analysis"
        tv.insert('special_analysis', 'end', 'special_individual_level', text='个体水平', image='')
        tv.insert('special_analysis', 'end', 'special_group_level', text='群体水平', image='')

        # Children for "Special Analysis - Individual Level"
        tv.insert('special_individual_level', 'end', 'stability_analysis', text=lang['stability_analysis'], image='')
        tv.insert('special_individual_level', 'end', 'identifiability', text=lang['identifiability_analysis'], image='')
        tv.insert('special_individual_level', 'end', 'group_identifiability', text=lang['group_identifiability_analysis'], image='')
        tv.insert('special_individual_level', 'end', 'single_identifiability', text=lang['single_identifiability_analysis'], image='')

        # Children for "Special Analysis - Group Level"
        tv.insert('special_group_level', 'end', 'curve_comparison', text='年龄维度曲线对比 (deepseek)', image='')
        tv.insert('special_group_level', 'end', 'raw_comparison', text='正常生成画像曲线分析', image='')
        tv.insert('special_group_level', 'end', 'antialign_comparison', text='抗对齐vs正常生成对比', image='')
        tv.insert('special_group_level', 'end', 'narrative_comparison', text='叙事vs抗对齐vs正常生成对比', image='')
        
        tv.item('working_db', open=True)
        tv.item('data_analysis', open=True)
        tv.item('special_analysis', open=True)

    def treeSelect(self, event):
        if not self.treeView.selection():
            return
            
        selected_item = self.treeView.selection()[0]
        
        # Map treeview item ID to panel key
        panel_key_map = {
            'personality-browse': 'personality-browse',
            'age-personality-curve': 'age-personality-curve',
            'personality-stats': 'personality-stats',
            'mahalanobis': 'mahalanobis',
            'stability_analysis': 'stability_analysis',
            'multi_mahalanobis': 'multi_mahalanobis',
            'ocean_density': 'ocean_density',
            'folder_clustering': 'folder_clustering',
            'file_clustering': 'file_clustering',
            'tsne': 'tsne',
            'comparison': 'comparison',
            'consistency': 'consistency',
            'factor': 'factor',
            'cfa': 'cfa',
            'identifiability': 'identifiability',
            'group_identifiability': 'group_identifiability',
            'single_identifiability': 'single_identifiability',
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

    def on_theme_change(self, event=None):
        new_theme = self.theme_var.get()
        if new_theme != self.current_theme:
            self.change_theme(new_theme)

    def change_theme(self, theme_name):
        self.current_theme = theme_name
        self.theme_var.set(theme_name)
        self.style.set_theme(theme_name)

if __name__ == "__main__":
    root = Tk()

    app = MainWindow(root)
    root.state('zoomed')
    
    def _quit():
        root.quit()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", _quit)
    root.mainloop()
