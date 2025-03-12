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
import customtkinter as ctk
from tkinter import filedialog, messagebox

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 设置GUI主题
ctk.set_appearance_mode("System")  # 跟随系统主题
ctk.set_default_color_theme("blue")

class PhotoOrganizerGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        # 配置主窗口
        self.title("照片整理工具")
        self.geometry("800x600")  # 增加窗口大小以便更好地显示日志
        
        # 创建消息队列用于线程间通信
        self.message_queue = queue.Queue()
        
        # 创建主框架
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # 创建界面元素
        self.create_widgets()
        
        # 定期检查消息队列
        self.check_message_queue()

    def create_widgets(self):
        # 主框架
        main_frame = ctk.CTkFrame(self)
        main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        main_frame.grid_columnconfigure(1, weight=1)
        
        # 输入目录选择
        ctk.CTkLabel(main_frame, text="输入目录:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.input_dir_var = ctk.StringVar()
        input_entry = ctk.CTkEntry(main_frame, textvariable=self.input_dir_var)
        input_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(main_frame, text="浏览", command=self.browse_input).grid(row=0, column=2, padx=5, pady=5)

        # 输出目录选择
        ctk.CTkLabel(main_frame, text="输出目录:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.output_dir_var = ctk.StringVar()
        output_entry = ctk.CTkEntry(main_frame, textvariable=self.output_dir_var)
        output_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(main_frame, text="浏览", command=self.browse_output).grid(row=1, column=2, padx=5, pady=5)

        # 进度显示
        self.progress_var = ctk.StringVar(value="准备就绪")
        progress_label = ctk.CTkLabel(main_frame, textvariable=self.progress_var)
        progress_label.grid(row=2, column=0, columnspan=3, padx=5, pady=5)

        # 进度条
        self.progressbar = ctk.CTkProgressBar(main_frame)
        self.progressbar.grid(row=3, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
        self.progressbar.set(0)  # 初始化进度条
        
        # 开始按钮
        self.start_button = ctk.CTkButton(
            main_frame, 
            text="开始处理", 
            command=self.start_processing,
            height=40  # 增加按钮高度
        )
        self.start_button.grid(row=4, column=0, columnspan=3, padx=5, pady=20)

        # 日志显示
        log_frame = ctk.CTkFrame(main_frame)
        log_frame.grid(row=5, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")
        main_frame.grid_rowconfigure(5, weight=1)
        
        # 日志标题
        ctk.CTkLabel(log_frame, text="处理日志:").pack(anchor="w", padx=5, pady=2)
        
        # 日志文本框
        self.log_text = ctk.CTkTextbox(log_frame, height=200, wrap="word")
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 添加初始日志
        self.log_text.insert("end", "程序已启动，等待选择目录...\n")
        self.log_text.see("end")

    def browse_input(self):
        directory = filedialog.askdirectory(title="选择输入目录")
        if directory:
            self.input_dir_var.set(directory)
            if not self.output_dir_var.get():
                self.output_dir_var.set(directory)

    def browse_output(self):
        directory = filedialog.askdirectory(title="选择输出目录")
        if directory:
            self.output_dir_var.set(directory)

    def update_progress(self, message, progress=None):
        try:
            self.progress_var.set(message)
            if progress is not None:
                self.progressbar.set(progress)
            self.log_text.insert("end", f"{datetime.now().strftime('%H:%M:%S')} - {message}\n")
            self.log_text.see("end")
            self.update_idletasks()  # 强制更新GUI
        except Exception as e:
            print(f"更新进度时出错: {e}")

    def check_message_queue(self):
        """检查消息队列并更新GUI"""
        try:
            while True:  # 处理队列中的所有消息
                message, progress = self.message_queue.get_nowait()
                self.update_progress(message, progress)
        except queue.Empty:
            pass
        finally:
            # 继续检查消息队列
            self.after(100, self.check_message_queue)

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
            self.message_queue.put((f"无法从{file_path}读取EXIF信息: {str(e)}", None))
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
            self.message_queue.put((f"从路径推断日期失败: {str(e)}", None))
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
        """将文件移动到未分类目录，保持原始路径结构"""
        try:
            # 创建未分类目录
            unsorted_dir = output_base / "Unsorted"
            unsorted_dir.mkdir(parents=True, exist_ok=True)
            
            # 保持原始相对路径
            relative_path = file_path.parent.relative_to(file_path.parent.anchor)
            target_dir = unsorted_dir / relative_path
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # 移动文件
            new_path = target_dir / file_path.name
            shutil.move(str(file_path), str(new_path))
            self.message_queue.put((f"已将文件 {file_path.name} 移动到未分类目录", None))
        except Exception as e:
            self.message_queue.put((f"移动文件到未分类目录失败: {str(e)}", None))

    def get_number_from_filename(self, filename: str) -> Optional[int]:
        """从文件名中提取数字"""
        match = re.search(r'(\d+)', filename)
        return int(match.group(1)) if match else None

    def process_directory(self):
        """处理指定目录下的所有照片和视频文件（包括所有子目录）"""
        input_dir = self.input_dir_var.get()
        output_dir = self.output_dir_var.get()
        
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        
        if not input_path.exists():
            raise ValueError(f"输入目录 {input_dir} 不存在")
        
        # 创建输出根目录
        output_path.mkdir(parents=True, exist_ok=True)

        # 获取所有支持的文件（包括子目录）
        supported_extensions = ('.jpg', '.jpeg', '.png', '.mp4', '.mov', '.MOV')
        all_files = [
            f for f in input_path.rglob('*') 
            if f.suffix.lower() in supported_extensions
        ]
        
        if not all_files:
            self.message_queue.put(("未找到支持的文件", 0))
            return
        
        # 按目录分组处理文件
        files_by_dir = {}
        for file in all_files:
            files_by_dir.setdefault(file.parent, []).append(file)

        # 处理每个目录中的文件
        processed_files = set()
        total_dirs = len(files_by_dir)
        
        for i, (dir_path, dir_files) in enumerate(files_by_dir.items(), 1):
            self.message_queue.put((f"正在处理目录: {dir_path}", i/total_dirs))
            
            # 获取目录的推断时间（用作后备）
            dir_inferred_date = self.infer_date_from_path(dir_path)
            
            # 按文件名排序处理文件
            sorted_files = sorted(dir_files, key=lambda x: self.get_number_from_filename(x.name) or float('inf'))
            
            for file in sorted_files:
                if file.name in processed_files:
                    continue

                # 尝试获取创建时间（多种方法）
                creation_date = None
                
                # 1. 从EXIF获取
                creation_date = self.get_creation_date_from_exif(str(file))
                
                # 2. 从相关文件获取
                if not creation_date:
                    creation_date = self.get_date_from_related_files(sorted_files, file)
                
                # 3. 从路径推断
                if not creation_date:
                    creation_date = dir_inferred_date
                
                # 如果仍然无法确定时间，移动到未分类目录
                if not creation_date:
                    self.move_to_unsorted(file, output_path)
                    processed_files.add(file.name)
                    continue

                # 创建目标目录
                year_dir = output_path / str(creation_date.year)
                month_dir = year_dir / f"{creation_date.month:02d}"
                month_dir.mkdir(parents=True, exist_ok=True)

                # 设置文件时间
                timestamp = creation_date.timestamp()
                os.utime(str(file), (timestamp, timestamp))

                # 移动文件
                new_path = month_dir / file.name
                shutil.move(str(file), str(new_path))
                processed_files.add(file.name)
                self.message_queue.put((f"已处理文件 {file.name}", None))

        self.message_queue.put(("处理完成！", 1.0))

    def process_directory_safe(self):
        """安全地处理目录，包含错误处理"""
        try:
            self.message_queue.put(("开始处理文件...", 0.0))
            self.process_directory()
        except Exception as e:
            error_msg = f"处理过程中发生错误: {str(e)}"
            self.message_queue.put((error_msg, None))
            messagebox.showerror("错误", error_msg)
        finally:
            # 重新启用开始按钮
            self.after(0, lambda: self.start_button.configure(state="normal"))

    def start_processing(self):
        """开始处理文件"""
        if not self.input_dir_var.get():
            messagebox.showerror("错误", "请选择输入目录")
            return
        if not self.output_dir_var.get():
            messagebox.showerror("错误", "请选择输出目录")
            return
            
        # 清空日志
        self.log_text.delete("1.0", "end")
        self.log_text.insert("end", "开始新的处理任务...\n")
        
        # 重置进度条
        self.progressbar.set(0)
        
        # 禁用开始按钮
        self.start_button.configure(state="disabled")
        
        # 在新线程中处理文件
        thread = threading.Thread(target=self.process_directory_safe)
        thread.daemon = True  # 设置为守护线程
        thread.start()

def main():
    app = PhotoOrganizerGUI()
    app.mainloop()

if __name__ == '__main__':
    main() 