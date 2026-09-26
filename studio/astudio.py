import matplotlib
matplotlib.use('TkAgg')

import tkinter as tk
from tkinter import *
from tkinter import filedialog
import os

import ttkbootstrap as ttk

from studio import theme
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
        'theme': '主题',
        'landing_hint': '在左侧选择一个分析功能',
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
        'theme': 'Theme',
        'landing_hint': 'Select a function on the left',
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

# Bootstrap Icons glyph per nav item (rendered via ttk.Icon, monochrome, theme-aware).
FUNCTION_ICONS = {
    'browse': 'table', 'stats': 'bar-chart',
    'analysis': 'clipboard-data', 'age_personality_curve': 'graph-up',
    'mahalanobis': 'sliders', 'clustering': 'grid-3x3-gap',
    'file_clustering': 'folder2-open', 'tsne': 'dice-5',
    'comparison': 'columns', 'ocean_density': 'activity',
    'consistency': 'link-45deg', 'factor': 'diagram-2',
    'curve': 'bezier', 'raw': 'graph-up-arrow',
    'antialign': 'arrow-left-right', 'narrative': 'book',
    'stability': 'shield-check', 'single_density': 'circle',
    'identifiability': 'fingerprint', 'group_identifiability': 'people',
    'single_identifiability': 'person', 'multi_mahalanobis': 'arrows-angle-expand',
}

