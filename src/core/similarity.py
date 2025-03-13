import os
from PIL import Image
import imagehash
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional
import logging

class PhotoSimilarityFinder:
    """相似图片查找类"""
    
    def __init__(self):
        self.hash_dict = defaultdict(list)
        self.supported_formats = {'.jpg', '.jpeg', '.png'}
        
    def compute_hash(self, image_path: str) -> Optional[str]:
        """计算图片的感知哈希值"""
        try:
            with Image.open(image_path) as img:
                # 使用感知哈希，对图片大小和小的修改不敏感
                return str(imagehash.average_hash(img))
        except Exception as e:
            logging.error(f"处理文件 {image_path} 时出错: {str(e)}")
            return None
            
    def find_similar_photos(self, directory: str, hash_threshold: int = 5) -> Dict[str, List[str]]:
        """
        递归搜索目录中的相似照片
        :param directory: 要搜索的目录
        :param hash_threshold: 哈希差异阈值，越小表示要求越相似
        :return: 字典，键为哈希值，值为相似照片的路径列表
        """
        self.hash_dict.clear()
        
        for root, _, files in os.walk(directory):
            for filename in files:
                if Path(filename).suffix.lower() in self.supported_formats:
                    file_path = os.path.join(root, filename)
                    file_hash = self.compute_hash(file_path)
                    if file_hash:
                        self.hash_dict[file_hash].append(file_path)
        
        # 只返回有相似照片的组
        return {k: v for k, v in self.hash_dict.items() if len(v) > 1}
    
    @staticmethod
    def get_file_info(file_path: str) -> Dict[str, any]:
        """获取文件信息"""
        stat = os.stat(file_path)
        return {
            'size': stat.st_size,
            'created': stat.st_ctime,
            'modified': stat.st_mtime,
            'path': file_path,
            'name': os.path.basename(file_path)
        } 