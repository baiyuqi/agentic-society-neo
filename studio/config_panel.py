import tkinter as tk
from tkinter import ttk, messagebox, filedialog, font
import json
import os

from asociety import config
from asociety.config import instrument_spec, match_instrument_tree
from asociety.repository.database import set_currentdb, create_tables
from asociety.repository.meta_rep import META_KEYS, set_meta
from studio.llm_test_panel import LLMTestPanel

# Correctly determine the project's root directory
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROMPTS_DIR = os.path.join(ROOT_DIR, 'prompts')
DB_ROOT = os.path.join(ROOT_DIR, 'data', 'db')


class ConfigPanel(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Configuration")
        self.geometry("640x480")
        self.parent = parent

        # --- Style and Font Configuration ---
        self.default_font = font.nametofont("TkDefaultFont")
        self.default_font.configure(family="Helvetica", size=11)

        style = ttk.Style(self)
        style.configure('TLabel', font=self.default_font)
        style.configure('TButton', font=self.default_font)
        style.configure('TEntry', font=self.default_font)
        style.configure('TCombobox', font=self.default_font)
        # --- End Style ---

        self.vars = {}
        self.instrument = None

        self.supported_llms = ['deepseek', 'gpt-4o', 'local', 'qwen']

        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(padx=20, pady=15, fill='both', expand=True)

        self.load_prompt_data()
        self.create_widgets()

    def load_prompt_data(self):
        try:
            with open(os.path.join(PROMPTS_DIR, 'experiment.json'), encoding='utf-8') as f:
                # {instrument: {prompt_name: text}} -- e.g. ipip_neo_120, pvq_21, mfq_30
                self.instrument_prompts = json.load(f)
            with open(os.path.join(PROMPTS_DIR, 'generation.json'), encoding='utf-8') as f:
                self.generation_prompts = json.load(f)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load prompt files: {e}")
            self.instrument_prompts = {}
            self.generation_prompts = {}

        self.experiment_prompts = next(iter(self.instrument_prompts.values()), {})

    def select_instrument(self, instrument):
        """Pick the prompt group for `instrument`, falling back to the first group."""
        if instrument in self.instrument_prompts:
            self.experiment_prompts = self.instrument_prompts[instrument]
        else:
            self.experiment_prompts = next(iter(self.instrument_prompts.values()), {})

    def create_widgets(self):
        row = 0

        # database selector
        label = ttk.Label(self.main_frame, text="database:")
        label.grid(row=row, column=0, sticky='ne', pady=6, padx=10)
        frame = ttk.Frame(self.main_frame)
        self.vars['database'] = tk.StringVar()
        entry = ttk.Entry(frame, textvariable=self.vars['database'])
        entry.pack(side='left', fill='x', expand=True)
        button = ttk.Button(frame, text="Browse...", command=self.browse_db_file)
        button.pack(side='left', padx=(5, 0))
        frame.grid(row=row, column=1, sticky='ew', pady=6, padx=10)
        row += 1

        # instrument is derived from the DB, so it is shown read-only
        label = ttk.Label(self.main_frame, text="instrument:")
        label.grid(row=row, column=0, sticky='ne', pady=6, padx=10)
        self.vars['instrument'] = tk.StringVar()
        widget = ttk.Entry(self.main_frame, textvariable=self.vars['instrument'], state='readonly')
        widget.grid(row=row, column=1, sticky='ew', pady=6, padx=10)
        row += 1

        # llm
        label = ttk.Label(self.main_frame, text="llm:")
        label.grid(row=row, column=0, sticky='ne', pady=6, padx=10)
        frame = ttk.Frame(self.main_frame)
        self.vars['llm'] = tk.StringVar()
        combo = ttk.Combobox(frame, textvariable=self.vars['llm'], values=self.supported_llms,
                             state='readonly')
        combo.pack(side='left', fill='x', expand=True)
        button = ttk.Button(frame, text="Test...", command=self.open_llm_test_panel)
        button.pack(side='left', padx=(5, 0))
        frame.grid(row=row, column=1, sticky='ew', pady=6, padx=10)
        row += 1

        # request_method
        label = ttk.Label(self.main_frame, text="request_method:")
        label.grid(row=row, column=0, sticky='ne', pady=6, padx=10)
        self.vars['request_method'] = tk.StringVar()
        widget = ttk.Combobox(self.main_frame, textvariable=self.vars['request_method'],
                              values=['question', 'sheet'], state='readonly')
        widget.bind('<<ComboboxSelected>>', self.update_question_prompts)
        widget.grid(row=row, column=1, sticky='ew', pady=6, padx=10)
        row += 1

        # question_prompt
        label = ttk.Label(self.main_frame, text="question_prompt:")
        label.grid(row=row, column=0, sticky='ne', pady=6, padx=10)
        self.vars['question_prompt'] = tk.StringVar()
        self.question_prompt_combo = ttk.Combobox(self.main_frame,
                                                  textvariable=self.vars['question_prompt'],
                                                  state='readonly')
        self.question_prompt_combo.grid(row=row, column=1, sticky='ew', pady=6, padx=10)
        row += 1

        # persona_prompt
        label = ttk.Label(self.main_frame, text="persona_prompt:")
        label.grid(row=row, column=0, sticky='ne', pady=6, padx=10)
        self.vars['persona_prompt'] = tk.StringVar()
        widget = ttk.Combobox(self.main_frame, textvariable=self.vars['persona_prompt'],
                              values=list(self.generation_prompts.keys()), state='readonly')
        widget.grid(row=row, column=1, sticky='ew', pady=6, padx=10)
        row += 1

        # model
        label = ttk.Label(self.main_frame, text="model:")
        label.grid(row=row, column=0, sticky='ne', pady=6, padx=10)
        self.vars['model'] = tk.StringVar()
        widget = ttk.Entry(self.main_frame, textvariable=self.vars['model'])
        widget.grid(row=row, column=1, sticky='ew', pady=6, padx=10)
        row += 1

        self.main_frame.rowconfigure(row, weight=1)
        self.main_frame.columnconfigure(1, weight=3)
        self.main_frame.columnconfigure(0, weight=1)

        self.update_question_prompts()

        button_frame = ttk.Frame(self)
        button_frame.pack(side='bottom', fill='x', padx=20, pady=(0, 20))

        spacer = ttk.Frame(button_frame)
        spacer.pack(side='left', expand=True)

        save_button = ttk.Button(button_frame, text="Save", command=self.save_config)
        save_button.pack(side='left', padx=5)

        cancel_button = ttk.Button(button_frame, text="Cancel", command=self.destroy)
        cancel_button.pack(side='left')

    def open_llm_test_panel(self):
        selected_llm = self.vars['llm'].get()
        if not selected_llm:
            messagebox.showwarning("No LLM Selected", "Please select an LLM from the dropdown first.",
                                   parent=self)
            return

        test_panel = LLMTestPanel(self, model_name=selected_llm)
        test_panel.grab_set()

    def load_db(self, db_path):
        """Point the panel at `db_path`: derive instrument and load its meta into the editors."""
        config.load_from_db(db_path)
        self.instrument = config.configuration['instrument']
        self.select_instrument(self.instrument)

        self.vars['database'].set(db_path)
        self.vars['instrument'].set(self.instrument or '')
        for key in META_KEYS:
            self.vars[key].set(config.configuration.get(key) or '')
        self.update_question_prompts()

    def _instrument_tree(self):
        """The database subtree the current instrument's items live in."""
        if not self.instrument:
            return None
        return instrument_spec(self.instrument)['tree']

    def _check_database_tree(self):
        """Whether the picked database sits in the derived instrument's tree.

        The pipeline rejects a mismatch up front (config.verify_db_path), so the panel must not let
        one be saved. An empty database is allowed: pointing the panel at a DB that does not exist
        yet is how a new run starts.
        """
        instrument = self.instrument
        database = self.vars['database'].get()
        if not database:
            return True
        if not instrument:
            messagebox.showerror(
                "Unknown instrument",
                f"Could not derive an instrument from {database}. Pick a DB under "
                f"data/db/personality/, data/db/value/, or data/db/morality/.",
                parent=self)
            return False
        if match_instrument_tree(instrument, database):
            return True
        messagebox.showerror(
            "Wrong instrument tree",
            f"database is {database}\n"
            f"but the '{instrument}' instrument lives under {self._instrument_tree()}.\n\n"
            f"Pick a database under {self._instrument_tree()}, or a DB whose question count "
            f"matches a different instrument.",
            parent=self)
        return False

    def browse_db_file(self):
        filepath = filedialog.askopenfilename(
            title="Select Database File",
            initialdir=DB_ROOT,
            filetypes=(("Database files", "*.db"), ("All files", "*.*"))
        )
        if not filepath:
            return
        rel = os.path.relpath(filepath, ROOT_DIR).replace('\\', '/')
        self.load_db(rel)

    def update_question_prompts(self, event=None):
        method = self.vars.get('request_method').get() if 'request_method' in self.vars else None
        if not method:
            return

        prompt_prefix = 'question_' if method == 'question' else 'sheet_'
        options = [p for p in self.experiment_prompts.keys() if p.startswith(prompt_prefix)]
        self.question_prompt_combo['values'] = options

        if self.vars['question_prompt'].get() not in options:
            self.vars['question_prompt'].set(options[0] if options else '')

    def save_config(self):
        db_path = self.vars['database'].get()
        if not db_path:
            messagebox.showerror("Error", "Pick a database first.", parent=self)
            return
        if not self._check_database_tree():
            return

        items = {key: self.vars[key].get() for key in META_KEYS}
        try:
            set_currentdb(db_path)
            create_tables()
            set_meta(items)
            messagebox.showinfo("Success", "Configuration saved to the database's meta table.")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    app = ConfigPanel(root)

    def _shutdown():
        root.quit()
        root.destroy()

    app.protocol("WM_DELETE_WINDOW", _shutdown)
    root.mainloop()