class MainWindow:
    def __init__(self, root) -> None:
        self.lang = 'zh'
        self.instrument = 'personality'
        self.current_theme = theme.DEFAULT_THEME
        self.root = root
        root.title('Agentic Society')

        # Bootstrap theme (ttkbootstrap) — drives all chrome and data tables.
        theme.set_theme(self.current_theme)

        # --- Body: sidebar + content ---
        self.main = ttk.Frame(root)
        self.main.pack(fill=BOTH, expand=True)

        self.menu(root)

        # Fixed-width sidebar. Background follows the theme (no grey wash); the
        # vertical separator is what divides it from the content.
        self.sidebar = ttk.Frame(self.main, width=theme.SIDEBAR_WIDTH)
        self.sidebar.pack(side=LEFT, fill=Y)
        self.sidebar.pack_propagate(False)

        # Logo pinned to the top of the sidebar.
        self.logo_label = ttk.Label(self.sidebar, text='Agentic Society',
                                    font=theme.FONT_LOGO)
        self.logo_label.pack(anchor=W, padx=24, pady=(26, 20))

        # Instrument selector.
        self.instrument_label = ttk.Label(self.sidebar,
                                          text=LANGUAGES[self.lang].get('instrument', 'Instrument'),
                                          style='Caption.TLabel', bootstyle='secondary')
        self.instrument_label.pack(anchor=W, padx=24)
        self.instrument_var = StringVar(value=self.instrument)
        instrument_combo = ttk.Combobox(self.sidebar, textvariable=self.instrument_var,
                                        values=['personality', 'value', 'morality'], state='readonly')
        instrument_combo.pack(fill=X, padx=24, pady=(6, 16))
        instrument_combo.bind('<<ComboboxSelected>>', self.on_instrument_change)

        # Function tree fills the middle of the sidebar.
        self.treeView = self.tree(self.sidebar)

        # Language + theme controls pinned to the bottom of the sidebar.
        bottom = ttk.Frame(self.sidebar)
        bottom.pack(side=BOTTOM, fill=X, padx=24, pady=(8, 18))

        self.lang_label = ttk.Label(bottom, text=LANGUAGES[self.lang]['language'],
                                    style='Caption.TLabel', bootstyle='secondary')
        self.lang_label.pack(anchor=W)
        self.lang_var = StringVar(value=self.lang)
        lang_combo = ttk.Combobox(bottom, textvariable=self.lang_var, values=['zh', 'en'], state='readonly')
        lang_combo.pack(fill=X, pady=(4, 12))
        lang_combo.bind('<<ComboboxSelected>>', self.on_lang_change)

        self.theme_label = ttk.Label(bottom, text=LANGUAGES[self.lang]['theme'],
                                     style='Caption.TLabel', bootstyle='secondary')
        self.theme_label.pack(anchor=W)
        self.theme_var = StringVar(value=self.current_theme)
        theme_combo = ttk.Combobox(bottom, textvariable=self.theme_var, values=theme.available_themes(), state='readonly')
        theme_combo.pack(fill=X, pady=(4, 0))
        theme_combo.bind('<<ComboboxSelected>>', self.on_theme_change)

        # Vertical divider between sidebar and content; drag it to resize the
        # sidebar. The wide invisible frame gives a comfortable grab target, the
        # 2px Separator inside it is the visual line.
        self.divider = ttk.Frame(self.main, width=8, cursor='sb_h_double_arrow')
        self.divider.pack(side=LEFT, fill=Y)
        self.divider.pack_propagate(False)
        ttk.Separator(self.divider, orient='vertical').pack(side=LEFT, fill=Y)
        self.divider.bind('<Button-1>', self._start_sidebar_resize)
        self.divider.bind('<B1-Motion>', self._resize_sidebar)
        self.divider.bind('<ButtonRelease-1>', self._end_sidebar_resize)

        # Content area.
        self.right = ttk.Frame(self.main)
        self.right.pack(side=LEFT, fill=BOTH, expand=True)

        # Landing state for the empty content area
        self.landing = ttk.Frame(self.right)
        self.landing.pack(fill=BOTH, expand=True)
        center = ttk.Frame(self.landing)
        center.pack(expand=True)
        self.landing_title = ttk.Label(center, text=LANGUAGES[self.lang]['tree_root'],
                                       font=('Segoe UI', 28, 'bold'))
        self.landing_title.pack(pady=(0, 8))
        self.landing_hint = ttk.Label(center, text=LANGUAGES[self.lang]['landing_hint'],
                                      bootstyle='secondary')
        self.landing_hint.pack()
        
        # Initialize all panels
        # Panel registry: key -> class. Instances are built lazily on first show so the
        # app doesn't construct ~60 panels (and their matplotlib figures) at startup.
        self._panel_classes = {
            'personality': PersonalityBrowser,
            'personality-analysis': PersonalityAnalysis,
            'personality-stats': PersonalityStats,
            'mahalanobis': SingleMahalanobisPanel,
            'multi_mahalanobis': MultiMahalanobisPanel,
            'clustering': ClusteringPanel,
            'file-clustering': FileClusteringPanel,
            'tsne': TSNEPanel,
            'comparison': ComparisonPanel,
            'ocean-density': OceanDensityPanel,
            'consistency': InternalConsistencyPanel,
            'factor': FactorAnalysisPanel,
            'identifiability': IdentifiabilityPanel,
            'group-identifiability': GroupIdentifiabilityPanel,
            'single-identifiability': SingleIdentifiabilityPanel,
            'age-personality-curve': AgePersonalityCurve,
            'curve_comparison': CurveComparisonPanel,
            'raw_comparison': RawComparisonPanel,
            'antialign_comparison': AntialignComparisonPanel,
            'narrative_comparison': NarrativeComparisonPanel,
            'stability': StabilityAnalysisPanel,
            'single-density': SingleDensityPanel,
            'value': ValueBrowser,
            'value-stats': ValueStats,
            'value-analysis': ValueAnalysisPanel,
            'value-curve-comparison': ValueCurveComparisonPanel,
            'value-raw-comparison': ValueRawComparisonPanel,
            'value-antialign-comparison': ValueAntialignComparisonPanel,
            'value-narrative-comparison': ValueNarrativeComparisonPanel,
            'value-stability': ValueStabilityPanel,
            'value-identifiability': ValueIdentifiabilityPanel,
            'value-group-identifiability': ValueGroupIdentifiabilityPanel,
            'value-single-identifiability': ValueSingleIdentifiabilityPanel,
            'value-single-density': ValueSingleDensityPanel,
            'value-age-curve': ValueAgeCurve,
            'value-mahalanobis': ValueSingleMahalanobisPanel,
            'value-multi-mahalanobis': ValueMultiMahalanobisPanel,
            'value-comparison': ValueComparisonPanel,
            'value-clustering': ValueClusteringPanel,
            'value-file-clustering': ValueFileClusteringPanel,
            'value-tsne': ValueTSNEPanel,
            'morality': MoralityBrowser,
            'morality-stats': MoralityStats,
            'morality-analysis': MoralityAnalysisPanel,
            'morality-curve-comparison': MoralityCurveComparisonPanel,
            'morality-raw-comparison': MoralityRawComparisonPanel,
            'morality-antialign-comparison': MoralityAntialignComparisonPanel,
            'morality-narrative-comparison': MoralityNarrativeComparisonPanel,
            'morality-stability': MoralityStabilityPanel,
            'morality-identifiability': MoralityIdentifiabilityPanel,
            'morality-group-identifiability': MoralityGroupIdentifiabilityPanel,
            'morality-single-identifiability': MoralitySingleIdentifiabilityPanel,
            'morality-single-density': MoralitySingleDensityPanel,
            'morality-age-curve': MoralityAgeCurve,
            'morality-mahalanobis': MoralitySingleMahalanobisPanel,
            'morality-multi-mahalanobis': MoralityMultiMahalanobisPanel,
            'morality-comparison': MoralityComparisonPanel,
            'morality-clustering': MoralityClusteringPanel,
            'morality-file-clustering': MoralityFileClusteringPanel,
            'morality-tsne': MoralityTSNEPanel,
        }
        # Constructed panels, keyed identically to _panel_classes.
        self.panels = {}
        
        self.set_language(self.lang)

    def _configure_tree_tags(self, tv):
        fg, muted = theme.tree_colors()
        tv.tag_configure('section', font=theme.FONT_NAV_SECTION, foreground=muted)
        tv.tag_configure('item', font=theme.FONT_NAV_ITEM, foreground=fg)

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
        # Tree + scrollbar live in their own frame packed to the top (the same
        # slot the bare tree used to occupy), so the bottom controls below keep
        # their vertical space instead of being squeezed out by a side-packed tree.
        wrap = ttk.Frame(frame)
        wrap.pack(fill=tk.BOTH, expand=True)
        tv = ttk.Treeview(wrap, show='tree', style='Nav.Treeview')
        sb = ttk.Scrollbar(wrap, orient='vertical', command=tv.yview, bootstyle='round')
        tv.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        tv.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(16, 0))
        self._configure_tree_tags(tv)
        self.recreate(tv)
        tv.bind("<<TreeviewSelect>>", self.treeSelect)
        return tv

    def updateTree(self):
        self.recreate(self.treeView)
        self.sidebar.update()

    def recreate(self, tv):
        for i in tv.get_children():
            tv.delete(i)

        lang = LANGUAGES[self.lang]

        for idx, (section_id, func_ids) in enumerate(SECTIONS):
            # A blank spacer row before every section after the first keeps the
            # four groups from running together into one wall of text.
            if idx > 0:
                tv.insert('', 'end', f'__spacer_{idx}', text='', tags=('section',))
            tv.insert('', 'end', section_id, text=lang[SECTION_LABEL_KEYS[section_id]].upper(),
                      tags=('section',))
            for func_id in func_ids:
                if FUNCTIONS[func_id][self.instrument] is None:
                    continue
                icon = FUNCTION_ICONS.get(func_id)
                image = ttk.Icon(icon, size=16, color='secondary') if icon else ''
                # The tree column puts the glyph flush against the label; lead the
                # text with spaces to give the icon breathing room.
                tv.insert(section_id, 'end', func_id,
                          text='  ' + lang[FUNCTION_LABEL_KEYS[func_id]],
                          image=image, tags=('item',))
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
        self.landing.pack(fill=BOTH, expand=True)

    def _ensure_panel(self, key):
        panel = self.panels.get(key)
        if panel is None:
            cls = self._panel_classes.get(key)
            if cls is None:
                return None
            panel = cls(self.right)
            # Panel __init__ packs its `main` frame; hide it until it is selected.
            panel.main.pack_forget()
            self.panels[key] = panel
            self._apply_language(panel)
        return panel

    def _apply_language(self, panel):
        import inspect
        if hasattr(panel, 'set_language'):
            sig = inspect.signature(panel.set_language)
            if len(sig.parameters) == 3:  # expects self, lang, lang_dict
                panel.set_language(self.lang, LANGUAGES[self.lang])
            else:  # expects self, lang
                panel.set_language(self.lang)
        if hasattr(panel, 'update_texts'):  # for the stats panels
            panel.update_texts(self.lang)

    def treeSelect(self, event):
        if not self.treeView.selection():
            return

        selected_item = self.treeView.selection()[0]

        # Blank spacer rows between sections are not selectable functions.
        if selected_item.startswith('__spacer_'):
            self.treeView.selection_remove(selected_item)
            return

        # The selected tree item is a function id; resolve it to the panel for the current instrument.
        panel_key = FUNCTIONS.get(selected_item, {}).get(self.instrument)

        if not panel_key or panel_key not in self._panel_classes:
            # Hide all panels if a non-leaf node is selected
            for p in self.panels.values():
                p.main.pack_forget()
            self.landing.pack(fill=BOTH, expand=True)
            return

        # Show the selected panel (building it on first use) and hide the others.
        self._ensure_panel(panel_key)
        self.landing.pack_forget()
        for key, p in self.panels.items():
            if key == panel_key:
                p.main.pack(fill=BOTH, expand=True)
                # Pass control methods if needed
                if hasattr(p, 'setData'):
                    p.setData(selected_item, self.updateTree)
            else:
                p.main.pack_forget()

    def set_language(self, lang):
        self.lang = lang
        self.lang_var.set(lang)
        self.menu(self.root)
        self.instrument_label.configure(text=LANGUAGES[lang].get('instrument', 'Instrument'))
        self.lang_label.configure(text=LANGUAGES[lang]['language'])
        self.theme_label.configure(text=LANGUAGES[lang]['theme'])
        self.landing_title.configure(text=LANGUAGES[lang]['tree_root'])
        self.landing_hint.configure(text=LANGUAGES[lang]['landing_hint'])
        self.recreate(self.treeView)
        for panel in self.panels.values():
            self._apply_language(panel)

    def on_lang_change(self, event=None):
        new_lang = self.lang_var.get()
        if new_lang != self.lang:
            self.set_language(new_lang)

    def on_theme_change(self, event=None):
        new_theme = self.theme_var.get()
        if new_theme != self.current_theme:
            self.change_theme(new_theme)

    def _start_sidebar_resize(self, event):
        self._resizing = True
        self._resize_start_x = event.x_root
        self._resize_start_width = self.sidebar.winfo_width()

    def _resize_sidebar(self, event):
        if not getattr(self, '_resizing', False):
            return
        new_width = self._resize_start_width + (event.x_root - self._resize_start_x)
        new_width = max(theme.SIDEBAR_WIDTH - 60, min(theme.SIDEBAR_WIDTH + 260, new_width))
        self.sidebar.configure(width=new_width)

    def _end_sidebar_resize(self, event):
        self._resizing = False

    def change_theme(self, theme_name):
        self.current_theme = theme_name
        self.theme_var.set(theme_name)
        theme.set_theme(theme_name)
        self._configure_tree_tags(self.treeView)
        # Icons are rendered with the theme's secondary color, so rebuild the tree
        # to re-render them against the new theme.
        self.recreate(self.treeView)
        # Recolor any already-built matplotlib figures to match the new theme.
        for panel in self.panels.values():
            for attr in ('fig', 'figure'):
                fig = getattr(panel, attr, None)
                if fig is not None:
                    theme.apply_mpl_theme(fig)
                    if fig.canvas is not None:
                        fig.canvas.draw_idle()

if __name__ == "__main__":
    root = ttk.Window()
    app = MainWindow(root)
    root.state('zoomed')
    
    def _quit():
        root.quit()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", _quit)
    root.mainloop()
