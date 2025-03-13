import customtkinter as ctk
from pathlib import Path
import threading
from typing import Callable, Dict, List
from PIL import Image, ImageTk
import os

from .base_tab import BaseTab
from ..core import PhotoSimilarityFinder

class SimilarityTab(BaseTab):
    """相似照片查找选项卡"""
    
    def __init__(self, parent: ctk.CTkFrame, message_callback: Callable):
        self.message_callback = message_callback
        self.similarity_input_path = ctk.StringVar()
        super().__init__(parent)
        
    def setup_ui(self):
        """设置UI组件"""
        # 配置父框架
        self.parent.grid_columnconfigure(0, weight=1)
        self.parent.grid_rowconfigure(0, weight=1)
        
        # 主框架
        main_frame = ctk.CTkFrame(self.parent)
        main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(2, weight=1)  # 预览区域可扩展
        
        # 输入目录选择
        self.create_directory_selector(
            main_frame,
            "选择要查找的目录：",
            self.similarity_input_path,
            lambda: self.browse_directory("选择目录", self.similarity_input_path),
            row=0
        )
        
        # 相似度设置框架
        threshold_frame = ctk.CTkFrame(main_frame)
        threshold_frame.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
        threshold_frame.grid_columnconfigure(1, weight=1)
        
        # 相似度阈值滑块
        threshold_label = ctk.CTkLabel(
            threshold_frame, 
            text="相似度阈值：",
            height=30  # 增加高度以便于点击
        )
        threshold_label.grid(row=0, column=0, padx=5, pady=5)
        
        self.similarity_threshold = ctk.CTkSlider(
            threshold_frame,
            from_=1,
            to=10,
            number_of_steps=9,
            height=20,  # 增加高度以便于点击
            width=200   # 设置合适的宽度
        )
        self.similarity_threshold.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # 预览区域标题
        preview_label = ctk.CTkLabel(
            main_frame, 
            text="相似照片预览：",
            height=30  # 增加高度以便于点击
        )
        preview_label.grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky="w")
        
        # 预览区域（可滚动）
        self.preview_frame = ctk.CTkScrollableFrame(
            main_frame,
            height=400,
            width=700  # 设置合适的初始宽度
        )
        self.preview_frame.grid(row=3, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")
        
        # 按钮框架
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
        button_frame.grid_columnconfigure(0, weight=1)
        
        # 开始查找按钮
        start_button = ctk.CTkButton(
            button_frame,
            text="开始查找",
            command=self.start_search,
            height=40,  # 增加按钮高度
            width=200   # 增加按钮宽度
        )
        start_button.grid(row=0, column=0, padx=5, pady=5)
        
    def start_search(self):
        """开始查找相似照片"""
        if not self.similarity_input_path.get():
            self.show_error("错误", "请选择要查找的目录")
            return
            
        # 清除预览区域
        for widget in self.preview_frame.winfo_children():
            widget.destroy()
            
        # 在新线程中处理
        thread = threading.Thread(target=self.search_thread)
        thread.daemon = True
        thread.start()
        
    def search_thread(self):
        """在线程中查找相似照片"""
        try:
            self.message_callback("开始查找相似照片...")
            
            finder = PhotoSimilarityFinder()
            similar_groups = finder.find_similar_photos(
                self.similarity_input_path.get(),
                hash_threshold=int(self.similarity_threshold.get())
            )
            
            if not similar_groups:
                self.message_callback("未找到相似照片")
                self.show_info("结果", "未找到相似照片")
                return
                
            self.show_similar_photos(similar_groups)
            self.message_callback(f"找到 {len(similar_groups)} 组相似照片")
            
        except Exception as e:
            error_msg = f"查找相似照片时出错: {str(e)}"
            self.message_callback(error_msg)
            self.show_error("错误", error_msg)
            
    def show_similar_photos(self, similar_groups: Dict[str, List[str]]):
        """显示相似照片组"""
        try:
            # 清除预览区域
            for widget in self.preview_frame.winfo_children():
                widget.destroy()
                
            # 显示每组相似照片
            for hash_value, file_paths in similar_groups.items():
                group_frame = ctk.CTkFrame(self.preview_frame)
                group_frame.pack(fill="x", padx=5, pady=5)
                
                # 显示缩略图和文件信息
                for file_path in file_paths:
                    try:
                        with Image.open(file_path) as img:
                            # 创建缩略图
                            thumb = img.copy()
                            thumb.thumbnail((150, 150))  # 增加缩略图大小
                            photo = ImageTk.PhotoImage(thumb)
                            
                            # 显示图片和信息
                            photo_frame = ctk.CTkFrame(group_frame)
                            photo_frame.pack(side="left", padx=10, pady=10)  # 增加间距
                            
                            label = ctk.CTkLabel(photo_frame, image=photo)
                            label.image = photo  # 保持引用
                            label.pack(padx=5, pady=5)
                            
                            info = PhotoSimilarityFinder.get_file_info(file_path)
                            info_text = (
                                f"大小: {info['size'] // 1024}KB\n"
                                f"路径: {info['path']}"
                            )
                            info_label = ctk.CTkLabel(
                                photo_frame, 
                                text=info_text,
                                wraplength=150,
                                height=60  # 增加高度以显示完整信息
                            )
                            info_label.pack(padx=5, pady=5)
                            
                            # 删除按钮
                            delete_button = ctk.CTkButton(
                                photo_frame,
                                text="删除",
                                command=lambda p=file_path: self.delete_photo(p),
                                height=32,  # 增加按钮高度
                                width=100   # 增加按钮宽度
                            )
                            delete_button.pack(padx=5, pady=5)
                            
                    except Exception as e:
                        self.message_callback(f"处理预览时出错: {str(e)}")
                        
        except Exception as e:
            self.message_callback(f"显示相似照片时出错: {str(e)}")
            
    def delete_photo(self, file_path: str):
        """删除照片"""
        if self.confirm("确认删除", f"确定要删除文件：\n{file_path}？"):
            try:
                os.remove(file_path)
                self.message_callback(f"已删除文件: {file_path}")
                # 刷新预览
                self.start_search()
            except Exception as e:
                error_msg = f"删除文件时出错：{str(e)}"
                self.message_callback(error_msg)
                self.show_error("错误", error_msg) 