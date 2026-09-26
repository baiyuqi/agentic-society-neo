import matplotlib
matplotlib.use('TkAgg')

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
from studio.multi_mahalanobis_panel import MultiMahalanobisPanel # Import the new multi Mahalanobis panel
from studio.personality_browse import PersonalityBrowser
from studio.personality_analysis import PersonalityAnalysis
from studio.personality_stats import PersonalityStats
from studio.value_browse import ValueBrowser
from studio.value_stats import ValueStats
from studio.value_analysis import ValueAnalysisPanel
from studio.value_curve_comparison_panel import ValueCurveComparisonPanel
from studio.value_raw_comparison_panel import ValueRawComparisonPanel
from studio.value_antialign_comparison_panel import ValueAntialignComparisonPanel
from studio.value_narrative_comparison_panel import ValueNarrativeComparisonPanel
from studio.value_stability_panel import ValueStabilityPanel
from studio.value_identifiability_panel import ValueIdentifiabilityPanel
from studio.value_single_mahalanobis_panel import ValueSingleMahalanobisPanel
from studio.value_multi_mahalanobis_panel import ValueMultiMahalanobisPanel
from studio.value_comparison_panel import ValueComparisonPanel
from studio.value_clustering_panel import ValueClusteringPanel
from studio.value_tsne_panel import ValueTSNEPanel
from studio.morality_browse import MoralityBrowser
from studio.morality_stats import MoralityStats
from studio.morality_analysis import MoralityAnalysisPanel
from studio.morality_curve_comparison_panel import MoralityCurveComparisonPanel
from studio.morality_raw_comparison_panel import MoralityRawComparisonPanel
from studio.morality_antialign_comparison_panel import MoralityAntialignComparisonPanel
from studio.morality_narrative_comparison_panel import MoralityNarrativeComparisonPanel
from studio.morality_stability_panel import MoralityStabilityPanel
from studio.morality_identifiability_panel import MoralityIdentifiabilityPanel
from studio.morality_single_mahalanobis_panel import MoralitySingleMahalanobisPanel
from studio.morality_multi_mahalanobis_panel import MoralityMultiMahalanobisPanel
from studio.morality_comparison_panel import MoralityComparisonPanel
from studio.morality_clustering_panel import MoralityClusteringPanel
from studio.morality_tsne_panel import MoralityTSNEPanel
from studio.single_identifiability_panel import SingleIdentifiabilityPanel
from studio.value_single_identifiability_panel import ValueSingleIdentifiabilityPanel
from studio.morality_single_identifiability_panel import MoralitySingleIdentifiabilityPanel
from studio.file_clustering_panel import FileClusteringPanel
from studio.value_file_clustering_panel import ValueFileClusteringPanel
from studio.morality_file_clustering_panel import MoralityFileClusteringPanel
from studio.single_density_panel import SingleDensityPanel
from studio.value_single_density_panel import ValueSingleDensityPanel
from studio.morality_single_density_panel import MoralitySingleDensityPanel
from studio.ocean_density_panel import OceanDensityPanel
from studio.group_identifiability_panel import GroupIdentifiabilityPanel
from studio.value_group_identifiability_panel import ValueGroupIdentifiabilityPanel
from studio.morality_group_identifiability_panel import MoralityGroupIdentifiabilityPanel
from studio.age_personality_curve import AgePersonalityCurve
from studio.value_age_curve import ValueAgeCurve
from studio.morality_age_curve import MoralityAgeCurve
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
        'value_section': '价值观实验',
        'value': '价值观结果浏览',
        'value_stats': '价值观统计',
        'value_analysis': '价值观分析',
        'value_curve_comparison': '年龄维度价值观曲线对比',
        'value_raw_comparison': '正常生成价值观曲线分析',
        'value_antialign_comparison': '抗对齐vs正常生成价值观对比',
        'value_narrative_comparison': '叙事vs抗对齐vs正常生成价值观对比',
        'value_mahalanobis_distance': '价值观马氏距离分析 (单文件)',
        'value_multi_mahalanobis_distance': '价值观马氏距离对比 (多数据源)',
        'value_clustering_analysis': '价值观聚类分析 (多文件)',
        'value_tsne_analysis': '价值观 t-SNE 可视化 (多文件)',
        'value_comparison_analysis': '价值观画像对比分析 (多模式)',
        'value_identifiability_analysis': '价值观可识别性分析',
        'value_stability_analysis': '价值观稳定性分析',
        'morality_section': '道德基础实验',
        'morality': '道德基础结果浏览',
        'morality_stats': '道德基础统计',
        'morality_analysis': '道德基础分析',
        'morality_curve_comparison': '年龄维度道德基础曲线对比',
        'morality_raw_comparison': '正常生成道德基础曲线分析',
        'morality_antialign_comparison': '抗对齐vs正常生成道德基础对比',
        'morality_narrative_comparison': '叙事vs抗对齐vs正常生成道德基础对比',
        'morality_mahalanobis_distance': '道德基础马氏距离分析 (单文件)',
        'morality_multi_mahalanobis_distance': '道德基础马氏距离对比 (多数据源)',
        'morality_clustering_analysis': '道德基础聚类分析 (多文件)',
        'morality_tsne_analysis': '道德基础 t-SNE 可视化 (多文件)',
        'morality_comparison_analysis': '道德基础画像对比分析 (多模式)',
        'morality_identifiability_analysis': '道德基础可识别性分析',
        'morality_stability_analysis': '道德基础稳定性分析',
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
        'identifiability_analysis': '可识别性分析',
        'group_identifiability_analysis': '群体可识别性分析',
        'stability_analysis': '稳定性分析',
        'single_identifiability_analysis': '单一可辨识性',
        'single_density_analysis': '马氏距离分析 (多文件)',
        'file_clustering_analysis': '选择文件聚类 (多文件)',
        'ocean_density_analysis': 'OCEAN维度密度分析',
        'age_personality_curve': '年龄性格曲线',
        'special_analysis': '专题分析',
        'instrument': '量表',
        'browse': '结果浏览',
        'stats': '统计',
        'curve_comparison_section': '曲线对比',
        'curve_comparison': '年龄维度曲线对比',
        'raw_comparison': '正常生成画像曲线分析',
        'antialign_comparison': '抗对齐vs正常生成对比',
        'narrative_comparison': '叙事vs抗对齐vs正常生成对比',
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
        'value_section': 'Values Experiment',
        'value': 'Value Result Browser',
        'value_stats': 'Value Statistics',
        'value_analysis': 'Values Analysis',
        'value_curve_comparison': 'Age-Values Curve Comparison (deepseek)',
        'value_raw_comparison': 'Normal Generation Values Curve Analysis',
        'value_antialign_comparison': 'Antialign vs Normal Values Comparison',
        'value_narrative_comparison': 'Narrative vs Antialign vs Normal Values Comparison',
        'value_mahalanobis_distance': 'Value Mahalanobis Dist (Single File)',
        'value_multi_mahalanobis_distance': 'Value Mahalanobis Compare (Multi-Source)',
        'value_clustering_analysis': 'Value Clustering (Multi-File)',
        'value_tsne_analysis': 'Value t-SNE Visualization (Multi-File)',
        'value_comparison_analysis': 'Value Profile Comparison (Multi-Mode)',
        'value_identifiability_analysis': 'Value Identifiability Analysis',
        'value_stability_analysis': 'Value Stability Analysis',
        'morality_section': 'Morality Experiment',
        'morality': 'Moral Foundation Result Browser',
        'morality_stats': 'Moral Foundation Statistics',
        'morality_analysis': 'Moral Foundations Analysis',
        'morality_curve_comparison': 'Age-Morality Curve Comparison (deepseek)',
        'morality_raw_comparison': 'Normal Generation Morality Curve Analysis',
        'morality_antialign_comparison': 'Antialign vs Normal Morality Comparison',
        'morality_narrative_comparison': 'Narrative vs Antialign vs Normal Morality Comparison',
        'morality_mahalanobis_distance': 'Morality Mahalanobis Dist (Single File)',
        'morality_multi_mahalanobis_distance': 'Morality Mahalanobis Compare (Multi-Source)',
        'morality_clustering_analysis': 'Morality Clustering (Multi-File)',
        'morality_tsne_analysis': 'Morality t-SNE Visualization (Multi-File)',
        'morality_comparison_analysis': 'Morality Profile Comparison (Multi-Mode)',
        'morality_identifiability_analysis': 'Morality Identifiability Analysis',
        'morality_stability_analysis': 'Morality Stability Analysis',
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
        'identifiability_analysis': 'Identifiability Analysis',
        'group_identifiability_analysis': 'Group Identifiability Analysis',
        'stability_analysis': 'Stability Analysis',
        'single_identifiability_analysis': 'Single Identifiability',
        'single_density_analysis': 'Mahalanobis Distance Analysis (Multi-File)',
        'file_clustering_analysis': 'File Clustering (Multi-File)',
        'ocean_density_analysis': 'OCEAN Dimension Density Analysis',
        'age_personality_curve': 'Age Personality Curve',
        'special_analysis': 'Special Analysis',
        'instrument': 'Instrument',
        'browse': 'Result Browser',
        'stats': 'Statistics',
        'curve_comparison_section': 'Curve Comparison',
        'curve_comparison': 'Age Curve Comparison',
        'raw_comparison': 'Normal Generation Curve Analysis',
        'antialign_comparison': 'Antialign vs Normal Comparison',
        'narrative_comparison': 'Narrative vs Antialign vs Normal Comparison',
        'select_db': 'Select Database File...',
        'run_analysis': 'Run Analysis',
        'run_factor_analysis': 'Run Factor Analysis',
        'configuration': 'Configuration',
        'switch_db': 'Switch Database'
    }
}

