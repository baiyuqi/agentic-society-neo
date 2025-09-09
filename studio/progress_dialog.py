import tkinter as tk
from tkinter import ttk
import threading
import time

class ProgressDialog:
    """进度显示对话框"""
    
    def __init__(self, parent, title="处理中...", message="正在处理，请稍候..."):
        self.parent = parent
        self.title = title
        self.message = message
        self.dialog = None
        self.progress_var = None
        self.progress_bar = None
        self.message_label = None
        self.cancel_requested = False
        
    def show(self):
        """显示进度对话框"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title(self.title)
        self.dialog.geometry("400x150")
        self.dialog.resizable(False, False)
        
        # 设置对话框居中
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # 计算居中位置
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (150 // 2)
        self.dialog.geometry(f"400x150+{x}+{y}")
        
        # 创建内容框架
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 消息标签
        self.message_label = ttk.Label(main_frame, text=self.message, font=("Helvetica", 11))
        self.message_label.pack(pady=(0, 15))
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            main_frame, 
            variable=self.progress_var,
            mode='indeterminate',
            length=350
        )
        self.progress_bar.pack(pady=(0, 15))
        
        # 取消按钮
        cancel_button = ttk.Button(main_frame, text="取消", command=self.cancel)
        cancel_button.pack()
        
        # 开始进度条动画
        self.progress_bar.start(10)
        
        # 防止对话框被关闭
        self.dialog.protocol("WM_DELETE_WINDOW", self.cancel)
        
    def update_message(self, message):
        """更新显示消息 (线程安全)"""
        def _task():
            if self.message_label:
                self.message_label.config(text=message)
        
        if self.dialog:
            self.dialog.after(0, _task)
    
    def set_progress(self, value):
        """设置进度值（0-100）(线程安全)"""
        def _task():
            if self.progress_bar:
                self.progress_bar.config(mode='determinate')
                self.progress_var.set(value)

        if self.dialog:
            self.dialog.after(0, _task)
    
    def cancel(self):
        """取消操作"""
        self.cancel_requested = True
        self.close()
    
    def close(self):
        """关闭进度对话框"""
        if self.dialog:
            self.dialog.grab_release()
            self.dialog.destroy()
            self.dialog = None
    
    def is_cancelled(self):
        """检查是否被取消"""
        return self.cancel_requested


class ProgressManager:
    """进度管理器，用于在后台线程中执行任务并显示进度"""
    
    def __init__(self, parent):
        self.parent = parent
        self.progress_dialog = None
        
    def run_with_progress(self, task_func, title="处理中...", message="正在处理，请稍候...", 
                         success_callback=None, error_callback=None):
        """
        在后台线程中运行任务并显示进度
        
        Args:
            task_func: 要执行的任务函数
            title: 进度对话框标题
            message: 进度对话框消息
            success_callback: 成功回调函数，接收任务结果
            error_callback: 错误回调函数，接收异常对象
        """
        self.progress_dialog = ProgressDialog(self.parent, title, message)
        self.progress_dialog.show()
        
        def worker():
            try:
                # 执行任务
                result = task_func(self.progress_dialog)
                
                # 在主线程中处理结果
                if not self.progress_dialog.is_cancelled():
                    self.parent.after(0, lambda: self._handle_success(result, success_callback))
                    
            except Exception as e:
                # 在主线程中处理错误
                if not self.progress_dialog.is_cancelled():
                    self.parent.after(0, lambda err=e: self._handle_error(err, error_callback))
        
        # 启动后台线程
        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
    
    def _handle_success(self, result, callback):
        """处理成功结果"""
        self.progress_dialog.close()
        if callback:
            callback(result)
    
    def _handle_error(self, error, callback):
        """处理错误"""
        self.progress_dialog.close()
        if callback:
            callback(error)
        else:
            # 默认错误处理，直接在控制台打印更详细的错误信息
            import traceback
            traceback.print_exc()
            from tkinter import messagebox
            messagebox.showerror("错误", f"处理过程中发生错误 (详情请查看控制台)：\n{str(error)}")


# 装饰器版本，用于简化使用
def with_progress(title="处理中...", message="正在处理，请稍候..."):
    """
    装饰器，为函数添加进度显示
    
    使用方法：
    @with_progress("分析中...", "正在进行聚类分析...")
    def my_analysis_function(self, progress_dialog=None):
        # 分析代码
        if progress_dialog:
            progress_dialog.update_message("正在加载数据...")
        # ...
        if progress_dialog and progress_dialog.is_cancelled():
            return None
        # ...
        return result
    """
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            if not hasattr(self, '_progress_manager'):
                self._progress_manager = ProgressManager(self.root if hasattr(self, 'root') else self.parent)
            
            def task(progress_dialog):
                return func(self, progress_dialog=progress_dialog, *args, **kwargs)
            
            def success_callback(result):
                # 可以在这里添加成功后的通用处理
                pass
            
            self._progress_manager.run_with_progress(
                task, title, message, success_callback
            )
        
        return wrapper
    return decorator
