from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QGridLayout, QPushButton, QLineEdit, QFileDialog,
    QListWidget, QListWidgetItem, QSpinBox, QGroupBox, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer
from datetime import datetime
from pathlib import Path
import threading
from typing import Callable, List

from .base_tab import BaseTab

class ManualTab(BaseTab):
    """手动处理选项卡"""
    
    def __init__(self, parent: QWidget, message_callback: Callable):
        self.message_callback = message_callback
        self.selected_files = []
        self.output_dir_line_edit = QLineEdit()
        self.file_list = None
        self.year_spinbox = None
        self.month_spinbox = None
        self.day_spinbox = None
        self.hour_spinbox = None
        self.minute_spinbox = None
        self.process_button = None
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
        
        # 文件选择部分
        file_frame = QFrame()
        frame_layout.addWidget(file_frame)
        file_layout = QHBoxLayout(file_frame)
        
        # 浏览文件按钮
        browse_button = QPushButton("浏览文件")
        browse_button.setMinimumHeight(40)
        browse_button.setMinimumWidth(120)
        browse_button.clicked.connect(self.browse_files)
        file_layout.addWidget(browse_button)
        
        # 文件列表
        list_frame = QFrame()
        frame_layout.addWidget(list_frame)
        list_layout = QVBoxLayout(list_frame)
        
        list_label = QLabel("已选择的文件:")
        list_layout.addWidget(list_label)
        
        self.file_list = QListWidget()
        self.file_list.setMinimumHeight(150)
        list_layout.addWidget(self.file_list)
        
        # 日期时间设置
        date_time_frame = QGroupBox("设置日期和时间")
        frame_layout.addWidget(date_time_frame)
        date_time_layout = QVBoxLayout(date_time_frame)
        
        # 创建日期时间输入
        date_time_layout.addWidget(self.create_date_time_inputs())
        
        # 输出目录选择
        self.create_directory_selector(
            main_frame,
            "输出目录:",
            self.output_dir_line_edit,
            lambda: self.browse_directory("选择输出目录", self.output_dir_line_edit)
        )
        
        # 处理按钮
        button_frame = QFrame()
        frame_layout.addWidget(button_frame)
        button_layout = QHBoxLayout(button_frame)
        button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.process_button = QPushButton("处理选定的文件")
        self.process_button.setMinimumHeight(40)
        self.process_button.setMinimumWidth(200)
        self.process_button.clicked.connect(self.process_files)
        button_layout.addWidget(self.process_button)
        
        # 设置主布局
        if hasattr(self.parent, 'layout') and callable(self.parent.layout):
            if self.parent.layout() is not None:
                existing_layout = self.parent.layout()
                existing_layout.addLayout(main_layout)
            else:
                self.parent.setLayout(main_layout)
        
    def create_date_time_inputs(self) -> QWidget:
        """创建日期时间输入控件"""
        date_time_widget = QWidget()
        layout = QGridLayout(date_time_widget)
        
        # 年份
        layout.addWidget(QLabel("年:"), 0, 0)
        self.year_spinbox = QSpinBox()
        self.year_spinbox.setMinimum(1970)
        self.year_spinbox.setMaximum(2100)
        self.year_spinbox.setValue(datetime.now().year)
        self.year_spinbox.setMinimumHeight(32)
        layout.addWidget(self.year_spinbox, 0, 1)
        
        # 月份
        layout.addWidget(QLabel("月:"), 0, 2)
        self.month_spinbox = QSpinBox()
        self.month_spinbox.setMinimum(1)
        self.month_spinbox.setMaximum(12)
        self.month_spinbox.setValue(datetime.now().month)
        self.month_spinbox.setMinimumHeight(32)
        layout.addWidget(self.month_spinbox, 0, 3)
        
        # 日
        layout.addWidget(QLabel("日:"), 0, 4)
        self.day_spinbox = QSpinBox()
        self.day_spinbox.setMinimum(1)
        self.day_spinbox.setMaximum(31)
        self.day_spinbox.setValue(datetime.now().day)
        self.day_spinbox.setMinimumHeight(32)
        layout.addWidget(self.day_spinbox, 0, 5)
        
        # 小时
        layout.addWidget(QLabel("时:"), 1, 0)
        self.hour_spinbox = QSpinBox()
        self.hour_spinbox.setMinimum(0)
        self.hour_spinbox.setMaximum(23)
        self.hour_spinbox.setValue(datetime.now().hour)
        self.hour_spinbox.setMinimumHeight(32)
        layout.addWidget(self.hour_spinbox, 1, 1)
        
        # 分钟
        layout.addWidget(QLabel("分:"), 1, 2)
        self.minute_spinbox = QSpinBox()
        self.minute_spinbox.setMinimum(0)
        self.minute_spinbox.setMaximum(59)
        self.minute_spinbox.setValue(datetime.now().minute)
        self.minute_spinbox.setMinimumHeight(32)
        layout.addWidget(self.minute_spinbox, 1, 3)
        
        return date_time_widget
        
    def browse_files(self):
        """浏览并选择文件"""
        files, _ = QFileDialog.getOpenFileNames(
            self.parent,
            "选择照片或视频文件",
            "",
            "媒体文件 (*.jpg *.jpeg *.png *.heic *.heif *.mp4 *.mov *.MOV)"
        )
        
        if files:
            self.selected_files = files
            self.update_file_list()
            
    def update_file_list(self):
        """更新文件列表显示"""
        self.file_list.clear()
        for file in self.selected_files:
            self.file_list.addItem(QListWidgetItem(Path(file).name))
        
    def process_files(self):
        """处理选定的文件"""
        if not self.selected_files:
            self.show_error("错误", "请先选择文件")
            return
            
        if not self.output_dir_line_edit.text():
            self.show_error("错误", "请选择输出目录")
            return
            
        try:
            # 获取设置的日期时间
            year = self.year_spinbox.value()
            month = self.month_spinbox.value()
            day = self.day_spinbox.value()
            hour = self.hour_spinbox.value()
            minute = self.minute_spinbox.value()
            
            # 创建日期时间对象
            try:
                date_time = datetime(year, month, day, hour, minute)
            except ValueError as e:
                self.show_error("日期错误", f"无效的日期时间: {str(e)}")
                return
                
            # 禁用处理按钮
            self.process_button.setEnabled(False)
            
            # 在新线程中处理文件
            thread = threading.Thread(
                target=self.process_files_thread,
                args=(date_time,)
            )
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            self.show_error("错误", f"处理文件时出错: {str(e)}")
            self.process_button.setEnabled(True)
            
    def process_files_thread(self, date_time: datetime):
        """在线程中处理文件"""
        try:
            from ..core.file_processor import FileProcessor
            
            processor = FileProcessor()
            output_dir = Path(self.output_dir_line_edit.text())
            
            self.message_callback(f"开始处理 {len(self.selected_files)} 个文件...")
            
            for i, file_path in enumerate(self.selected_files):
                try:
                    file_path = Path(file_path)
                    progress = (i + 1) / len(self.selected_files)
                    
                    self.message_callback(f"处理文件 {i+1}/{len(self.selected_files)}: {file_path.name}")
                    
                    # 处理单个文件
                    processor.process_single_file_with_date(
                        file_path,
                        output_dir,
                        date_time
                    )
                    
                except Exception as e:
                    self.message_callback(f"处理文件 {file_path.name} 时出错: {str(e)}")
                    
            self.message_callback("所有文件处理完成!")
            
            # 使用QTimer.singleShot在主线程中显示完成对话框
            files_count = len(self.selected_files)
            QTimer.singleShot(0, lambda: self.show_info("处理完成", f"已完成 {files_count} 个文件的处理。"))
                
        except Exception as e:
            self.message_callback(f"处理过程中发生错误: {str(e)}")
            # 使用QTimer.singleShot在主线程中显示错误对话框
            error_msg = str(e)
            QTimer.singleShot(0, lambda: self.show_error("错误", f"处理过程中发生错误: {error_msg}"))
            
        finally:
            # 使用QTimer.singleShot重新启用处理按钮
            QTimer.singleShot(0, lambda: self.process_button.setEnabled(True)) 