# One function set shared by all three instruments. `FUNCTIONS` maps a stable function id to the
# per-instrument panel key; `SECTIONS` groups those ids into the tree's four top-level sections.
# A value of None marks a personality-only function (consistency / factor) with no value/morality twin.
FUNCTIONS = {
    'browse':        {'personality': 'personality', 'value': 'value', 'morality': 'morality'},
    'stats':         {'personality': 'personality-stats', 'value': 'value-stats', 'morality': 'morality-stats'},
    'analysis':      {'personality': 'personality-analysis', 'value': 'value-analysis', 'morality': 'morality-analysis'},
    'mahalanobis':   {'personality': 'mahalanobis', 'value': 'value-mahalanobis', 'morality': 'morality-mahalanobis'},
    'multi_mahalanobis': {'personality': 'multi_mahalanobis', 'value': 'value-multi-mahalanobis', 'morality': 'morality-multi-mahalanobis'},
    'clustering':    {'personality': 'clustering', 'value': 'value-clustering', 'morality': 'morality-clustering'},
    'file_clustering': {'personality': 'file-clustering', 'value': 'value-file-clustering', 'morality': 'morality-file-clustering'},
    'tsne':          {'personality': 'tsne', 'value': 'value-tsne', 'morality': 'morality-tsne'},
    'comparison':    {'personality': 'comparison', 'value': 'value-comparison', 'morality': 'morality-comparison'},
    'curve':         {'personality': 'curve_comparison', 'value': 'value-curve-comparison', 'morality': 'morality-curve-comparison'},
    'raw':           {'personality': 'raw_comparison', 'value': 'value-raw-comparison', 'morality': 'morality-raw-comparison'},
    'antialign':     {'personality': 'antialign_comparison', 'value': 'value-antialign-comparison', 'morality': 'morality-antialign-comparison'},
    'narrative':     {'personality': 'narrative_comparison', 'value': 'value-narrative-comparison', 'morality': 'morality-narrative-comparison'},
    'identifiability': {'personality': 'identifiability', 'value': 'value-identifiability', 'morality': 'morality-identifiability'},
    'group_identifiability': {'personality': 'group-identifiability', 'value': 'value-group-identifiability', 'morality': 'morality-group-identifiability'},
    'single_identifiability': {'personality': 'single-identifiability', 'value': 'value-single-identifiability', 'morality': 'morality-single-identifiability'},
    'stability':     {'personality': 'stability', 'value': 'value-stability', 'morality': 'morality-stability'},
    'single_density': {'personality': 'single-density', 'value': 'value-single-density', 'morality': 'morality-single-density'},
    'age_personality_curve': {'personality': 'age-personality-curve', 'value': 'value-age-curve', 'morality': 'morality-age-curve'},
    'ocean_density': {'personality': 'ocean-density', 'value': None, 'morality': None},
    'consistency':   {'personality': 'consistency', 'value': None, 'morality': None},
    'factor':        {'personality': 'factor', 'value': None, 'morality': None},
}

