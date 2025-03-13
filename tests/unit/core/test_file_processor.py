import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
from datetime import datetime
import shutil
import tempfile
import os

from src.core import FileProcessor

class TestFileProcessor(unittest.TestCase):
    def setUp(self):
        """测试前创建临时目录"""
        self.temp_dir = tempfile.mkdtemp()
        self.input_dir = Path(self.temp_dir) / "input"
        self.output_dir = Path(self.temp_dir) / "output"
        self.input_dir.mkdir()
        self.output_dir.mkdir()
        self.processor = FileProcessor()
        
    def tearDown(self):
        """测试后清理临时目录"""
        shutil.rmtree(self.temp_dir)
        
    def create_test_file(self, filename: str, content: bytes = b"test") -> Path:
        """创建测试文件"""
        file_path = self.input_dir / filename
        file_path.write_bytes(content)
        return file_path
        
    def test_process_file(self):
        """测试处理单个文件"""
        # 创建测试文件
        test_file = self.create_test_file("test.jpg")
        test_date = datetime(2024, 3, 13, 12, 0)
        
        # 处理文件
        result = self.processor.process_file(test_file, self.output_dir, test_date)
        
        # 验证结果
        self.assertTrue(result)
        expected_path = self.output_dir / "2024" / "03" / "test.jpg"
        self.assertTrue(expected_path.exists())
        
    def test_process_file_with_duplicate_name(self):
        """测试处理同名文件"""
        # 创建两个同名文件
        test_file1 = self.create_test_file("test.jpg", b"content1")
        test_file2 = self.create_test_file("test.jpg", b"content2")
        test_date = datetime(2024, 3, 13, 12, 0)
        
        # 处理文件
        self.processor.process_file(test_file1, self.output_dir, test_date)
        self.processor.process_file(test_file2, self.output_dir, test_date)
        
        # 验证结果
        month_dir = self.output_dir / "2024" / "03"
        self.assertTrue((month_dir / "test.jpg").exists())
        self.assertTrue((month_dir / "test_1.jpg").exists())
        
    def test_process_unsupported_file(self):
        """测试处理不支持的文件类型"""
        test_file = self.create_test_file("test.txt")
        test_date = datetime(2024, 3, 13, 12, 0)
        
        # 处理文件
        result = self.processor.process_file(test_file, self.output_dir, test_date)
        
        # 验证结果
        self.assertFalse(result)
        self.assertFalse(any(self.output_dir.iterdir()))
        
    @patch('src.core.file_processor.PhotoSimilarityFinder')
    def test_find_similar_photos(self, mock_finder):
        """测试查找相似照片"""
        # 设置模拟对象
        mock_finder_instance = MagicMock()
        mock_finder.return_value = mock_finder_instance
        mock_finder_instance.find_similar_photos.return_value = {
            "hash1": ["photo1.jpg", "photo2.jpg"]
        }
        
        # 创建测试文件
        self.create_test_file("photo1.jpg")
        self.create_test_file("photo2.jpg")
        
        # 执行查找
        result = self.processor.find_similar_photos(str(self.input_dir))
        
        # 验证结果
        self.assertEqual(len(result), 1)
        self.assertEqual(len(result["hash1"]), 2)
        mock_finder_instance.find_similar_photos.assert_called_once()

if __name__ == '__main__':
    unittest.main() 