from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QGridLayout, QPushButton, QLineEdit, QProgressBar
)
from PyQt6.QtCore import Qt
from pathlib import Path
import threading
from typing import Callable

from .base_tab import BaseTab
from ..core import FileProcessor, generate_report

class BatchTab(BaseTab):
    """批量处理选项卡"""
    
    def __init__(self, parent: QWidget, message_callback: Callable):
        self.message_callback = message_callback
        self.input_dir_line_edit = QLineEdit()
        self.output_dir_line_edit = QLineEdit()
        self.progress_label = None
        self.progressbar = None
        self.start_button = None
        super().__init__(parent)
        
    def setup_ui(self):
        """设置UI组件"""
        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 主框架
        main_frame = QFrame()
        main_layout.addWidget(main_frame)
        frame_layout = QVBoxLayout(main_frame)
        
        # 输入目录选择
        self.create_directory_selector(
            main_frame,
            "输入目录:",
            self.input_dir_line_edit,
            lambda: self.browse_directory("选择输入目录", self.input_dir_line_edit)
        )
        
        # 输出目录选择
        self.create_directory_selector(
            main_frame,
            "输出目录:",
            self.output_dir_line_edit,
            lambda: self.browse_directory("选择输出目录", self.output_dir_line_edit)
        )
        
        # 进度显示框架
        progress_frame = QFrame()
        frame_layout.addWidget(progress_frame)
        progress_layout = QVBoxLayout(progress_frame)
        
        # 进度显示
        self.progress_label = QLabel("准备就绪")
        self.progress_label.setMinimumHeight(30)  # 增加高度以便于点击
        progress_layout.addWidget(self.progress_label)
        
        # 进度条
        self.progressbar = QProgressBar()
        self.progressbar.setMinimum(0)
        self.progressbar.setMaximum(100)
        self.progressbar.setValue(0)
        progress_layout.addWidget(self.progressbar)
        
        # 按钮框架
        button_frame = QFrame()
        frame_layout.addWidget(button_frame)
        button_layout = QHBoxLayout(button_frame)
        button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 开始按钮
        self.start_button = QPushButton("开始处理")
        self.start_button.setMinimumHeight(40)  # 增加按钮高度
        self.start_button.setMinimumWidth(200)  # 增加按钮宽度
        self.start_button.clicked.connect(self.start_processing)
        button_layout.addWidget(self.start_button)
        
        # 设置主布局
        if hasattr(self.parent, 'layout') and callable(self.parent.layout):
            if self.parent.layout() is not None:
                existing_layout = self.parent.layout()
                existing_layout.addLayout(main_layout)
            else:
                self.parent.setLayout(main_layout)
        
    def update_progress(self, progress: float, message: str):
        """更新进度信息"""
        self.progress_label.setText(message)
        self.progressbar.setValue(int(progress * 100))
        self.message_callback(message)
        
    def process_directory_safe(self):
        """安全地处理目录"""
        try:
            self.message_callback("开始处理文件...")
            self.update_progress(0.0, "开始处理...")
            
            processor = FileProcessor()
            result = processor.process_directory(
                Path(self.input_dir_line_edit.text()),
                Path(self.output_dir_line_edit.text()),
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
            self.start_button.setEnabled(True)
            # 重置进度条状态
            self.progressbar.setValue(0)
            self.progress_label.setText("准备就绪")
            
    def start_processing(self):
        """开始处理文件"""
        if not self.input_dir_line_edit.text():
            self.show_error("错误", "请选择输入目录")
            return
            
        if not self.output_dir_line_edit.text():
            self.show_error("错误", "请选择输出目录")
            return
            
        # 禁用开始按钮
        self.start_button.setEnabled(False)
        
        # 在新线程中处理文件
        thread = threading.Thread(target=self.process_directory_safe)
        thread.daemon = True
        thread.start() 