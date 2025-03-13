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
import tkcalendar  # 需要安装：pip install tkcalendar

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 设置GUI主题
ctk.set_appearance_mode("System")  # 跟随系统主题
ctk.set_default_color_theme("blue")

class PhotoOrganizerGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        # 配置主窗口
        self.title("照片视频Exif日期修改整理工具")
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
        
        # 创建选项卡控件
        tabview = ctk.CTkTabview(main_frame)
        tabview.grid(row=0, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")
        main_frame.grid_rowconfigure(0, weight=1)
        
        # 添加选项卡
        tab_auto = tabview.add("批量处理")
        tab_manual = tabview.add("手动处理")
        
        # 配置选项卡
        for tab in [tab_auto, tab_manual]:
            tab.grid_columnconfigure(1, weight=1)
        
        # ====== 批量处理选项卡 ======
        # 输入目录选择
        ctk.CTkLabel(tab_auto, text="输入目录:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.input_dir_var = ctk.StringVar()
        input_entry = ctk.CTkEntry(tab_auto, textvariable=self.input_dir_var)
        input_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(tab_auto, text="浏览", command=self.browse_input).grid(row=0, column=2, padx=5, pady=5)

        # 输出目录选择
        ctk.CTkLabel(tab_auto, text="输出目录:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.output_dir_var = ctk.StringVar()
        output_entry = ctk.CTkEntry(tab_auto, textvariable=self.output_dir_var)
        output_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(tab_auto, text="浏览", command=self.browse_output).grid(row=1, column=2, padx=5, pady=5)

        # 进度显示
        self.progress_var = ctk.StringVar(value="准备就绪")
        progress_label = ctk.CTkLabel(tab_auto, textvariable=self.progress_var)
        progress_label.grid(row=2, column=0, columnspan=3, padx=5, pady=5)

        # 进度条
        self.progressbar = ctk.CTkProgressBar(tab_auto)
        self.progressbar.grid(row=3, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
        self.progressbar.set(0)  # 初始化进度条
        
        # 开始按钮
        self.start_button = ctk.CTkButton(
            tab_auto, 
            text="开始处理", 
            command=self.start_processing,
            height=40  # 增加按钮高度
        )
        self.start_button.grid(row=4, column=0, columnspan=3, padx=5, pady=20)

        # ====== 手动处理选项卡 ======
        # 文件选择框架
        file_frame = ctk.CTkFrame(tab_manual)
        file_frame.grid(row=0, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
        
        # 选择文件按钮
        ctk.CTkLabel(file_frame, text="选择需要手动处理的文件:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ctk.CTkButton(file_frame, text="浏览文件", command=self.browse_manual_files).grid(row=0, column=1, padx=5, pady=5)
        
        # 显示选择的文件
        self.selected_files_var = ctk.StringVar(value="未选择文件")
        self.selected_files_label = ctk.CTkLabel(file_frame, textvariable=self.selected_files_var, wraplength=600)
        self.selected_files_label.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        
        # 日期选择框架
        date_frame = ctk.CTkFrame(tab_manual)
        date_frame.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
        
        # 创建日期选择控件
        ctk.CTkLabel(date_frame, text="设置照片拍摄日期:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        # 日期输入框架
        date_input_frame = ctk.CTkFrame(date_frame)
        date_input_frame.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        
        # 年月日选择
        self.year_var = ctk.StringVar(value=str(datetime.now().year))
        self.month_var = ctk.StringVar(value=str(datetime.now().month))
        self.day_var = ctk.StringVar(value=str(datetime.now().day))
        
        # 年选择
        ctk.CTkLabel(date_input_frame, text="年:").grid(row=0, column=0, padx=5, pady=5)
        year_entry = ctk.CTkEntry(date_input_frame, textvariable=self.year_var, width=60)
        year_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # 月选择
        ctk.CTkLabel(date_input_frame, text="月:").grid(row=0, column=2, padx=5, pady=5)
        month_entry = ctk.CTkEntry(date_input_frame, textvariable=self.month_var, width=40)
        month_entry.grid(row=0, column=3, padx=5, pady=5)
        
        # 日选择
        ctk.CTkLabel(date_input_frame, text="日:").grid(row=0, column=4, padx=5, pady=5)
        day_entry = ctk.CTkEntry(date_input_frame, textvariable=self.day_var, width=40)
        day_entry.grid(row=0, column=5, padx=5, pady=5)
        
        # 时间选择（可选）
        ctk.CTkLabel(date_input_frame, text="时:").grid(row=0, column=6, padx=5, pady=5)
        self.hour_var = ctk.StringVar(value="12")
        hour_entry = ctk.CTkEntry(date_input_frame, textvariable=self.hour_var, width=40)
        hour_entry.grid(row=0, column=7, padx=5, pady=5)
        
        ctk.CTkLabel(date_input_frame, text="分:").grid(row=0, column=8, padx=5, pady=5)
        self.minute_var = ctk.StringVar(value="00")
        minute_entry = ctk.CTkEntry(date_input_frame, textvariable=self.minute_var, width=40)
        minute_entry.grid(row=0, column=9, padx=5, pady=5)
        
        # 输出目录选择
        output_frame = ctk.CTkFrame(tab_manual)
        output_frame.grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
        
        ctk.CTkLabel(output_frame, text="处理后的文件保存到:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.manual_output_dir_var = ctk.StringVar()
        manual_output_entry = ctk.CTkEntry(output_frame, textvariable=self.manual_output_dir_var)
        manual_output_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        output_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkButton(output_frame, text="浏览", command=self.browse_manual_output).grid(row=0, column=2, padx=5, pady=5)
        
        # 处理按钮
        self.process_manual_button = ctk.CTkButton(
            tab_manual, 
            text="处理选定的文件", 
            command=self.process_manual_files,
            height=40
        )
        self.process_manual_button.grid(row=3, column=0, columnspan=3, padx=5, pady=20, sticky="ew")

        # 日志显示
        log_frame = ctk.CTkFrame(main_frame)
        log_frame.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")
        main_frame.grid_rowconfigure(1, weight=1)
        
        # 日志标题
        ctk.CTkLabel(log_frame, text="处理日志:").pack(anchor="w", padx=5, pady=2)
        
        # 日志文本框
        self.log_text = ctk.CTkTextbox(log_frame, height=200, wrap="word")
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 添加初始日志
        self.log_text.insert("end", "程序已启动，等待选择目录或文件...\n")
        self.log_text.see("end")
        
        # 存储手动选择的文件
        self.manual_files = []

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

    def browse_manual_files(self):
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
            self.message_queue.put((f"已选择 {len(files)} 个文件进行手动处理", None))
            
            # 如果没有设置输出目录，则使用第一个文件的目录作为默认输出目录
            if not self.manual_output_dir_var.get() and files:
                default_output = str(Path(files[0]).parent)
                self.manual_output_dir_var.set(default_output)

    def browse_manual_output(self):
        """为手动处理选择输出目录"""
        directory = filedialog.askdirectory(title="选择输出目录")
        if directory:
            self.manual_output_dir_var.set(directory)

    def process_manual_files(self):
        """处理手动选择的文件，设置为指定的日期"""
        if not self.manual_files:
            messagebox.showerror("错误", "请先选择需要处理的文件")
            return
            
        if not self.manual_output_dir_var.get():
            messagebox.showerror("错误", "请选择输出目录")
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
            messagebox.showerror("错误", f"日期格式无效: {str(e)}")
            return
            
        # 禁用处理按钮
        self.process_manual_button.configure(state="disabled")
        
        # 在新线程中处理文件
        thread = threading.Thread(
            target=self.process_manual_files_thread, 
            args=(user_date,)
        )
        thread.daemon = True
        thread.start()
        
    def process_manual_files_thread(self, user_date):
        """在线程中处理手动选择的文件"""
        try:
            self.message_queue.put(("开始处理手动选择的文件...", 0.0))
            
            output_path = Path(self.manual_output_dir_var.get())
            output_path.mkdir(parents=True, exist_ok=True)
            
            # 创建目标目录
            year_dir = output_path / str(user_date.year)
            month_dir = year_dir / f"{user_date.month:02d}"
            month_dir.mkdir(parents=True, exist_ok=True)
            
            processed_count = 0
            total_files = len(self.manual_files)
            
            for file_path in self.manual_files:
                file = Path(file_path)
                
                # 设置文件时间
                timestamp = user_date.timestamp()
                os.utime(str(file), (timestamp, timestamp))
                
                # 复制到目标目录
                new_path = month_dir / file.name
                
                # 如果目标路径已存在同名文件，添加数字后缀
                counter = 1
                while new_path.exists():
                    new_path = month_dir / f"{file.stem}_{counter}{file.suffix}"
                    counter += 1
                
                shutil.copy2(str(file), str(new_path))
                
                processed_count += 1
                self.message_queue.put((f"已处理文件 {file.name} ({processed_count}/{total_files})", processed_count/total_files))
                
            self.message_queue.put((f"所有手动选择的文件处理完成！共处理 {processed_count} 个文件", 1.0))
            
            # 显示完成提示
            self.after(500, lambda: messagebox.showinfo("处理完成", 
                f"手动选择的文件处理完成！\n\n"
                f"已将 {processed_count} 个文件处理为日期: "
                f"{user_date.year}-{user_date.month:02d}-{user_date.day:02d} "
                f"{user_date.hour:02d}:{user_date.minute:02d}"))
                
        except Exception as e:
            error_msg = f"处理文件时出错: {str(e)}"
            self.message_queue.put((error_msg, None))
            messagebox.showerror("错误", error_msg)
        finally:
            # 启用处理按钮
            self.after(0, lambda: self.process_manual_button.configure(state="normal"))

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
        """将文件复制到未分类目录，不保留原始路径结构"""
        try:
            # 创建未分类目录
            unsorted_dir = output_base / "Unsorted"
            unsorted_dir.mkdir(parents=True, exist_ok=True)
            
            # 直接复制到Unsorted目录下，不保留原路径结构
            new_path = unsorted_dir / file_path.name
            
            # 如果目标路径已存在同名文件，添加数字后缀
            counter = 1
            while new_path.exists():
                new_path = unsorted_dir / f"{file_path.stem}_{counter}{file_path.suffix}"
                counter += 1
                
            shutil.copy2(str(file_path), str(new_path))
            self.message_queue.put((f"已将文件 {file_path.name} 复制到未分类目录", None))
        except Exception as e:
            self.message_queue.put((f"复制文件到未分类目录失败: {str(e)}", None))

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

    def generate_report(self, input_stats: dict, output_stats: dict, output_path: Path) -> None:
        """生成处理报告并保存到文件"""
        report = "照片视频处理统计报告\n"
        report += "=" * 50 + "\n\n"
        
        report += "输入目录统计：\n"
        report += f"图片数量：{input_stats['images']['count']} 个\n"
        report += f"图片大小：{self.format_size(input_stats['images']['size'])}\n"
        report += f"视频数量：{input_stats['videos']['count']} 个\n"
        report += f"视频大小：{self.format_size(input_stats['videos']['size'])}\n"
        report += f"总文件数：{input_stats['images']['count'] + input_stats['videos']['count']} 个\n"
        report += f"总大小：{self.format_size(input_stats['images']['size'] + input_stats['videos']['size'])}\n\n"
        
        report += "输出目录统计：\n"
        report += f"图片数量：{output_stats['images']['count']} 个\n"
        report += f"图片大小：{self.format_size(output_stats['images']['size'])}\n"
        report += f"视频数量：{output_stats['videos']['count']} 个\n"
        report += f"视频大小：{self.format_size(output_stats['videos']['size'])}\n"
        report += f"总文件数：{output_stats['images']['count'] + output_stats['videos']['count']} 个\n"
        report += f"总大小：{self.format_size(output_stats['images']['size'] + output_stats['videos']['size'])}\n"
        
        report_path = output_path / "处理报告.txt"
        report_path.write_text(report, encoding='utf-8')
        self.message_queue.put((f"统计报告已保存到：{report_path}", None))
        
        # 在日志框中显示报告内容
        self.message_queue.put(("=" * 50, None))
        self.message_queue.put(("处理统计报告：", None))
        for line in report.split('\n'):
            if line.strip():
                self.message_queue.put((line, None))
        self.message_queue.put(("=" * 50, None))

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
        supported_extensions = ('.jpg', '.jpeg', '.png', '.heic', '.heif', '.mp4', '.mov', '.MOV')
        all_files = [
            f for f in input_path.rglob('*') 
            if f.suffix.lower() in supported_extensions
        ]
        
        # 获取输入目录的统计信息
        input_stats = self.get_file_stats(all_files)
        
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
                    # 找到相关文件（基于文件名序号）
                    related_files = []
                    for other_file in sorted_files:
                        if abs((self.get_number_from_filename(file.name) or 0) - 
                              (self.get_number_from_filename(other_file.name) or 0)) <= 1:
                            related_files.append(other_file)
                    
                    # 将所有相关文件都复制到未分类目录
                    self.message_queue.put((f"无法确定{file.name}及相关文件的创建时间，复制到未分类目录", None))
                    for related_file in related_files:
                        if related_file.name not in processed_files:
                            self.move_to_unsorted(related_file, output_path)
                            processed_files.add(related_file.name)
                    continue

                # 创建目标目录
                year_dir = output_path / str(creation_date.year)
                month_dir = year_dir / f"{creation_date.month:02d}"
                month_dir.mkdir(parents=True, exist_ok=True)

                # 设置文件时间
                timestamp = creation_date.timestamp()
                os.utime(str(file), (timestamp, timestamp))

                # 复制文件
                new_path = month_dir / file.name
                shutil.copy2(str(file), str(new_path))
                processed_files.add(file.name)
                self.message_queue.put((f"已复制文件 {file.name}", None))

        # 获取输出目录的统计信息
        output_files = [
            f for f in output_path.rglob('*') 
            if f.suffix.lower() in supported_extensions
        ]
        output_stats = self.get_file_stats(output_files)
        
        # 生成报告
        self.generate_report(input_stats, output_stats, output_path)
        
        self.message_queue.put(("处理完成！", 1.0))
        
        # 显示处理完成的对话框，提示用户可以重置状态
        self.after(500, lambda: messagebox.showinfo("处理完成", 
            f"所有文件处理完成！\n\n"
            f"已处理 {len(processed_files)} 个文件。\n"
            f"输入目录共有 {input_stats['images']['count'] + input_stats['videos']['count']} 个媒体文件。\n"
            f"输出目录共有 {output_stats['images']['count'] + output_stats['videos']['count']} 个媒体文件。\n\n"
            f"如需处理新的目录，请选择新的输入/输出目录，然后点击「开始处理」按钮。"))

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
            # 重置进度条状态
            self.progressbar.set(0)
            self.progress_var.set("准备就绪")

    def reset_state(self):
        """重置处理状态"""
        # 清空日志
        self.log_text.delete("1.0", "end")
        self.log_text.insert("end", "已重置状态，准备开始新的处理任务...\n")
        
        # 重置进度条
        self.progressbar.set(0)
        self.progress_var.set("准备就绪")
        
        # 重新启用开始按钮
        self.start_button.configure(state="normal")

    def start_processing(self):
        """开始处理文件"""
        if not self.input_dir_var.get():
            messagebox.showerror("错误", "请选择输入目录")
            return
        if not self.output_dir_var.get():
            messagebox.showerror("错误", "请选择输出目录")
            return
        
        # 重置状态
        self.reset_state()
        
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