SECTIONS = [
    ('working_db', ['browse', 'stats']),
    ('data_analysis', ['analysis', 'age_personality_curve', 'mahalanobis', 'clustering', 'file_clustering', 'tsne', 'comparison', 'ocean_density', 'consistency', 'factor']),
    ('curve_comparison_section', ['curve', 'raw', 'antialign', 'narrative']),
    ('special_analysis', ['stability', 'single_density', 'identifiability', 'group_identifiability', 'single_identifiability', 'multi_mahalanobis']),
]

FUNCTION_LABEL_KEYS = {
    'browse': 'browse', 'stats': 'stats', 'analysis': 'analysis',
    'mahalanobis': 'mahalanobis_distance', 'multi_mahalanobis': 'multi_mahalanobis_distance',
    'clustering': 'clustering_analysis', 'file_clustering': 'file_clustering_analysis',
    'tsne': 'tsne_analysis',
    'comparison': 'comparison_analysis', 'curve': 'curve_comparison',
    'raw': 'raw_comparison', 'antialign': 'antialign_comparison',
    'narrative': 'narrative_comparison', 'identifiability': 'identifiability_analysis',
    'group_identifiability': 'group_identifiability_analysis',
    'single_identifiability': 'single_identifiability_analysis',
    'stability': 'stability_analysis', 'single_density': 'single_density_analysis',
    'age_personality_curve': 'age_personality_curve',
    'ocean_density': 'ocean_density_analysis',
    'consistency': 'consistency_analysis', 'factor': 'factor_analysis',
}

