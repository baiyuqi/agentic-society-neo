import tkinter as tk
from tkinter import ttk, messagebox, filedialog, font
import json
import os
from studio.llm_test_panel import LLMTestPanel

# Correctly determine the project's root directory
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(ROOT_DIR, 'config.json')
PROMPTS_DIR = os.path.join(ROOT_DIR, 'prompts')

class ConfigPanel(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Configuration")
        self.geometry("600x400")
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
        
        self.config_vars = {}
        
        # Load data for widgets
        self.load_prompt_data()
        self.supported_llms = ['deepseek', 'gpt-4o', 'local', 'qwen']
        
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(padx=20, pady=15, fill='both', expand=True)
        
        self.load_config()
        self.create_widgets()
        
    def load_config(self):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                self.config_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            messagebox.showerror("Error", f"Could not load config.json: {e}")
            self.config_data = {}

    def load_prompt_data(self):
        try:
            with open(os.path.join(PROMPTS_DIR, 'experiment.json'), 'r', encoding='utf-8') as f:
                self.experiment_prompts = list(json.load(f).values())[0]
            with open(os.path.join(PROMPTS_DIR, 'generation.json'), 'r', encoding='utf-8') as f:
                self.generation_prompts = json.load(f)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load prompt files: {e}")
            self.experiment_prompts = {}
            self.generation_prompts = {}

    def create_widgets(self):
        num_items = len(self.config_data)
        for i, (key, value) in enumerate(self.config_data.items()):
            label = ttk.Label(self.main_frame, text=f"{key}:")
            label.grid(row=i, column=0, sticky='ne', pady=6, padx=10)
            
            var = tk.StringVar(value=value)
            self.config_vars[key] = var

            if key == 'llm':
                frame = ttk.Frame(self.main_frame)
                combo = ttk.Combobox(frame, textvariable=var, values=self.supported_llms, state='readonly')
                combo.pack(side='left', fill='x', expand=True)
                button = ttk.Button(frame, text="Test...", command=self.open_llm_test_panel)
                button.pack(side='left', padx=(5,0))
                widget = frame
            elif key == 'database':
                frame = ttk.Frame(self.main_frame)
                entry = ttk.Entry(frame, textvariable=var)
                entry.pack(side='left', fill='x', expand=True)
                button = ttk.Button(frame, text="Browse...", command=self.browse_db_file)
                button.pack(side='left', padx=(5,0))
                widget = frame
            elif key == 'request_method':
                widget = ttk.Combobox(self.main_frame, textvariable=var, values=['question', 'sheet'], state='readonly')
                widget.bind('<<ComboboxSelected>>', self.update_question_prompts)
            elif key == 'question_prompt':
                self.question_prompt_combo = ttk.Combobox(self.main_frame, textvariable=var, state='readonly')
                widget = self.question_prompt_combo
            elif key == 'persona_prompt':
                widget = ttk.Combobox(self.main_frame, textvariable=var, values=list(self.generation_prompts.keys()), state='readonly')
            else:
                widget = ttk.Entry(self.main_frame, textvariable=var)
            
            widget.grid(row=i, column=1, sticky='ew', pady=6, padx=10)

        self.main_frame.rowconfigure(num_items, weight=1)
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
        selected_llm = self.config_vars['llm'].get()
        if not selected_llm:
            messagebox.showwarning("No LLM Selected", "Please select an LLM from the dropdown first.", parent=self)
            return
        
        test_panel = LLMTestPanel(self, model_name=selected_llm)
        test_panel.grab_set()

    def browse_db_file(self):
        db_dir = os.path.join(ROOT_DIR, 'data', 'db')
        filepath = filedialog.askopenfilename(
            title="Select Database File",
            initialdir=db_dir,
            filetypes=(("Database files", "*.db"), ("All files", "*.*"))
        )
        if filepath:
            rel_path = os.path.relpath(filepath, ROOT_DIR).replace('\\', '/')
            self.config_vars['database'].set(rel_path)

    def update_question_prompts(self, event=None):
        method = self.config_vars.get('request_method').get()
        if not method: return
        
        prompt_prefix = 'question_' if method == 'question' else 'sheet_'
        options = [p for p in self.experiment_prompts.keys() if p.startswith(prompt_prefix)]
        self.question_prompt_combo['values'] = options
        
        if self.config_vars['question_prompt'].get() not in options:
            self.config_vars['question_prompt'].set(options[0] if options else '')

    def save_config(self):
        for key, var in self.config_vars.items():
            self.config_data[key] = var.get()
            
        try:
            with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, indent=4)
            messagebox.showinfo("Success", "Configuration saved successfully.")
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
