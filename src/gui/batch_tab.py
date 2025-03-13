import customtkinter as ctk
from pathlib import Path
import threading
from typing import Callable
import logging

from .base_tab import BaseTab
from ..core import FileProcessor, generate_report

class BatchTab(BaseTab):
    """批量处理选项卡"""
    
    def __init__(self, parent: ctk.CTkFrame, message_callback: Callable):
        self.message_callback = message_callback
        self.input_dir_var = ctk.StringVar()
        self.output_dir_var = ctk.StringVar()
        self.progress_var = ctk.StringVar(value="准备就绪")
        super().__init__(parent)
        
    def setup_ui(self):
        """设置UI组件"""
        # 配置父框架
        self.parent.grid_columnconfigure(0, weight=1)
        self.parent.grid_rowconfigure(0, weight=1)
        
        # 主框架
        main_frame = ctk.CTkFrame(self.parent)
        main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        main_frame.grid_columnconfigure(1, weight=1)
        
        # 输入目录选择
        self.create_directory_selector(
            main_frame,
            "输入目录:",
            self.input_dir_var,
            lambda: self.browse_directory("选择输入目录", self.input_dir_var),
            row=0
        )
        
        # 输出目录选择
        self.create_directory_selector(
            main_frame,
            "输出目录:",
            self.output_dir_var,
            lambda: self.browse_directory("选择输出目录", self.output_dir_var),
            row=1
        )
        
        # 进度显示框架
        progress_frame = ctk.CTkFrame(main_frame)
        progress_frame.grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
        progress_frame.grid_columnconfigure(0, weight=1)
        
        # 进度显示
        progress_label = ctk.CTkLabel(
            progress_frame, 
            textvariable=self.progress_var,
            height=30  # 增加高度以便于点击
        )
        progress_label.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        # 进度条
        self.progressbar = ctk.CTkProgressBar(progress_frame)
        self.progressbar.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        self.progressbar.set(0)
        
        # 按钮框架
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
        button_frame.grid_columnconfigure(0, weight=1)
        
        # 开始按钮
        self.start_button = ctk.CTkButton(
            button_frame,
            text="开始处理",
            command=self.start_processing,
            height=40,  # 增加按钮高度
            width=200   # 增加按钮宽度
        )
        self.start_button.grid(row=0, column=0, padx=5, pady=20)
        
    def update_progress(self, progress: float, message: str):
        """更新进度信息"""
        self.progress_var.set(message)
        self.progressbar.set(progress)
        self.message_callback(message)
        
    def process_directory_safe(self):
        """安全地处理目录"""
        try:
            self.message_callback("开始处理文件...")
            self.update_progress(0.0, "开始处理...")
            
            processor = FileProcessor()
            result = processor.process_directory(
                Path(self.input_dir_var.get()),
                Path(self.output_dir_var.get()),
                self.update_progress
            )
            
            # 生成报告
            report = generate_report(result['input_stats'], result['output_stats'])
            self.message_callback("=" * 50)
            self.message_callback("处理统计报告：")
            for line in report.split('\n'):
                if line.strip():
                    self.message_callback(line)
            self.message_callback("=" * 50)
            
            # 显示完成对话框
            self.show_info("处理完成", 
                f"所有文件处理完成！\n\n"
                f"已处理 {result['processed']} 个文件，成功 {result['success']} 个。\n"
                f"如需处理新的目录，请选择新的输入/输出目录，然后点击「开始处理」按钮。")
                
        except Exception as e:
            error_msg = f"处理过程中发生错误: {str(e)}"
            self.message_callback(error_msg)
            self.show_error("错误", error_msg)
            
        finally:
            # 重新启用开始按钮
            self.start_button.configure(state="normal")
            # 重置进度条状态
            self.progressbar.set(0)
            self.progress_var.set("准备就绪")
            
    def start_processing(self):
        """开始处理文件"""
        if not self.input_dir_var.get():
            self.show_error("错误", "请选择输入目录")
            return
            
        if not self.output_dir_var.get():
            self.show_error("错误", "请选择输出目录")
            return
            
        # 禁用开始按钮
        self.start_button.configure(state="disabled")
        
        # 在新线程中处理文件
        thread = threading.Thread(target=self.process_directory_safe)
        thread.daemon = True
        thread.start() 