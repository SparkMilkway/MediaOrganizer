import customtkinter as ctk
from datetime import datetime
from pathlib import Path
import threading
from typing import Callable, List
from tkinter import filedialog

from .base_tab import BaseTab
from ..core import FileProcessor

class ManualTab(BaseTab):
    """手动处理选项卡"""
    
    def __init__(self, parent: ctk.CTkFrame, message_callback: Callable):
        self.message_callback = message_callback
        self.manual_files: List[str] = []
        self.manual_output_dir_var = ctk.StringVar()
        self.selected_files_var = ctk.StringVar(value="未选择文件")
        
        # 日期时间变量
        self.year_var = ctk.StringVar(value=str(datetime.now().year))
        self.month_var = ctk.StringVar(value=str(datetime.now().month))
        self.day_var = ctk.StringVar(value=str(datetime.now().day))
        self.hour_var = ctk.StringVar(value="12")
        self.minute_var = ctk.StringVar(value="00")
        
        super().__init__(parent)
        
    def setup_ui(self):
        """设置UI组件"""
        # 文件选择框架
        file_frame = ctk.CTkFrame(self.parent)
        file_frame.grid(row=0, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
        
        # 选择文件按钮
        ctk.CTkLabel(file_frame, text="选择需要手动处理的文件:").grid(
            row=0, column=0, padx=5, pady=5, sticky="w"
        )
        ctk.CTkButton(file_frame, text="浏览文件", command=self.browse_files).grid(
            row=0, column=1, padx=5, pady=5
        )
        
        # 显示选择的文件
        self.selected_files_label = ctk.CTkLabel(
            file_frame, 
            textvariable=self.selected_files_var,
            wraplength=600
        )
        self.selected_files_label.grid(
            row=1, column=0, columnspan=2, padx=5, pady=5, sticky="w"
        )
        
        # 日期选择框架
        date_frame = ctk.CTkFrame(self.parent)
        date_frame.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
        
        # 日期选择标题
        ctk.CTkLabel(date_frame, text="设置照片拍摄日期:").grid(
            row=0, column=0, padx=5, pady=5, sticky="w"
        )
        
        # 日期输入框架
        date_input_frame = ctk.CTkFrame(date_frame)
        date_input_frame.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        
        # 年月日时分输入
        self.create_date_time_inputs(date_input_frame)
        
        # 输出目录选择
        output_frame = ctk.CTkFrame(self.parent)
        output_frame.grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
        
        self.create_directory_selector(
            output_frame,
            "处理后的文件保存到:",
            self.manual_output_dir_var,
            lambda: self.browse_directory("选择输出目录", self.manual_output_dir_var),
            row=0
        )
        
        # 处理按钮
        self.process_button = ctk.CTkButton(
            self.parent,
            text="处理选定的文件",
            command=self.process_files,
            height=40
        )
        self.process_button.grid(row=3, column=0, columnspan=3, padx=5, pady=20, sticky="ew")
        
    def create_date_time_inputs(self, frame: ctk.CTkFrame):
        """创建日期时间输入组件"""
        # 年选择
        ctk.CTkLabel(frame, text="年:").grid(row=0, column=0, padx=5, pady=5)
        year_entry = ctk.CTkEntry(frame, textvariable=self.year_var, width=60)
        year_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # 月选择
        ctk.CTkLabel(frame, text="月:").grid(row=0, column=2, padx=5, pady=5)
        month_entry = ctk.CTkEntry(frame, textvariable=self.month_var, width=40)
        month_entry.grid(row=0, column=3, padx=5, pady=5)
        
        # 日选择
        ctk.CTkLabel(frame, text="日:").grid(row=0, column=4, padx=5, pady=5)
        day_entry = ctk.CTkEntry(frame, textvariable=self.day_var, width=40)
        day_entry.grid(row=0, column=5, padx=5, pady=5)
        
        # 时间选择
        ctk.CTkLabel(frame, text="时:").grid(row=0, column=6, padx=5, pady=5)
        hour_entry = ctk.CTkEntry(frame, textvariable=self.hour_var, width=40)
        hour_entry.grid(row=0, column=7, padx=5, pady=5)
        
        ctk.CTkLabel(frame, text="分:").grid(row=0, column=8, padx=5, pady=5)
        minute_entry = ctk.CTkEntry(frame, textvariable=self.minute_var, width=40)
        minute_entry.grid(row=0, column=9, padx=5, pady=5)
        
    def browse_files(self):
        """浏览并选择需要手动处理的文件"""
        files = filedialog.askopenfilenames(
            title="选择需要手动处理的照片/视频",
            filetypes=[
                ("图片文件", "*.jpg *.jpeg *.png *.heic *.heif"),
                ("视频文件", "*.mp4 *.mov *.MOV"),
                ("所有文件", "*.*")
            ]
        )
        
        if files:
            self.manual_files = list(files)
            if len(files) <= 3:
                file_names = ", ".join([Path(f).name for f in files])
            else:
                file_names = ", ".join([Path(f).name for f in files[:3]]) + f"...等 {len(files)} 个文件"
            
            self.selected_files_var.set(f"已选择: {file_names}")
            self.message_callback(f"已选择 {len(files)} 个文件进行手动处理")
            
            # 如果没有设置输出目录，则使用第一个文件的目录作为默认输出目录
            if not self.manual_output_dir_var.get() and files:
                default_output = str(Path(files[0]).parent)
                self.manual_output_dir_var.set(default_output)
                
    def process_files(self):
        """处理手动选择的文件"""
        if not self.manual_files:
            self.show_error("错误", "请先选择需要处理的文件")
            return
            
        if not self.manual_output_dir_var.get():
            self.show_error("错误", "请选择输出目录")
            return
            
        # 获取用户设置的日期
        try:
            year = int(self.year_var.get())
            month = int(self.month_var.get())
            day = int(self.day_var.get())
            hour = int(self.hour_var.get())
            minute = int(self.minute_var.get())
            
            user_date = datetime(year, month, day, hour, minute)
        except ValueError as e:
            self.show_error("错误", f"日期格式无效: {str(e)}")
            return
            
        # 禁用处理按钮
        self.process_button.configure(state="disabled")
        
        # 在新线程中处理文件
        thread = threading.Thread(
            target=self.process_files_thread,
            args=(user_date,)
        )
        thread.daemon = True
        thread.start()
        
    def process_files_thread(self, user_date: datetime):
        """在线程中处理手动选择的文件"""
        try:
            self.message_callback("开始处理手动选择的文件...")
            
            processor = FileProcessor()
            output_path = Path(self.manual_output_dir_var.get())
            
            processed_count = 0
            success_count = 0
            total_files = len(self.manual_files)
            
            for file_path in self.manual_files:
                if processor.process_file(Path(file_path), output_path, user_date):
                    success_count += 1
                processed_count += 1
                
                self.message_callback(
                    f"已处理文件 {Path(file_path).name} ({processed_count}/{total_files})"
                )
                
            self.message_callback(f"所有手动选择的文件处理完成！共处理 {processed_count} 个文件")
            
            # 显示完成提示
            self.show_info("处理完成",
                f"手动选择的文件处理完成！\n\n"
                f"已将 {processed_count} 个文件处理为日期: "
                f"{user_date.year}-{user_date.month:02d}-{user_date.day:02d} "
                f"{user_date.hour:02d}:{user_date.minute:02d}")
                
        except Exception as e:
            error_msg = f"处理文件时出错: {str(e)}"
            self.message_callback(error_msg)
            self.show_error("错误", error_msg)
            
        finally:
            # 启用处理按钮
            self.process_button.configure(state="normal") 