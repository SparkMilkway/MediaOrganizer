import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging

from .date_extractor import DateExtractor
from .utils import format_size, get_number_from_filename

class FileProcessor:
    """文件处理核心类"""
    
    def __init__(self):
        self.supported_formats = {
            'images': {'.jpg', '.jpeg', '.png', '.heic', '.heif'},
            'videos': {'.mp4', '.mov', '.MOV'}
        }
        self.date_extractor = DateExtractor()
        
    def get_supported_files(self, directory: Path) -> List[Path]:
        """获取目录下所有支持的文件"""
        supported_extensions = set().union(*self.supported_formats.values())
        return [
            f for f in directory.rglob('*')
            if f.suffix.lower() in supported_extensions
        ]
        
    def get_file_stats(self, files: List[Path]) -> Dict[str, Dict[str, int]]:
        """统计文件数量和大小"""
        stats = {
            'images': {'count': 0, 'size': 0},
            'videos': {'count': 0, 'size': 0}
        }
        
        for file in files:
            size = file.stat().st_size
            ext = file.suffix.lower()
            
            if ext in self.supported_formats['images']:
                stats['images']['count'] += 1
                stats['images']['size'] += size
            elif ext in self.supported_formats['videos']:
                stats['videos']['count'] += 1
                stats['videos']['size'] += size
                
        return stats
        
    def move_to_unsorted(self, file_path: Path, output_base: Path) -> None:
        """将文件移动到未分类目录"""
        try:
            unsorted_dir = output_base / "Unsorted"
            unsorted_dir.mkdir(parents=True, exist_ok=True)
            
            new_path = unsorted_dir / file_path.name
            counter = 1
            while new_path.exists():
                new_path = unsorted_dir / f"{file_path.stem}_{counter}{file_path.suffix}"
                counter += 1
                
            shutil.copy2(str(file_path), str(new_path))
            logging.info(f"已将文件 {file_path.name} 复制到未分类目录")
        except Exception as e:
            logging.error(f"复制文件到未分类目录失败: {str(e)}")
            
    def process_file(self, file_path: Path, output_base: Path, creation_date: Optional[datetime] = None) -> bool:
        """处理单个文件"""
        try:
            if not creation_date:
                creation_date = self.date_extractor.get_creation_date(file_path)
                
            if not creation_date:
                self.move_to_unsorted(file_path, output_base)
                return False
                
            # 创建目标目录
            year_dir = output_base / str(creation_date.year)
            month_dir = year_dir / f"{creation_date.month:02d}"
            month_dir.mkdir(parents=True, exist_ok=True)
            
            # 设置文件时间
            timestamp = creation_date.timestamp()
            os.utime(str(file_path), (timestamp, timestamp))
            
            # 复制文件
            new_path = month_dir / file_path.name
            counter = 1
            while new_path.exists():
                new_path = month_dir / f"{file_path.stem}_{counter}{file_path.suffix}"
                counter += 1
                
            shutil.copy2(str(file_path), str(new_path))
            logging.info(f"已处理文件: {file_path.name}")
            return True
            
        except Exception as e:
            logging.error(f"处理文件 {file_path} 时出错: {str(e)}")
            return False
            
    def process_directory(self, input_dir: Path, output_dir: Path, 
                         progress_callback: Optional[callable] = None) -> Dict[str, Any]:
        """处理整个目录"""
        if not input_dir.exists():
            raise ValueError(f"输入目录 {input_dir} 不存在")
            
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 获取所有文件
        all_files = self.get_supported_files(input_dir)
        if not all_files:
            logging.warning("未找到支持的文件")
            return {'processed': 0, 'total': 0, 'success': 0}
            
        # 获取输入统计
        input_stats = self.get_file_stats(all_files)
        
        # 按目录分组处理文件
        files_by_dir = {}
        for file in all_files:
            files_by_dir.setdefault(file.parent, []).append(file)
            
        processed_count = 0
        success_count = 0
        total_files = len(all_files)
        
        # 处理每个目录
        for dir_path, dir_files in files_by_dir.items():
            logging.info(f"正在处理目录: {dir_path}")
            
            # 按文件名排序
            sorted_files = sorted(dir_files, 
                                key=lambda x: get_number_from_filename(x.name) or float('inf'))
            
            for file in sorted_files:
                if self.process_file(file, output_dir):
                    success_count += 1
                processed_count += 1
                
                if progress_callback:
                    progress_callback(processed_count / total_files, 
                                   f"已处理: {processed_count}/{total_files}")
                    
        # 获取输出统计
        output_files = self.get_supported_files(output_dir)
        output_stats = self.get_file_stats(output_files)
        
        return {
            'processed': processed_count,
            'success': success_count,
            'total': total_files,
            'input_stats': input_stats,
            'output_stats': output_stats
        } 