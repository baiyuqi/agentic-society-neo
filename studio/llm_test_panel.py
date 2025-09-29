
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import os
import threading
from queue import Queue

# This file duplicates the LLM creation logic from llm_engine.py
# to avoid modifying it, as requested.
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

class LLMTestPanel(tk.Toplevel):
    def __init__(self, parent, model_name: str):
        super().__init__(parent)
        self.title(f"LLM Test: {model_name}")
        self.geometry("700x500")
        self.model_name = model_name
        self.llm = None
        self.response_queue = Queue()

        # --- UI Elements ---
        main_frame = ttk.Frame(self)
        main_frame.pack(padx=15, pady=15, fill='both', expand=True)

        # Input Area
        input_label = ttk.Label(main_frame, text="Input Prompt:")
        input_label.pack(anchor='w')
        self.input_text = scrolledtext.ScrolledText(main_frame, height=8, wrap=tk.WORD)
        self.input_text.pack(fill='x', expand=True, pady=(5, 10))
        self.input_text.insert('1.0', "Hello, who are you?")

        # Send Button
        self.send_button = ttk.Button(main_frame, text="Send to LLM", command=self.send_request_threaded)
        self.send_button.pack(pady=5)

        # Output Area
        output_label = ttk.Label(main_frame, text="LLM Response:")
        output_label.pack(anchor='w', pady=(10, 0))
        self.output_text = scrolledtext.ScrolledText(main_frame, height=12, wrap=tk.WORD, state='disabled')
        self.output_text.pack(fill='both', expand=True, pady=5)
        
        # --- Initialization ---
        self.initialize_llm()
        self.after(100, self.process_queue)

    def initialize_llm(self):
        try:
            if self.model_name == 'local':
                self.llm = ChatOpenAI(model="/data1/glm-4-9b-chat", api_key="aaa", openai_api_base="http://221.229.101.198:8000/v1")
            elif self.model_name == 'gpt-4o':
                apikey = os.getenv('OPENAI_APIKEY')
                if not apikey: raise ValueError("OPENAI_APIKEY environment variable not set.")
                self.llm = ChatOpenAI(model="glm4-chat-9b", openai_api_base="", api_key=apikey)
            elif self.model_name == 'deepseek':
                apikey = os.getenv('DS_API_KEY')
                api_base = os.getenv('DS_BASE_URL')
                if not apikey or not api_base: raise ValueError("DS_API_KEY or DS_BASE_URL not set.")
                self.llm = ChatOpenAI(model="deepseek-chat", openai_api_base=api_base, api_key=apikey)
            elif self.model_name == 'qwen':
                apikey = os.getenv('QW_API_KEY')
                api_base = os.getenv('QW_BASE_URL')
                if not apikey or not api_base: raise ValueError("QW_API_KEY or QW_BASE_URL not set.")
                self.llm = ChatOpenAI(model="qwen-vl-plus", openai_api_base=api_base, api_key=apikey)
            else:
                raise ValueError(f"Unsupported model for testing: {self.model_name}")
        except Exception as e:
            messagebox.showerror("LLM Initialization Error", str(e), parent=self)
            self.send_button.config(state='disabled')

    def send_request_threaded(self):
        if not self.llm:
            messagebox.showwarning("Warning", "LLM is not initialized.", parent=self)
            return
        
        prompt = self.input_text.get("1.0", tk.END).strip()
        if not prompt:
            messagebox.showwarning("Warning", "Input prompt cannot be empty.", parent=self)
            return

        self.send_button.config(state='disabled')
        self.output_text.config(state='normal')
        self.output_text.delete('1.0', tk.END)
        self.output_text.insert('1.0', "Waiting for response...")
        self.output_text.config(state='disabled')

        thread = threading.Thread(target=self.invoke_llm, args=(prompt,))
        thread.daemon = True
        thread.start()

    def invoke_llm(self, prompt):
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            self.response_queue.put(response.content)
        except Exception as e:
            self.response_queue.put(f"Error: {str(e)}")

    def process_queue(self):
        try:
            message = self.response_queue.get_nowait()
            self.output_text.config(state='normal')
            self.output_text.delete('1.0', tk.END)
            self.output_text.insert('1.0', message)
            self.output_text.config(state='disabled')
            self.send_button.config(state='normal')
        except Exception:
            pass
        self.after(100, self.process_queue)

if __name__ == '__main__':
    # Example of how to run this panel for testing
    root = tk.Tk()
    root.withdraw()
    
    # You can change this model name to test different LLMs
    test_model = 'deepseek' 
    
    app = LLMTestPanel(root, model_name=test_model)
    app.protocol("WM_DELETE_WINDOW", root.destroy)
    root.mainloop()
