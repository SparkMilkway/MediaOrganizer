from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QGridLayout, QPushButton, QLineEdit, QFileDialog, 
    QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from typing import Optional, Callable, Union
from pathlib import Path
import logging

class BaseTab:
    """选项卡基类，提供共同的功能"""
    
    def __init__(self, parent: QWidget):
        self.parent = parent
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI组件，子类必须实现"""
        raise NotImplementedError
        
    def browse_directory(self, title: str, line_edit: QLineEdit) -> Optional[str]:
        """通用的目录选择对话框"""
        directory = QFileDialog.getExistingDirectory(self.parent, title)
        if directory:
            line_edit.setText(directory)
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
        QMessageBox.critical(self.parent, title, message)
        
    def show_info(self, title: str, message: str):
        """显示信息对话框"""
        QMessageBox.information(self.parent, title, message)
        
    def confirm(self, title: str, message: str) -> bool:
        """显示确认对话框"""
        reply = QMessageBox.question(
            self.parent, 
            title, 
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes
        
    def create_directory_selector(self, frame: QWidget, 
                                label_text: str,
                                line_edit: QLineEdit,
                                browse_command: Callable,
                                row: int = 0) -> QWidget:
        """创建通用的目录选择组件"""
        # 创建子框架
        selector_frame = QFrame(frame)
        selector_layout = QHBoxLayout(selector_frame)
        selector_layout.setContentsMargins(5, 5, 5, 5)
        
        # 标签
        label = QLabel(label_text)
        label.setMinimumHeight(30)  # 增加高度以便于点击
        selector_layout.addWidget(label)
        
        # 输入框
        line_edit.setMinimumHeight(32)  # 增加高度以便于点击
        selector_layout.addWidget(line_edit, 1)  # 1为伸缩因子，使输入框占据更多空间
        
        # 浏览按钮
        browse_button = QPushButton("浏览")
        browse_button.setMinimumHeight(32)  # 增加高度以便于点击
        browse_button.setMinimumWidth(100)  # 增加按钮宽度
        browse_button.clicked.connect(browse_command)
        selector_layout.addWidget(browse_button)
        
        # 如果提供了布局和行信息，则将框架添加到布局中
        if isinstance(frame.layout(), QGridLayout):
            frame.layout().addWidget(selector_frame, row, 0, 1, 3)
        else:
            frame.layout().addWidget(selector_frame)
        
        return selector_frame 