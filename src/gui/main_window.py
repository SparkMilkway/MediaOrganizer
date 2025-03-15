#!/usr/bin/env python3
import os
import re
import threading
import queue
from datetime import datetime
from pathlib import Path
import shutil
from PIL import Image
import piexif
from typing import Optional, List
import logging
import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, 
    QHBoxLayout, QLabel, QTextEdit, QFrame, QGridLayout, QSplitter
)
from PyQt6.QtCore import QTimer, Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QFont
import imagehash

from .batch_tab import BatchTab
from .manual_tab import ManualTab
from .similarity_tab import SimilarityTab

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class PhotoOrganizerGUI(QMainWindow):
    """照片视频整理工具主窗口"""
    
    def __init__(self):
        super().__init__()
        
        # 配置主窗口
        self.setWindowTitle("照片视频整理及Exif修改工具")
        self.resize(900, 700)
        
        # 创建消息队列用于线程间通信
        self.message_queue = queue.Queue()
        
        # 创建主框架
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # 创建界面元素
        self.create_widgets()
        
        # 定期检查消息队列
        self.message_timer = QTimer(self)
        self.message_timer.timeout.connect(self.check_message_queue)
        self.message_timer.start(100)  # 每100毫秒检查一次
        
    def create_widgets(self):
        """创建界面元素"""
        # 创建选项卡控件
        self.tabview = QTabWidget()
        self.main_layout.addWidget(self.tabview)
        
        # 添加选项卡
        self.tab_batch = QWidget()
        self.tab_manual = QWidget()
        self.tab_similarity = QWidget()
        
        # 设置选项卡布局
        self.tab_batch.setLayout(QVBoxLayout())
        self.tab_manual.setLayout(QVBoxLayout())
        self.tab_similarity.setLayout(QVBoxLayout())
        
        # 将选项卡添加到选项卡控件
        self.tabview.addTab(self.tab_batch, "批量整理")
        self.tabview.addTab(self.tab_manual, "手动修改日期")
        self.tabview.addTab(self.tab_similarity, "相似照片查找")
        
        # 创建选项卡内容
        self.batch_tab = BatchTab(self.tab_batch, self.log_message)
        self.manual_tab = ManualTab(self.tab_manual, self.log_message)
        self.similarity_tab = SimilarityTab(self.tab_similarity, self.log_message)
        
        # 创建一个分割器，用于调整日志区域大小
        splitter = QSplitter(Qt.Orientation.Vertical)
        self.main_layout.addWidget(splitter, 1)  # 1是拉伸因子
        
        # 日志显示框架
        log_frame = QWidget()
        log_layout = QVBoxLayout(log_frame)
        
        # 日志标题
        log_label = QLabel("处理日志:")
        log_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        log_layout.addWidget(log_label)
        
        # 日志文本框
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        # 将日志框架添加到分割器
        splitter.addWidget(log_frame)
        
        # 添加初始日志
        self.log_message("程序已启动，等待选择目录或文件...")
        
    def log_message(self, message: str):
        """添加日志消息到队列"""
        self.message_queue.put(message)
        
    def check_message_queue(self):
        """检查消息队列并更新GUI"""
        try:
            while True:  # 处理队列中的所有消息
                message = self.message_queue.get_nowait()
                self.update_log(message)
        except queue.Empty:
            pass
            
    def update_log(self, message: str):
        """更新日志显示"""
        try:
            timestamp = datetime.now().strftime('%H:%M:%S')
            self.log_text.append(f"{timestamp} - {message}")
            # 滚动到底部
            scrollbar = self.log_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
        except Exception as e:
            print(f"更新日志时出错: {e}")

    def get_creation_date_from_exif(self, file_path: str) -> Optional[datetime]:
        """从文件的EXIF信息中获取创建时间"""
        try:
            if file_path.lower().endswith(('.jpg', '.jpeg', '.png')):
                img = Image.open(file_path)
                if 'exif' in img.info:
                    exif_dict = piexif.load(img.info['exif'])
                    if piexif.ExifIFD.DateTimeOriginal in exif_dict['Exif']:
                        date_str = exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal].decode('utf-8')
                        return datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
        except Exception as e:
            self.log_message(f"无法从{file_path}读取EXIF信息: {str(e)}")
        return None

    def infer_date_from_path(self, file_path: Path) -> Optional[datetime]:
        """从文件路径推断日期"""
        try:
            # 常见的日期模式，例如：2023-01-01, 20230101, 2023_01_01等
            date_patterns = [
                r'(20\d{2})[/_-]?(\d{2})[/_-]?(\d{2})',  # 2023-01-01, 2023_01_01, 20230101
                r'(19\d{2})[/_-]?(\d{2})[/_-]?(\d{2})',  # 1999-01-01, 1999_01_01, 19990101
            ]
            
            path_str = str(file_path)
            for pattern in date_patterns:
                match = re.search(pattern, path_str)
                if match:
                    year, month, day = map(int, match.groups())
                    return datetime(year, month, day)
        except Exception as e:
            self.log_message(f"从路径推断日期失败: {str(e)}")
        return None

    def get_date_from_related_files(self, files: List[Path], current_file: Path) -> Optional[datetime]:
        """从相关文件中获取日期"""
        all_files = sorted(files, key=lambda x: self.get_number_from_filename(x.name) or float('inf'))
        current_index = all_files.index(current_file)
        
        # 向前和向后查找最近的有日期的文件
        for offset in range(len(all_files)):
            # 向前查找
            if current_index - offset >= 0:
                date = self.get_creation_date_from_exif(str(all_files[current_index - offset]))
                if date:
                    return date
            # 向后查找
            if current_index + offset < len(all_files):
                date = self.get_creation_date_from_exif(str(all_files[current_index + offset]))
                if date:
                    return date
        return None

    def move_to_unsorted(self, file_path: Path, output_base: Path) -> None:
        """将文件复制到未分类目录"""
        try:
            # 创建未分类目录
            unsorted_dir = output_base / "Unsorted"
            unsorted_dir.mkdir(parents=True, exist_ok=True)
            
            # 直接复制到Unsorted目录下
            new_path = unsorted_dir / file_path.name
            
            # 如果目标路径已存在同名文件，添加数字后缀
            counter = 1
            while new_path.exists():
                new_path = unsorted_dir / f"{file_path.stem}_{counter}{file_path.suffix}"
                counter += 1
                
            shutil.copy2(str(file_path), str(new_path))
            self.log_message(f"已将文件 {file_path.name} 复制到未分类目录")
        except Exception as e:
            self.log_message(f"复制文件到未分类目录失败: {str(e)}")

    def get_number_from_filename(self, filename: str) -> Optional[int]:
        """从文件名中提取数字"""
        match = re.search(r'(\d+)', filename)
        return int(match.group(1)) if match else None

    def get_file_stats(self, files: List[Path]) -> dict:
        """统计文件数量和大小"""
        stats = {
            'images': {'count': 0, 'size': 0},
            'videos': {'count': 0, 'size': 0}
        }
        
        image_extensions = {'.jpg', '.jpeg', '.png', '.heic', '.heif'}
        video_extensions = {'.mp4', '.mov', '.MOV'}
        
        for file in files:
            size = file.stat().st_size
            ext = file.suffix.lower()
            
            if ext in image_extensions:
                stats['images']['count'] += 1
                stats['images']['size'] += size
            elif ext in video_extensions:
                stats['videos']['count'] += 1
                stats['videos']['size'] += size
        
        return stats

    def format_size(self, size_in_bytes: int) -> str:
        """将字节大小转换为人类可读格式"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_in_bytes < 1024:
                return f"{size_in_bytes:.2f} {unit}"
            size_in_bytes /= 1024
        return f"{size_in_bytes:.2f} TB"

def main():
    app = QApplication(sys.argv)
    window = PhotoOrganizerGUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 