from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QGridLayout, QPushButton, QLineEdit, QFileDialog,
    QSlider, QScrollArea, QSizePolicy, QGroupBox, QCheckBox
)
from PyQt6.QtCore import Qt, QSize, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QPixmap, QImage
from pathlib import Path
import threading
from typing import Callable, Dict, List, Set
from PIL import Image
import os

from .base_tab import BaseTab
from ..core.similarity import PhotoSimilarityFinder

class SimilarityWorker(QObject):
    """用于处理相似照片搜索的工作线程"""
    finished = pyqtSignal(dict)  # 搜索完成信号
    error = pyqtSignal(str)      # 错误信号
    progress = pyqtSignal(str)   # 进度信号

    def __init__(self):
        super().__init__()
        self.finder = PhotoSimilarityFinder()

    def search(self, input_dir: str, threshold: int):
        """执行搜索"""
        try:
            self.progress.emit("开始搜索相似照片...")
            similar_photos = self.finder.find_similar_photos(
                Path(input_dir),
                hash_threshold=threshold
            )
            
            if similar_photos:
                self.progress.emit(f"搜索完成，找到 {len(similar_photos)} 组相似照片")
                for group_id, files in similar_photos.items():
                    self.progress.emit(f"组 {group_id} 包含 {len(files)} 张照片")
                self.finished.emit(similar_photos)
            else:
                self.progress.emit("未找到相似照片。")
                self.finished.emit({})
                
        except Exception as e:
            self.error.emit(str(e))

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
        self.worker = SimilarityWorker()  # 创建工作线程对象
        self.selected_photos: Set[str] = set()  # 存储选中的照片
        self.thumbnail_size = 150  # 默认缩略图大小
        super().__init__(parent)
        
        # 连接信号
        self.worker.finished.connect(self.on_search_finished)
        self.worker.error.connect(self.on_search_error)
        self.worker.progress.connect(self.message_callback)
        
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
        
        # 缩略图大小设置
        size_frame = QFrame()
        frame_layout.addWidget(size_frame)
        size_layout = QHBoxLayout(size_frame)
        
        size_layout.addWidget(QLabel("缩略图大小:"))
        
        self.size_slider = QSlider(Qt.Orientation.Horizontal)
        self.size_slider.setMinimum(50)
        self.size_slider.setMaximum(300)
        self.size_slider.setValue(self.thumbnail_size)
        self.size_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.size_slider.setTickInterval(50)
        self.size_slider.valueChanged.connect(self.update_thumbnail_size)
        size_layout.addWidget(self.size_slider)
        
        self.size_value_label = QLabel(str(self.thumbnail_size))
        size_layout.addWidget(self.size_value_label)
        
        # 预览区域
        preview_group = QGroupBox("相似照片预览")
        frame_layout.addWidget(preview_group, 1)  # 1是拉伸因子
        preview_layout = QVBoxLayout(preview_group)
        
        # 批量操作按钮
        batch_buttons = QFrame()
        batch_layout = QHBoxLayout(batch_buttons)
        
        self.select_all_button = QPushButton("全选")
        self.select_all_button.clicked.connect(self.select_all_photos)
        batch_layout.addWidget(self.select_all_button)
        
        self.deselect_all_button = QPushButton("取消全选")
        self.deselect_all_button.clicked.connect(self.deselect_all_photos)
        batch_layout.addWidget(self.deselect_all_button)
        
        self.delete_selected_button = QPushButton("删除选中")
        self.delete_selected_button.clicked.connect(self.delete_selected_photos)
        self.delete_selected_button.setEnabled(False)
        batch_layout.addWidget(self.delete_selected_button)
        
        preview_layout.addWidget(batch_buttons)
        
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
            target=self.worker.search,
            args=(input_dir, threshold)
        )
        thread.daemon = True
        thread.start()
        
    def on_search_finished(self, similar_photos: Dict):
        """搜索完成的回调"""
        self.similar_photos = similar_photos
        if self.similar_photos:
            self.show_similar_photos()
            
    def on_search_error(self, error_msg: str):
        """搜索错误的回调"""
        self.message_callback(f"搜索过程中发生错误: {error_msg}")
    
    def show_similar_photos(self):
        """显示相似照片"""
        try:
            # 清除先前的预览
            self.clear_preview()
            
            if not self.similar_photos:
                self.message_callback("没有相似照片需要显示")
                return
                
            self.message_callback("开始显示相似照片...")
            
            # 显示新的预览
            for group_id, files in self.similar_photos.items():
                self.message_callback(f"正在显示组 {group_id} 的照片...")
                
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
                    self.message_callback(f"正在处理照片: {Path(file_path).name}")
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
                
            self.message_callback("相似照片显示完成")
            
        except Exception as e:
            self.message_callback(f"显示相似照片时发生错误: {str(e)}")
            self.show_error("显示错误", f"无法显示相似照片: {str(e)}")
    
    def create_photo_preview(self, file_path: str, file_info: Dict, group_id: int) -> QWidget:
        """创建照片预览小部件"""
        frame = QFrame()
        layout = QVBoxLayout(frame)
        
        # 添加复选框
        checkbox = QCheckBox()
        checkbox.setChecked(file_path in self.selected_photos)
        checkbox.stateChanged.connect(
            lambda state, path=file_path: self.toggle_photo_selection(path, state == Qt.CheckState.Checked)
        )
        layout.addWidget(checkbox)
        
        try:
            # 使用PIL打开图片
            with Image.open(file_path) as img:
                # 转换为RGB模式（处理RGBA等格式）
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # 计算缩放比例，保持宽高比
                ratio = min(self.thumbnail_size / img.width, self.thumbnail_size / img.height)
                new_size = (int(img.width * ratio), int(img.height * ratio))
                
                # 缩放图片
                img = img.resize(new_size, Image.Resampling.LANCZOS)
                
                # 转换为QPixmap
                img_data = img.tobytes("raw", "RGB")
                qimage = QImage(img_data, img.width, img.height, img.width * 3, QImage.Format.Format_RGB888)
                pixmap = QPixmap.fromImage(qimage)
                
                # 显示缩略图
                image_label = QLabel()
                image_label.setPixmap(pixmap)
                image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                image_label.setMinimumSize(self.thumbnail_size, self.thumbnail_size)
                layout.addWidget(image_label)
                
        except Exception as e:
            # 如果无法加载图像，显示错误消息
            error_label = QLabel(f"无法加载图像: {str(e)}")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            error_label.setMinimumSize(self.thumbnail_size, self.thumbnail_size)
            layout.addWidget(error_label)
            self.message_callback(f"无法加载图像 {Path(file_path).name}: {str(e)}")
        
        # 文件信息
        file_size = f"{file_info['size'] // 1024}KB" if 'size' in file_info else 'N/A'
        info_label = QLabel(
            f"文件: {Path(file_path).name}\n"
            f"大小: {file_size}\n"
            f"修改时间: {file_info.get('modified', 'N/A')}"
        )
        info_label.setWordWrap(True)
        info_label.setMinimumHeight(60)
        layout.addWidget(info_label)
        
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

    def update_thumbnail_size(self, value: int):
        """更新缩略图大小"""
        self.thumbnail_size = value
        self.size_value_label.setText(str(value))
        if self.similar_photos:
            self.show_similar_photos()

    def select_all_photos(self):
        """全选所有照片"""
        self.selected_photos.clear()
        for group_files in self.similar_photos.values():
            self.selected_photos.update(group_files)
        self.update_selection_state()
        self.show_similar_photos()

    def deselect_all_photos(self):
        """取消全选"""
        self.selected_photos.clear()
        self.update_selection_state()
        self.show_similar_photos()

    def update_selection_state(self):
        """更新选择状态"""
        self.delete_selected_button.setEnabled(len(self.selected_photos) > 0)

    def delete_selected_photos(self):
        """删除选中的照片"""
        if not self.selected_photos:
            return
            
        if self.confirm("确认删除", f"确定要删除选中的 {len(self.selected_photos)} 张照片吗？"):
            try:
                # 删除文件
                for file_path in self.selected_photos:
                    os.remove(file_path)
                    self.message_callback(f"已删除文件: {file_path}")
                
                # 更新相似照片列表
                new_similar_photos = {}
                for group_id, files in self.similar_photos.items():
                    remaining_files = [f for f in files if f not in self.selected_photos]
                    if remaining_files:
                        new_similar_photos[group_id] = remaining_files
                
                self.similar_photos = new_similar_photos
                self.selected_photos.clear()
                self.update_selection_state()
                
                # 重新显示预览
                self.show_similar_photos()
                
            except Exception as e:
                self.message_callback(f"删除文件时出错: {str(e)}")
                self.show_error("删除错误", f"无法删除文件: {str(e)}")

    def toggle_photo_selection(self, file_path: str, selected: bool):
        """切换照片选择状态"""
        if selected:
            self.selected_photos.add(file_path)
        else:
            self.selected_photos.discard(file_path)
        self.update_selection_state() 