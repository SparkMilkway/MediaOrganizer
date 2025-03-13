import customtkinter as ctk
from typing import Optional, Callable
from pathlib import Path
import logging

class BaseTab:
    """选项卡基类，提供共同的功能"""
    
    def __init__(self, parent: ctk.CTkFrame):
        self.parent = parent
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI组件，子类必须实现"""
        raise NotImplementedError
        
    def browse_directory(self, title: str, var: ctk.StringVar) -> Optional[str]:
        """通用的目录选择对话框"""
        directory = ctk.filedialog.askdirectory(title=title)
        if directory:
            var.set(directory)
            return directory
        return None
        
    def update_progress(self, progress: float, message: str):
        """更新进度信息，子类可以重写"""
        pass
        
    def log_message(self, message: str):
        """记录日志信息"""
        logging.info(message)
        
    def show_error(self, title: str, message: str):
        """显示错误对话框"""
        ctk.messagebox.showerror(title, message)
        
    def show_info(self, title: str, message: str):
        """显示信息对话框"""
        ctk.messagebox.showinfo(title, message)
        
    def confirm(self, title: str, message: str) -> bool:
        """显示确认对话框"""
        return ctk.messagebox.askyesno(title, message)
        
    def create_directory_selector(self, frame: ctk.CTkFrame, 
                                label_text: str,
                                var: ctk.StringVar,
                                browse_command: Callable,
                                row: int = 0) -> None:
        """创建通用的目录选择组件"""
        # 创建子框架
        selector_frame = ctk.CTkFrame(frame)
        selector_frame.grid(row=row, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
        selector_frame.grid_columnconfigure(1, weight=1)
        
        # 标签
        ctk.CTkLabel(
            selector_frame, 
            text=label_text,
            height=30  # 增加高度以便于点击
        ).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        # 输入框
        entry = ctk.CTkEntry(
            selector_frame, 
            textvariable=var,
            height=32  # 增加高度以便于点击
        )
        entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # 浏览按钮
        browse_button = ctk.CTkButton(
            selector_frame, 
            text="浏览",
            command=browse_command,
            height=32,  # 增加高度以便于点击
            width=100   # 增加按钮宽度
        )
        browse_button.grid(row=0, column=2, padx=5, pady=5) 