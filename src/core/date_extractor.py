import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, List
import logging
from PIL import Image
import piexif

class DateExtractor:
    """日期提取类"""
    
    def __init__(self):
        self.date_patterns = [
            r'(20\d{2})[/_-]?(\d{2})[/_-]?(\d{2})',  # 2023-01-01, 2023_01_01, 20230101
            r'(19\d{2})[/_-]?(\d{2})[/_-]?(\d{2})',  # 1999-01-01, 1999_01_01, 19990101
        ]
        
    def get_creation_date_from_exif(self, file_path: str) -> Optional[datetime]:
        """从EXIF信息中获取创建时间"""
        try:
            if file_path.lower().endswith(('.jpg', '.jpeg', '.png')):
                with Image.open(file_path) as img:
                    if 'exif' in img.info:
                        exif_dict = piexif.load(img.info['exif'])
                        if piexif.ExifIFD.DateTimeOriginal in exif_dict['Exif']:
                            date_str = exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal].decode('utf-8')
                            return datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
        except Exception as e:
            logging.error(f"无法从{file_path}读取EXIF信息: {str(e)}")
        return None
        
    def get_date_from_path(self, file_path: Path) -> Optional[datetime]:
        """从文件路径推断日期"""
        try:
            path_str = str(file_path)
            for pattern in self.date_patterns:
                match = re.search(pattern, path_str)
                if match:
                    year, month, day = map(int, match.groups())
                    return datetime(year, month, day)
        except Exception as e:
            logging.error(f"从路径推断日期失败: {str(e)}")
        return None
        
    def get_date_from_related_files(self, current_file: Path, related_files: List[Path]) -> Optional[datetime]:
        """从相关文件中获取日期"""
        try:
            all_files = sorted(related_files)
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
        except Exception as e:
            logging.error(f"从相关文件获取日期失败: {str(e)}")
        return None
        
    def get_creation_date(self, file_path: Path, related_files: Optional[List[Path]] = None) -> Optional[datetime]:
        """尝试所有方法获取创建时间"""
        # 1. 从EXIF获取
        date = self.get_creation_date_from_exif(str(file_path))
        if date:
            return date
            
        # 2. 从相关文件获取
        if related_files:
            date = self.get_date_from_related_files(file_path, related_files)
            if date:
                return date
                
        # 3. 从路径推断
        date = self.get_date_from_path(file_path)
        if date:
            return date
            
        return None 