SECTION_LABEL_KEYS = {
    'working_db': 'working_db', 'data_analysis': 'data_analysis',
    'curve_comparison_section': 'curve_comparison_section', 'special_analysis': 'special_analysis',
}

class MainWindow:
    def __init__(self, root) -> None:
        self.lang = 'zh'
        self.instrument = 'personality'
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

        # Instrument selector: switching this swaps the whole function tree to the selected instrument.
        selector_frame = ttk.Frame(self.left)
        selector_frame.pack(fill=X, padx=6, pady=(6, 2))
        self.instrument_label = ttk.Label(selector_frame, text=LANGUAGES[self.lang].get('instrument', 'Instrument'), font=("Helvetica", 11))
        self.instrument_label.pack(anchor=W)
        self.instrument_var = StringVar(value=self.instrument)
        instrument_combo = ttk.Combobox(selector_frame, textvariable=self.instrument_var,
                                        values=['personality', 'value', 'morality'], state='readonly')
        instrument_combo.pack(fill=X, pady=(2, 0))
        instrument_combo.bind('<<ComboboxSelected>>', self.on_instrument_change)

        self.treeView = self.tree(self.left)
        
        # Initialize all panels
        self.panels = {
            'personality': PersonalityBrowser(self.right),
            'personality-analysis': PersonalityAnalysis(self.right),
            'personality-stats': PersonalityStats(self.right),
            'mahalanobis': SingleMahalanobisPanel(self.right),
            'multi_mahalanobis': MultiMahalanobisPanel(self.right),
            'clustering': ClusteringPanel(self.right),
            'file-clustering': FileClusteringPanel(self.right),
            'tsne': TSNEPanel(self.right),
            'comparison': ComparisonPanel(self.right),
            'ocean-density': OceanDensityPanel(self.right),
            'consistency': InternalConsistencyPanel(self.right),
            'factor': FactorAnalysisPanel(self.right),
            'identifiability': IdentifiabilityPanel(self.right),
            'group-identifiability': GroupIdentifiabilityPanel(self.right),
            'single-identifiability': SingleIdentifiabilityPanel(self.right),
            'age-personality-curve': AgePersonalityCurve(self.right),
            'curve_comparison': CurveComparisonPanel(self.right),
            'raw_comparison': RawComparisonPanel(self.right),
            'antialign_comparison': AntialignComparisonPanel(self.right),
            'narrative_comparison': NarrativeComparisonPanel(self.right),
            'stability': StabilityAnalysisPanel(self.right),
            'single-density': SingleDensityPanel(self.right),
            'value': ValueBrowser(self.right),
            'value-stats': ValueStats(self.right),
            'value-analysis': ValueAnalysisPanel(self.right),
            'value-curve-comparison': ValueCurveComparisonPanel(self.right),
            'value-raw-comparison': ValueRawComparisonPanel(self.right),
            'value-antialign-comparison': ValueAntialignComparisonPanel(self.right),
            'value-narrative-comparison': ValueNarrativeComparisonPanel(self.right),
            'value-stability': ValueStabilityPanel(self.right),
            'value-identifiability': ValueIdentifiabilityPanel(self.right),
            'value-group-identifiability': ValueGroupIdentifiabilityPanel(self.right),
            'value-single-identifiability': ValueSingleIdentifiabilityPanel(self.right),
            'value-single-density': ValueSingleDensityPanel(self.right),
            'value-age-curve': ValueAgeCurve(self.right),
            'value-mahalanobis': ValueSingleMahalanobisPanel(self.right),
            'value-multi-mahalanobis': ValueMultiMahalanobisPanel(self.right),
            'value-comparison': ValueComparisonPanel(self.right),
            'value-clustering': ValueClusteringPanel(self.right),
            'value-file-clustering': ValueFileClusteringPanel(self.right),
            'value-tsne': ValueTSNEPanel(self.right),
            'morality': MoralityBrowser(self.right),
            'morality-stats': MoralityStats(self.right),
            'morality-analysis': MoralityAnalysisPanel(self.right),
            'morality-curve-comparison': MoralityCurveComparisonPanel(self.right),
            'morality-raw-comparison': MoralityRawComparisonPanel(self.right),
            'morality-antialign-comparison': MoralityAntialignComparisonPanel(self.right),
            'morality-narrative-comparison': MoralityNarrativeComparisonPanel(self.right),
            'morality-stability': MoralityStabilityPanel(self.right),
            'morality-identifiability': MoralityIdentifiabilityPanel(self.right),
            'morality-group-identifiability': MoralityGroupIdentifiabilityPanel(self.right),
            'morality-single-identifiability': MoralitySingleIdentifiabilityPanel(self.right),
            'morality-single-density': MoralitySingleDensityPanel(self.right),
            'morality-age-curve': MoralityAgeCurve(self.right),
            'morality-mahalanobis': MoralitySingleMahalanobisPanel(self.right),
            'morality-multi-mahalanobis': MoralityMultiMahalanobisPanel(self.right),
            'morality-comparison': MoralityComparisonPanel(self.right),
            'morality-clustering': MoralityClusteringPanel(self.right),
            'morality-file-clustering': MoralityFileClusteringPanel(self.right),
            'morality-tsne': MoralityTSNEPanel(self.right)
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
            for key in ['personality', 'personality-analysis', 'personality-stats',
                        'value', 'value-analysis', 'value-stats',
                        'morality', 'morality-analysis', 'morality-stats']:
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

        # One function tree for the selected instrument. Section nodes use the section id as the
        # tree item id; function nodes use the function id (resolved to a panel via FUNCTIONS).
        for section_id, func_ids in SECTIONS:
            tv.insert('', 'end', section_id, text=lang[SECTION_LABEL_KEYS[section_id]], image='')
            for func_id in func_ids:
                if FUNCTIONS[func_id][self.instrument] is None:
                    continue
                tv.insert(section_id, 'end', func_id, text=lang[FUNCTION_LABEL_KEYS[func_id]], image='')
            tv.item(section_id, open=True)

    def on_instrument_change(self, event=None):
        new_instrument = self.instrument_var.get()
        if new_instrument == self.instrument:
            return
        self.instrument = new_instrument
        self.recreate(self.treeView)
        # Hide every panel so no stale instrument's panel stays visible.
        for p in self.panels.values():
            p.main.pack_forget()

    def treeSelect(self, event):
        if not self.treeView.selection():
            return

        selected_item = self.treeView.selection()[0]

        # The selected tree item is a function id; resolve it to the panel for the current instrument.
        panel_key = FUNCTIONS.get(selected_item, {}).get(self.instrument)

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
        self.instrument_label.config(text=LANGUAGES[lang].get('instrument', 'Instrument'))
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
