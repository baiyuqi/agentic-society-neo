import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import sqlite3
import json
import os
import seaborn as sns
from factor_analyzer import FactorAnalyzer
from factor_analyzer.factor_analyzer import calculate_bartlett_sphericity, calculate_kmo

from studio.collapsible_help_panel import CollapsibleHelpPanel
from studio.progress_dialog import ProgressManager
from studio.analysis_panel_utils import show_analysis_window
from asociety.generator.qwen_analyzer import save_figure_to_bytes, analyze_image_with_text

UI_TEXT = {
    'zh': {
        'select_db': "选择数据库文件...",
        'run_analysis': "运行因素分析",
        'analysis_results': "分析结果",
        'factor_analysis': "因素分析"
    },
    'en': {
        'select_db': "Select Database File",
        'run_analysis': "Run Factor Analysis",
        'analysis_results': "Analysis Results",
        'factor_analysis': "Factor Analysis"
    }
}
from studio.help_constants import helpcnstants
HELP_CONTENT = helpcnstants['factor_analysis']


class FactorAnalysisPanel:
    def __init__(self, parent):
        self.main = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)
        
        main_content_frame = ttk.Frame(self.main)
        self.main.add(main_content_frame, weight=3)

        self.db_path = tk.StringVar()
        self.db_path_display = tk.StringVar()
        self.factor_option = tk.StringVar(value='fixed')
        self.results_text = tk.StringVar()
        self.current_lang = 'zh'
        self.parent = parent
        self.analysis_results = {}

        self.canvas1, self.canvas2 = None, None
        self.figure1, self.figure2 = None, None
        self.message_label = None
        self.loadings_tree = None

        self._create_widgets(main_content_frame)

        help_config = {"title": HELP_CONTENT[self.current_lang]['title'], "content": HELP_CONTENT[self.current_lang]['content']}
        self.collapsible_help = CollapsibleHelpPanel(self.main, help_config, weight=1)

    def _create_widgets(self, parent):
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill='x', padx=5, pady=5)

        self.select_button = ttk.Button(control_frame, text="Select Database File", command=self.select_db_file)
        self.select_button.pack(side='left', padx=(0, 5))
        
        self.db_label = ttk.Label(control_frame, textvariable=self.db_path_display)
        self.db_label.pack(side='left', fill='x', expand=True)

        factor_choice_frame = ttk.LabelFrame(control_frame, text="Factor Count")
        factor_choice_frame.pack(side='left', padx=(5, 5), fill='y')

        fixed_rb = ttk.Radiobutton(factor_choice_frame, text="Fixed (5)", variable=self.factor_option, value='fixed')
        fixed_rb.pack(anchor='w')

        free_rb = ttk.Radiobutton(factor_choice_frame, text="From Eigenvalues (>1)", variable=self.factor_option, value='free')
        free_rb.pack(anchor='w')

        self.run_button = ttk.Button(control_frame, text="Run Factor Analysis", command=self.start_analysis, state=tk.DISABLED)
        self.run_button.pack(side='left', padx=(5, 0))

        self.qwen_button = ttk.Button(control_frame, text="结果解析 (AI)", command=self.start_qwen_analysis, state=tk.DISABLED)
        self.qwen_button.pack(side='left', padx=(5, 0))

        self.copy_button = ttk.Button(control_frame, text="Copy Data (JSON)", command=self.copy_analysis_data_to_clipboard, state=tk.DISABLED)
        self.copy_button.pack(side='left', padx=(5, 0))

        self.progress_manager = ProgressManager(self.main)

        results_frame = ttk.LabelFrame(parent, text="Analysis Results")
        results_frame.pack(fill='x', padx=5, pady=5)
        self.results_label = ttk.Label(results_frame, textvariable=self.results_text, justify=tk.LEFT)
        self.results_label.pack(fill='x', padx=5, pady=5)

        self.fig = None # For combined plot

        # Paned window for plots and data table
        self.results_paned_window = ttk.PanedWindow(parent, orient=tk.VERTICAL)
        self.results_paned_window.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Frame for the plots
        self.plot_frame = ttk.Frame(self.results_paned_window)
        self.results_paned_window.add(self.plot_frame, weight=2)

        # Frame for the data table
        self.data_frame = ttk.Frame(self.results_paned_window)
        self.results_paned_window.add(self.data_frame, weight=1)

        self.message_frame = ttk.Frame(parent)
        self.message_frame.pack(fill='x', padx=5, pady=5)

    def select_db_file(self):
        filepath = filedialog.askopenfilename(
            title="Select a database file",
            filetypes=(("Database files", "*.db"), ("All files", "*.*")),
            initialdir='data/db/backup'
        )
        if filepath:
            self.db_path.set(filepath)
            
            # Create a shortened path for display
            max_len = 40  # Max length of the path to display
            filename = os.path.basename(filepath)
            if len(filepath) > max_len:
                # Show last part of the path with ellipsis
                display_path = "..." + filepath[-max_len:]
            else:
                display_path = filepath
            self.db_path_display.set(display_path)

            self.run_button.config(state=tk.NORMAL)

    def start_analysis(self):
        db_path = self.db_path.get()
        if not db_path:
            return

        def analysis_task(progress_dialog):
            progress_dialog.update_message("Loading and preparing data...")
            df = self._load_and_prepare_data(db_path)
            if progress_dialog.is_cancelled(): return None

            progress_dialog.update_message("Performing analysis...")
            results = self._perform_analysis(df)
            return results

        def on_success(result):
            if result:
                self.analysis_results = result
                self.results_text.set(result['text'])
                
                # Create plots in the main thread
                self.fig = self._create_plots(result)
                
                self.full_loadings_df = result['loadings']
                
                self._display_plot(self.fig)
                self._display_loadings_table()

                self.qwen_button.config(state=tk.NORMAL)
                self.copy_button.config(state=tk.NORMAL)

        def on_error(error):
            self._show_message(f"Error: {error}")

        self._clear_all()
        self.progress_manager.run_with_progress(
            analysis_task,
            title="Factor Analysis",
            message="Preparing analysis...",
            success_callback=on_success,
            error_callback=on_error
        )

    def _load_and_prepare_data(self, db_path):
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
                raise ValueError("No valid answer data found.")

            df = pd.DataFrame(all_answers)
            num_questions = max(max(d.keys()) for d in all_answers if d)
            column_range = range(1, 301) if num_questions > 120 else range(1, 121)
            df = df.reindex(columns=column_range)
            df.dropna(inplace=True)
            
            if len(df) < 2:
                raise ValueError("Not enough valid data rows for analysis after dropping NaNs.")

            
            
            return df
        finally:
            conn.close()

    def _perform_analysis(self, df):
        import traceback
        try:
            # Proactive check for zero variance columns
            zero_std_cols = df.columns[df.std() == 0]
            if len(zero_std_cols) > 0:
                warning_msg = f"Warning: Found {len(zero_std_cols)} columns with zero variance. They will be removed from the analysis: {zero_std_cols.tolist()}"
                messagebox.showwarning("Data Quality Issue", warning_msg)
                df = df.drop(columns=zero_std_cols)

            if df.shape[1] < 5: # Need at least 5 variables for a 5-factor model
                raise ValueError(f"Not enough columns ({df.shape[1]}) left for analysis after removing zero-variance columns.")

            chi_square_value, p_value = calculate_bartlett_sphericity(df)
            kmo_all, kmo_model = calculate_kmo(df)
            
            results_str = (
                f"Data Adequacy:\n"
                f"  - KMO Test: {kmo_model:.3f}\n"
                f"  - Bartlett's Test: χ²={chi_square_value:.2f}, p={p_value:.3e}"
            )

            fa_scree = FactorAnalyzer(rotation=None, n_factors=len(df.columns))
            fa_scree.fit(df)
            ev, v = fa_scree.get_eigenvalues()
            
            if self.factor_option.get() == 'fixed':
                n_factors = 5
            else:  # 'free'
                n_factors = sum(e > 1 for e in ev)
                if n_factors == 0:
                    n_factors = 1  # Fallback to at least one factor
                results_str += f"\n  - Factors from Eigenvalues (>1): {n_factors}"

            if df.shape[1] < n_factors:
                raise ValueError(f"Not enough columns ({df.shape[1]}) for the requested {n_factors} factors.")

            fa = FactorAnalyzer(n_factors=n_factors, rotation='varimax')
            fa.fit(df)
            loadings_df = pd.DataFrame(fa.loadings_, index=df.columns, columns=[f'F{i+1}' for i in range(n_factors)])
            
            return {
                'text': results_str, 
                'eigenvalues': ev,
                'kmo': kmo_model,
                'bartlett_chi_square': chi_square_value,
                'bartlett_p_value': p_value,
                'loadings': loadings_df,
                'df_shape': df.shape
            }
        except Exception as e:
            error_full_trace = traceback.format_exc()
            error_msg = f"An error occurred during factor analysis:\n\n{str(e)}\n\nFull Traceback:\n{error_full_trace}"
            messagebox.showerror("Analysis Error", error_msg)
            return None

    def _create_plots(self, analysis_results):
        """Creates the matplotlib plots from analysis results. Must be run on the main thread."""
        ev = analysis_results['eigenvalues']
        loadings_df = analysis_results['loadings']
        df_shape = analysis_results['df_shape']

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))

        ax1.scatter(range(1, df_shape[1] + 1), ev)
        ax1.plot(range(1, df_shape[1] + 1), ev)
        ax1.set_title('Scree Plot')
        ax1.set_xlabel('Factors')
        ax1.set_ylabel('Eigenvalue')
        ax1.grid()

        sns.heatmap(loadings_df, cmap='viridis', annot=False, ax=ax2)
        ax2.set_title(f'Factor Loadings Heatmap')
        ax2.set_xlabel('Factors')
        ax2.set_ylabel('Questions')
        
        fig.tight_layout()
        return fig

    def copy_analysis_data_to_clipboard(self):
        if not hasattr(self, 'top_loadings_df') or self.top_loadings_df.empty:
            messagebox.showwarning("No Data", "There is no analysis data to copy. Please run the analysis first.")
            return

        try:
            # Prepare data for JSON export using the top loadings data
            data_to_export = {
                "source_file": os.path.basename(self.db_path.get()),
                "data_adequacy": {
                    "kmo_test": self.analysis_results.get('kmo'),
                    "bartlett_test": {
                        "chi_square": self.analysis_results.get('bartlett_chi_square'),
                        "p_value": self.analysis_results.get('bartlett_p_value')
                    }
                },
                "top_5_loadings_per_factor": self.top_loadings_df.to_dict('records')
            }
            
            json_data = json.dumps(data_to_export, indent=4)

            self.main.clipboard_clear()
            self.main.clipboard_append(json_data)
            
            messagebox.showinfo("Copied", "Top 5 loadings data has been copied to the clipboard in JSON format.")

        except Exception as e:
            messagebox.showerror("Copy Error", f"An error occurred while copying data: {e}")

    def _display_loadings_table(self):
        if self.loadings_tree:
            self.loadings_tree.destroy()
            
        df = self.full_loadings_df
        
        # --- New Logic: Get top 5 loadings for each factor ---
        top_loadings = []
        for factor in df.columns:
            # Sort by the absolute value of the loading for the current factor
            sorted_questions = df[factor].reindex(df[factor].abs().sort_values(ascending=False).index)
            # Get the top 5
            top_5 = sorted_questions.head(5)
            for question_id, loading_score in top_5.items():
                top_loadings.append({
                    'Factor': factor,
                    'Question ID': question_id,
                    'Loading': f"{loading_score:.4f}"
                })
        
        self.top_loadings_df = pd.DataFrame(top_loadings)
        # --- End of New Logic ---

        columns = ['Factor', 'Question ID', 'Loading']
        self.loadings_tree = ttk.Treeview(self.data_frame, columns=columns, show='headings')
        
        for col in columns:
            self.loadings_tree.heading(col, text=col)
            self.loadings_tree.column(col, width=100, anchor='center')

        for index, row in self.top_loadings_df.iterrows():
            # Add a tag for alternating row colors by factor
            tag = row['Factor']
            tag_name = f'{tag}_style'
            
            # Simple alternating color based on even/odd factor number
            factor_num = int(tag.replace('F', ''))
            bg_color = '#f0f0f0' if factor_num % 2 == 0 else '#ffffff'
            
            # Configure the tag's background color. It's safe to call this multiple times.
            self.loadings_tree.tag_configure(tag_name, background=bg_color)

            self.loadings_tree.insert('', 'end', values=list(row), tags=(tag_name,))

        # Add a scrollbar
        scrollbar = ttk.Scrollbar(self.data_frame, orient="vertical", command=self.loadings_tree.yview)
        self.loadings_tree.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side='right', fill='y')
        self.loadings_tree.pack(side='left', fill='both', expand=True)

    def _display_plot(self, fig):
        # self._clear_plot() # This is now handled by _clear_all()
        self.canvas1 = FigureCanvasTkAgg(fig, master=self.plot_frame)
        self.canvas1.draw()
        self.canvas1.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    def _clear_all(self):
        self._clear_plot()
        self._clear_message()
        if self.loadings_tree:
            self.loadings_tree.destroy()
            self.loadings_tree = None
        self.results_text.set("")
        self.qwen_button.config(state=tk.DISABLED)
        self.copy_button.config(state=tk.DISABLED)
        self.analysis_results = {}

    def _clear_plot(self):
        # This method is now simplified for a single plot frame
        if self.canvas1:
            self.canvas1.get_tk_widget().destroy()
        if self.fig:
            plt.close(self.fig)
        self.canvas1, self.fig = None, None

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
        if self.fig is None:
            return

        def analysis_task(progress_dialog):
            progress_dialog.update_message("Preparing image data...")
            image_bytes = save_figure_to_bytes(self.fig)
            if progress_dialog.is_cancelled(): return None

            progress_dialog.update_message("Building analysis prompt...")
            prompt = self._build_factor_analysis_prompt()

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

    def _build_factor_analysis_prompt(self):
        adequacy_results = self.results_text.get()
        
        if self.factor_option.get() == 'fixed':
            goal_desc = 'To determine if the questionnaire items effectively measure the underlying "Big Five" personality traits (Neuroticism, Extraversion, Openness, Agreeableness, Conscientiousness). We are expecting to find 5 significant factors.'
        else:
            goal_desc = 'To explore the underlying factor structure of a personality questionnaire without a preconceived number of factors.'

        return f"""
You are an expert psychologist and statistician specializing in psychometrics. Your task is to interpret the results of an Exploratory Factor Analysis (EFA) performed on a personality questionnaire.

**Background Information:**
- **Goal**: {goal_desc}
- **Analysis Performed**: EFA with Varimax rotation.
- **Data Adequacy**: {adequacy_results}

**Image Content:**
The image contains two plots:
1.  **Scree Plot (Left)**: Shows the eigenvalues for each factor. The eigenvalue represents the amount of variance explained by a factor.
2.  **Factor Loadings Heatmap (Right)**: Shows how strongly each questionnaire item (Y-axis) is associated with each of the 5 extracted factors (X-axis). A brighter color means a higher loading (stronger association).

**Your Task:**
1.  **Assess Data Suitability**: Based on the KMO and Bartlett's test results provided, briefly comment on whether the data was suitable for factor analysis.
2.  **Interpret the Scree Plot**:
    -   Identify the "elbow" of the plot. How many factors does the scree plot suggest we should retain?
    -   Does this number align with the expected 5 factors from the Big Five model?
3.  **Interpret the Factor Loadings Heatmap**:
    -   Describe the overall structure. Does the heatmap show a "simple structure"? (i.e., do most questions load strongly on only ONE factor, with weak loadings on others?).
    -   Are there any items that load on multiple factors (cross-loadings)?
    -   Are there any factors that don't have many strongly loading items?
4.  **Synthesize and Conclude**:
    -   Based on all the evidence (data adequacy, scree plot, and heatmap), what is your overall conclusion about the construct validity of this questionnaire?
    -   Does it appear to be a good measure of 5 distinct personality factors? What are its strengths and weaknesses?

Please provide your analysis in a clear, structured format.
"""
            
    def set_language(self, lang):
        self.current_lang = lang
        self.collapsible_help.update_content(
            title=HELP_CONTENT[lang]['title'],
            content=HELP_CONTENT[lang]['content']
        )

        # 更新按钮和标签文本
        self.select_button.config(text=UI_TEXT[lang]['select_db'])
        self.run_button.config(text=UI_TEXT[lang]['run_analysis'])
        self.results_label.master.config(text=UI_TEXT[lang]['analysis_results'])  
    def setData(self, appKey, updateTree):
        pass
