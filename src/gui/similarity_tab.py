from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QGridLayout, QPushButton, QLineEdit, QFileDialog,
    QSlider, QScrollArea, QSizePolicy, QGroupBox
)
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QPixmap, QImage
from pathlib import Path
import threading
from typing import Callable, Dict, List
from PIL import Image
import os

from .base_tab import BaseTab
from ..core.similarity import PhotoSimilarityFinder

class SimilarityTab(BaseTab):
    """相似照片查找选项卡"""
    
    def __init__(self, parent: QWidget, message_callback: Callable):
        self.message_callback = message_callback
        self.input_dir_line_edit = QLineEdit()
        self.threshold_slider = None
        self.threshold_value_label = None
        self.preview_area = None
        self.similar_photos = {}  # 存储相似照片组
        self.preview_widgets = {}  # 存储预览小部件
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
            "照片目录:",
            self.input_dir_line_edit,
            lambda: self.browse_directory("选择包含照片的目录", self.input_dir_line_edit)
        )
        
        # 相似度阈值设置
        threshold_frame = QFrame()
        frame_layout.addWidget(threshold_frame)
        threshold_layout = QHBoxLayout(threshold_frame)
        
        threshold_layout.addWidget(QLabel("相似度阈值:"))
        
        self.threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.threshold_slider.setMinimum(1)
        self.threshold_slider.setMaximum(10)
        self.threshold_slider.setValue(5)
        self.threshold_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.threshold_slider.setTickInterval(1)
        self.threshold_slider.valueChanged.connect(self.update_threshold_label)
        threshold_layout.addWidget(self.threshold_slider)
        
        self.threshold_value_label = QLabel("5")
        threshold_layout.addWidget(self.threshold_value_label)
        
        # 预览区域
        preview_group = QGroupBox("相似照片预览")
        frame_layout.addWidget(preview_group, 1)  # 1是拉伸因子
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_area = QScrollArea()
        self.preview_area.setWidgetResizable(True)
        self.preview_area.setMinimumHeight(300)
        
        preview_content = QWidget()
        self.preview_area.setWidget(preview_content)
        self.preview_layout = QVBoxLayout(preview_content)
        
        preview_layout.addWidget(self.preview_area)
        
        # 搜索按钮
        button_frame = QFrame()
        frame_layout.addWidget(button_frame)
        button_layout = QHBoxLayout(button_frame)
        button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        search_button = QPushButton("开始搜索")
        search_button.setMinimumHeight(40)
        search_button.setMinimumWidth(200)
        search_button.clicked.connect(self.start_search)
        button_layout.addWidget(search_button)
        
        # 设置主布局
        if hasattr(self.parent, 'layout') and callable(self.parent.layout):
            if self.parent.layout() is not None:
                existing_layout = self.parent.layout()
                existing_layout.addLayout(main_layout)
            else:
                self.parent.setLayout(main_layout)
    
    def update_threshold_label(self, value):
        """更新阈值标签"""
        self.threshold_value_label.setText(str(value))
    
    def start_search(self):
        """开始搜索相似照片"""
        input_dir = self.input_dir_line_edit.text()
        if not input_dir:
            self.show_error("错误", "请选择照片目录")
            return
            
        if not Path(input_dir).exists():
            self.show_error("错误", "选择的目录不存在")
            return
            
        # 清除先前的结果
        self.clear_preview()
        
        # 在新线程中搜索
        threshold = self.threshold_slider.value()
        thread = threading.Thread(
            target=self.search_thread,
            args=(input_dir, threshold)
        )
        thread.daemon = True
        thread.start()
        
    def search_thread(self, input_dir: str, threshold: int):
        """在线程中搜索相似照片"""
        try:
            self.message_callback("开始搜索相似照片...")
            
            finder = PhotoSimilarityFinder()
            self.similar_photos = finder.find_similar_photos(
                Path(input_dir),
                hash_threshold=threshold
            )
            
            # 在主线程中更新UI
            if self.similar_photos:
                # 不使用QMetaObject.invokeMethod，而是通过父窗口的after方法安全地在主线程中调用
                QTimer.singleShot(0, self.show_similar_photos)
                self.message_callback(f"找到 {len(self.similar_photos)} 组相似照片。")
            else:
                self.message_callback("未找到相似照片。")
                
        except Exception as e:
            self.message_callback(f"搜索过程中发生错误: {str(e)}")
            
    def show_similar_photos(self):
        """显示相似照片"""
        # 清除先前的预览
        self.clear_preview()
        
        # 显示新的预览
        for group_id, files in self.similar_photos.items():
            # 组标题
            group_frame = QFrame()
            group_layout = QVBoxLayout(group_frame)
            
            title_label = QLabel(f"相似组 {group_id} (共 {len(files)} 张照片)")
            title_label.setStyleSheet("font-weight: bold;")
            group_layout.addWidget(title_label)
            
            # 照片网格
            photos_frame = QFrame()
            photos_layout = QGridLayout(photos_frame)
            group_layout.addWidget(photos_frame)
            
            # 每行显示3张照片
            for i, file_path in enumerate(files):
                file_info = PhotoSimilarityFinder.get_file_info(file_path)
                file_frame = self.create_photo_preview(file_path, file_info, group_id)
                
                row = i // 3
                col = i % 3
                photos_layout.addWidget(file_frame, row, col)
            
            # 分隔线
            separator = QFrame()
            separator.setFrameShape(QFrame.Shape.HLine)
            separator.setFrameShadow(QFrame.Shadow.Sunken)
            
            # 添加到预览区域
            self.preview_layout.addWidget(group_frame)
            self.preview_layout.addWidget(separator)
            
            # 保存小部件引用
            self.preview_widgets[group_id] = group_frame
            
    def create_photo_preview(self, file_path: str, file_info: Dict, group_id: int) -> QWidget:
        """创建照片预览小部件"""
        frame = QFrame()
        layout = QVBoxLayout(frame)
        
        try:
            # 缩略图
            img = Image.open(file_path)
            img.thumbnail((150, 150))
            
            # 转换为QPixmap
            img_rgb = img.convert("RGB")
            qimage = QImage(
                img_rgb.tobytes(), 
                img.width, 
                img.height, 
                img.width * 3,
                QImage.Format.Format_RGB888
            )
            pixmap = QPixmap.fromImage(qimage)
            
            # 显示缩略图
            image_label = QLabel()
            image_label.setPixmap(pixmap)
            image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(image_label)
            
        except Exception as e:
            # 如果无法加载图像，显示错误消息
            error_label = QLabel("无法加载图像")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(error_label)
            self.message_callback(f"无法加载图像 {Path(file_path).name}: {str(e)}")
        
        # 文件信息
        file_size = f"{file_info['size'] // 1024}KB" if 'size' in file_info else 'N/A'
        info_label = QLabel(
            f"文件: {Path(file_path).name}\n"
            f"大小: {file_size}\n"
            f"修改时间: {file_info.get('mtime', 'N/A')}"
        )
        info_label.setWordWrap(True)
        info_label.setMinimumHeight(60)
        layout.addWidget(info_label)
        
        # 删除按钮
        delete_button = QPushButton("删除")
        delete_button.clicked.connect(
            lambda checked=False, path=file_path, gid=group_id: 
            self.delete_photo(path, gid)
        )
        layout.addWidget(delete_button)
        
        return frame
    
    def delete_photo(self, file_path: str, group_id: int):
        """删除照片"""
        if self.confirm("确认删除", f"确定要删除文件 {Path(file_path).name} 吗？"):
            try:
                # 删除文件
                os.remove(file_path)
                self.message_callback(f"已删除文件: {file_path}")
                
                # 从相似照片列表中移除
                self.similar_photos[group_id] = [
                    f for f in self.similar_photos[group_id]
                    if f != file_path
                ]
                
                # 如果组中没有照片了，则移除整个组
                if not self.similar_photos[group_id]:
                    del self.similar_photos[group_id]
                    
                # 重新显示预览
                self.show_similar_photos()
                
            except Exception as e:
                self.message_callback(f"删除文件时出错: {str(e)}")
                self.show_error("删除错误", f"无法删除文件: {str(e)}")
    
    def clear_preview(self):
        """清除预览区域"""
        # 移除所有小部件
        for widget in self.preview_widgets.values():
            widget.setParent(None)
            
        # 清空存储
        self.preview_widgets = {} 