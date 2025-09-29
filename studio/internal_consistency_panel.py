import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import pingouin as pg
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import sqlite3
import json
import os

from studio.collapsible_help_panel import CollapsibleHelpPanel
from studio.progress_dialog import ProgressManager
from studio.analysis_panel_utils import show_analysis_window
from asociety.generator.qwen_analyzer import save_figure_to_bytes, analyze_image_with_text

DOMAIN_LABELS = {
    'zh': {"O": "开放性", "C": "尽责性", "E": "外向性", "A": "宜人性", "N": "神经质"},
    'en': {"O": "Openness", "C": "Conscientiousness", "E": "Extraversion", "A": "Agreeableness", "N": "Neuroticism"}
}
UI_TEXT = {
    'zh': {
        'select_db': "选择数据库文件...",
        'run_analysis': "运行分析",
        'analysis_title': "内部一致性信度分析",
        'analysis_results': "分析结果",
        'alpha_ylabel': "Cronbach's Alpha (α)",
        'plot_title': "内部一致性信度",
        'acceptable_text': "可接受 (0.7)",
        'file_dialog_title': "选择数据库文件"
    },
    'en': {
        'select_db': "Select Database File...",
        'run_analysis': "Run Analysis",
        'analysis_title': "Internal Consistency Reliability Analysis",
        'analysis_results': "Analysis Results",
        'alpha_ylabel': "Cronbach's Alpha (α)",
        'plot_title': "Internal Consistency Reliability",
        'acceptable_text': "Acceptable (0.7)",
        'file_dialog_title': "Select a database file"
    }
}
from studio.help_constants import helpcnstants
HELP_CONTENT = helpcnstants['internal_consistency']

DOMAIN_TO_FACETS = {
    "N": [1, 6, 11, 16, 21, 26], "E": [2, 7, 12, 17, 22, 27],
    "O": [3, 8, 13, 18, 23, 28], "A": [4, 9, 14, 19, 24, 29],
    "C": [5, 10, 15, 20, 25, 30],
}

