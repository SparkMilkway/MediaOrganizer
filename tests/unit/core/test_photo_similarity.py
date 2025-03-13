import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import shutil
import os
from PIL import Image
import numpy as np

from src.core import PhotoSimilarityFinder

class TestPhotoSimilarityFinder(unittest.TestCase):
    def setUp(self):
        """测试前创建临时目录"""
        self.temp_dir = tempfile.mkdtemp()
        self.finder = PhotoSimilarityFinder()
        
    def tearDown(self):
        """测试后清理临时目录"""
        shutil.rmtree(self.temp_dir)
        
    def create_test_image(self, filename: str, size=(100, 100), color=(255, 0, 0)) -> Path:
        """创建测试图片"""
        file_path = Path(self.temp_dir) / filename
        img = Image.new('RGB', size, color)
        img.save(file_path)
        return file_path
        
    def test_find_similar_photos_with_identical_images(self):
        """测试查找完全相同的图片"""
        # 创建两张相同的图片
        img1 = self.create_test_image("test1.jpg")
        img2 = self.create_test_image("test2.jpg")
        
        # 查找相似图片
        result = self.finder.find_similar_photos(str(self.temp_dir))
        
        # 验证结果
        self.assertEqual(len(result), 1)  # 应该只有一组相似图片
        for hash_value, files in result.items():
            self.assertEqual(len(files), 2)  # 每组应该有两张图片
            self.assertTrue(str(img1) in files)
            self.assertTrue(str(img2) in files)
            
    def test_find_similar_photos_with_different_images(self):
        """测试查找不同的图片"""
        # 创建两张不同的图片
        self.create_test_image("test1.jpg", color=(255, 0, 0))
        self.create_test_image("test2.jpg", color=(0, 255, 0))
        
        # 查找相似图片
        result = self.finder.find_similar_photos(str(self.temp_dir))
        
        # 验证结果
        self.assertEqual(len(result), 0)  # 不应该找到相似图片
        
    def test_get_file_info(self):
        """测试获取文件信息"""
        # 创建测试图片
        test_file = self.create_test_image("test.jpg")
        
        # 获取文件信息
        info = self.finder.get_file_info(str(test_file))
        
        # 验证结果
        self.assertIn('size', info)
        self.assertIn('path', info)
        self.assertEqual(info['path'], str(test_file))
        self.assertGreater(info['size'], 0)
        
    def test_unsupported_file_type(self):
        """测试处理不支持的文件类型"""
        # 创建文本文件
        test_file = Path(self.temp_dir) / "test.txt"
        test_file.write_text("test")
        
        # 查找相似图片
        result = self.finder.find_similar_photos(str(self.temp_dir))
        
        # 验证结果
        self.assertEqual(len(result), 0)  # 不应该处理文本文件
        
    def test_empty_directory(self):
        """测试空目录"""
        # 直接使用空的临时目录
        result = self.finder.find_similar_photos(str(self.temp_dir))
        
        # 验证结果
        self.assertEqual(len(result), 0)

if __name__ == '__main__':
    unittest.main() 