class InternalConsistencyPanel:
    def __init__(self, parent):
        self.main = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)
        
        main_content_frame = ttk.Frame(self.main)
        self.main.add(main_content_frame, weight=3)

        self.db_path = tk.StringVar()
        self.figure = None
        self.canvas = None
        self.message_label = None
        self.current_lang = 'zh'
        self.alphas = None

        self._create_widgets(main_content_frame)

        help_config = {"title": HELP_CONTENT[self.current_lang]['title'], "content": HELP_CONTENT[self.current_lang]['content']}
        self.collapsible_help = CollapsibleHelpPanel(self.main, help_config, weight=1)

    def _create_widgets(self, parent):
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill='x', padx=10, pady=10)

        self.select_button = ttk.Button(control_frame, text="Select Database File", command=self.select_db_file)
        self.select_button.pack(side='left', padx=(0, 5))
        
        self.db_label = ttk.Label(control_frame, textvariable=self.db_path)
        self.db_label.pack(side='left', fill='x', expand=True)

        self.run_button = ttk.Button(control_frame, text="Run Analysis", command=self.start_analysis, state=tk.DISABLED)
        self.run_button.pack(side='left', padx=(5, 0))

        self.qwen_button = ttk.Button(control_frame, text="结果解析 (AI)", command=self.start_qwen_analysis, state=tk.DISABLED)
        self.qwen_button.pack(side='left', padx=(5, 0))

        self.copy_button = ttk.Button(control_frame, text="Copy Data (JSON)", command=self.copy_analysis_data_to_clipboard, state=tk.DISABLED)
        self.copy_button.pack(side='left', padx=(5, 0))

        self.progress_manager = ProgressManager(self.main)
        
        # Vertical PanedWindow for plot and data table
        self.results_paned_window = ttk.PanedWindow(parent, orient=tk.VERTICAL)
        self.results_paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.plot_frame = ttk.Frame(self.results_paned_window)
        self.results_paned_window.add(self.plot_frame, weight=3)

        self.data_frame = ttk.Frame(self.results_paned_window)
        self.results_paned_window.add(self.data_frame, weight=1)
        
        self.message_frame = ttk.Frame(parent)
        self.message_frame.pack(fill='x', padx=5, pady=5)

        self.metrics_tree = None

    def select_db_file(self):
        filepath = filedialog.askopenfilename(
            title=UI_TEXT[self.current_lang]['file_dialog_title'],

            filetypes=(("Database files", "*.db"), ("All files", "*.*")),
            initialdir='data/db/backup'
        )
        if filepath:
            self.db_path.set(filepath)
            self.run_button.config(state=tk.NORMAL)
            self._clear_all()

    def start_analysis(self):
        db_path = self.db_path.get()
        if not db_path:
            return

        def analysis_task(progress_dialog):
            progress_dialog.update_message("Loading data...")
            df = self._load_data(db_path)
            if progress_dialog.is_cancelled(): return None
            
            progress_dialog.update_message("Calculating reliability...")
            alphas = self._calculate_alphas(df)
            return alphas

        def on_success(result):
            if result is not None:
                self.alphas = result
                self.figure = self._create_plot(self.alphas)
                self._display_plot(self.figure)
                self._display_metrics_table(self.alphas)
                self.qwen_button.config(state=tk.NORMAL)
                self.copy_button.config(state=tk.NORMAL)

        def on_error(error):
            self._show_message(f"Error: {error}")

        self._clear_all()
        self.progress_manager.run_with_progress(
            analysis_task,
            title="Internal Consistency Analysis",
            message="Preparing analysis...",
            success_callback=on_success,
            error_callback=on_error
        )

    def _load_data(self, db_path):
        conn = sqlite3.connect(db_path)
        try:
            df_raw = pd.read_sql_query("SELECT persona_id, personality_json FROM personality", conn)
            if df_raw.empty:
                raise ValueError("The 'personality' table is empty.")
            
            all_answers = []
            for _, row in df_raw.iterrows():
                if isinstance(row['personality_json'], str):
                    data = json.loads(row['personality_json'])
                    answer_list = data.get('person', {}).get('result', {}).get('compare', {}).get('user_answers_reversed')
                    if answer_list:
                        answers = {item['id_question']: item['id_select'] for item in answer_list}
                        all_answers.append(answers)
            
            if not all_answers:
                raise ValueError("No valid answer data found in the 'personality' table.")

            df = pd.DataFrame(all_answers)
            num_questions = max(max(d.keys()) for d in all_answers if d)
            column_range = range(1, 301) if num_questions > 120 else range(1, 121)
            df = df.reindex(columns=column_range)
            return df
        finally:
            conn.close()

    def _calculate_alphas(self, df):
        num_questions = len(df.columns)
        

        alphas = {}
        domains = ["O", "C", "E", "A", "N"]
        for domain in domains:
            domain_questions = self._get_domain_questions(domain, num_questions)
            existing_qs = [q for q in domain_questions if q in df.columns]
            if existing_qs:
                domain_df = df[existing_qs].dropna()
                if len(domain_df) > 1:
                    alpha_results = pg.cronbach_alpha(data=domain_df)
                    alphas[domain] = alpha_results[0]
                else:
                    alphas[domain] = float('nan')
        
        return alphas

    def _get_domain_questions(self, domain, num_questions=120):
        questions_per_facet = 4 if num_questions <= 120 else 10
        num_facets = 30
        domain_q_numbers = []
        facets = DOMAIN_TO_FACETS[domain]
        for i in range(questions_per_facet):
            for facet_num in facets:
                q_num = i * num_facets + facet_num
                domain_q_numbers.append(q_num)
        return sorted(domain_q_numbers)

    def _create_plot(self, alphas):
        fig, ax = plt.subplots(figsize=(8, 6))
        db_path = self.db_path.get()
        domains = ["O", "C", "E", "A", "N"]
        domain_labels = DOMAIN_LABELS[self.current_lang]
        
        alpha_values = [alphas.get(d, float('nan')) for d in domains]
        display_labels = [domain_labels.get(d, d) for d in domains]

        bars = ax.bar(display_labels, alpha_values, color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'])
        ax.set_ylabel(UI_TEXT[self.current_lang]['alpha_ylabel'])
        ax.set_title(f"{UI_TEXT[self.current_lang]['plot_title']}\n(Source: {os.path.basename(db_path)})")
        ax.set_ylim(0, 1)
        ax.axhline(y=0.7, color='grey', linestyle='--', linewidth=1)
        ax.text(len(domains)-0.5, 0.71, UI_TEXT[self.current_lang]['acceptable_text'], color='grey', ha='center')
   
        for bar in bars:
            yval = bar.get_height()
            if not pd.isna(yval):
                ax.text(bar.get_x() + bar.get_width()/2.0, yval + 0.02, f'{yval:.3f}', ha='center', va='bottom')
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        
        return fig

    def copy_analysis_data_to_clipboard(self):
        if not self.alphas:
            messagebox.showwarning("No Data", "There is no analysis data to copy. Please run the analysis first.")
            return

        try:
            # Prepare data for JSON export
            data_to_export = {
                "source_file": os.path.basename(self.db_path.get()),
                "cronbach_alpha": self.alphas
            }
            
            json_data = json.dumps(data_to_export, indent=4)

            self.main.clipboard_clear()
            self.main.clipboard_append(json_data)
            
            messagebox.showinfo("Copied", "Analysis data has been copied to the clipboard in JSON format.")

        except Exception as e:
            messagebox.showerror("Copy Error", f"An error occurred while copying data: {e}")

    def _display_plot(self, fig):
        self._clear_plot()
        self.figure = fig
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    def _display_metrics_table(self, alphas):
        if self.metrics_tree:
            self.metrics_tree.destroy()

        self.metrics_tree = ttk.Treeview(self.data_frame, columns=('Domain', 'Cronbach\'s Alpha'), show='headings')
        self.metrics_tree.heading('Domain', text='Domain')
        self.metrics_tree.heading('Cronbach\'s Alpha', text='Cronbach\'s Alpha')
        self.metrics_tree.column('Domain', width=150)
        self.metrics_tree.column('Cronbach\'s Alpha', width=150)

        domain_labels = DOMAIN_LABELS[self.current_lang]
        for domain, alpha in alphas.items():
            self.metrics_tree.insert('', 'end', values=(domain_labels.get(domain, domain), f"{alpha:.4f}"))

        self.metrics_tree.pack(fill=tk.BOTH, expand=True)

    def _clear_all(self):
        self._clear_plot()
        self._clear_message()
        if self.metrics_tree:
            self.metrics_tree.destroy()
            self.metrics_tree = None
        self.qwen_button.config(state=tk.DISABLED)
        self.copy_button.config(state=tk.DISABLED)

    def _clear_plot(self):
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
            self.canvas = None
        if self.figure:
            plt.close(self.figure)
            self.figure = None
            
    def _show_message(self, text, is_error=True):
        self._clear_message()
        color = "red" if is_error else "black"
        self.message_label = ttk.Label(self.message_frame, text=text, foreground=color, wraplength=600)
        self.message_label.pack()

    def _clear_message(self):
        if self.message_label:
            self.message_label.destroy()
            self.message_label = None

    def start_qwen_analysis(self):
        if self.figure is None:
            return

        def analysis_task(progress_dialog):
            progress_dialog.update_message("Preparing image data...")
            image_bytes = save_figure_to_bytes(self.figure)
            if progress_dialog.is_cancelled(): return None

            progress_dialog.update_message("Building analysis prompt...")
            prompt = self._build_consistency_prompt()

            progress_dialog.update_message("Calling AI API for analysis...")
            analysis_result = analyze_image_with_text(image_bytes, prompt)
            return analysis_result

        def on_success(result):
            if result:
                show_analysis_window(self.main, result)

        def on_error(error):
            self._show_message(f"AI Analysis Error: {error}")

        self.progress_manager.run_with_progress(
            analysis_task,
            title="AI Result Analysis",
            message="Connecting to AI...",
            success_callback=on_success,
            error_callback=on_error
        )

    def _build_consistency_prompt(self):
        alpha_values = "\n".join([f"- {DOMAIN_LABELS['zh'][domain]}: {value:.3f}" for domain, value in self.alphas.items()])
        return f"""
You are an expert psychometrician. Your task is to interpret the results of an internal consistency analysis for a Big Five personality questionnaire.

**Background Information:**
- **Goal**: To assess the reliability of the scales measuring the Big Five personality traits.
- **Metric**: Cronbach's Alpha (α), which measures how well a set of items collectively measure a single underlying latent construct.
- **Data Source**: {os.path.basename(self.db_path.get())}

**Image Content:**
The bar chart displays the Cronbach's Alpha value for each of the five personality domains: Openness (开放性), Conscientiousness (尽责性), Extraversion (外向性), Agreeableness (宜人性), and Neuroticism (神经质).

**Cronbach's Alpha Values:**
{alpha_values}

**Interpretation Guidelines:**
- **α ≥ 0.9**: Excellent
- **0.8 ≤ α < 0.9**: Good
- **0.7 ≤ α < 0.8**: Acceptable
- **0.6 ≤ α < 0.7**: Questionable
- **0.5 ≤ α < 0.6**: Poor
- **α < 0.5**: Unacceptable
The dashed line at 0.7 on the chart marks the generally accepted minimum threshold for reliability.

**Your Task:**
1.  **Overall Assessment**: Provide a general summary of the questionnaire's reliability based on the chart.
2.  **Domain-by-Domain Analysis**: For each of the five domains, evaluate its Cronbach's Alpha value according to the guidelines above. State whether the reliability is excellent, good, acceptable, questionable, poor, or unacceptable.
3.  **Identify Strengths and Weaknesses**:
    - Which personality domains are measured most reliably?
    - Which domains have low reliability and may need improvement (e.g., by revising or removing certain questions)?
4.  **Conclusion**: What is your final conclusion about the internal consistency of this personality test? Is it generally reliable for use?

Please provide your analysis in a clear, structured format.
"""

    def set_language(self, lang):
        self.current_lang = lang
        self.collapsible_help.update_content(
            title=HELP_CONTENT[lang]['title'],
            content=HELP_CONTENT[lang]['content']
        )
