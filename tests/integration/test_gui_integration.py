import unittest
from pathlib import Path
import tempfile
import shutil
import os
from datetime import datetime
import threading
import time

from src.gui import PhotoOrganizerGUI
from src.core import FileProcessor

class TestGUIIntegration(unittest.TestCase):
    def setUp(self):
        """测试前创建临时目录和测试文件"""
        self.temp_dir = tempfile.mkdtemp()
        self.input_dir = Path(self.temp_dir) / "input"
        self.output_dir = Path(self.temp_dir) / "output"
        self.input_dir.mkdir()
        self.output_dir.mkdir()
        
        # 创建测试文件
        self.create_test_files()
        
        # 创建GUI实例
        self.app = PhotoOrganizerGUI()
        
    def tearDown(self):
        """测试后清理"""
        try:
            self.app.quit()
        except:
            pass
        shutil.rmtree(self.temp_dir)
        
    def create_test_files(self):
        """创建测试文件"""
        # 创建一些测试图片
        for i in range(3):
            file_path = self.input_dir / f"test{i}.jpg"
            with open(file_path, "wb") as f:
                f.write(b"test image content")
                
    def test_batch_processing(self):
        """测试批量处理功能"""
        def run_test():
            # 设置输入输出目录
            self.app.tab_batch.input_dir_var.set(str(self.input_dir))
            self.app.tab_batch.output_dir_var.set(str(self.output_dir))
            
            # 启动处理
            self.app.tab_batch.start_processing()
            
            # 等待处理完成
            time.sleep(2)
            
            # 验证结果
            self.assertTrue(any(self.output_dir.iterdir()))
            self.app.quit()
            
        # 在新线程中运行测试
        thread = threading.Thread(target=run_test)
        thread.daemon = True
        thread.start()
        
        # 运行主循环
        self.app.mainloop()
        
    def test_manual_processing(self):
        """测试手动处理功能"""
        def run_test():
            # 选择文件
            test_file = str(next(self.input_dir.iterdir()))
            self.app.manual_tab.manual_files = [test_file]
            self.app.manual_tab.manual_output_dir_var.set(str(self.output_dir))
            
            # 设置日期
            now = datetime.now()
            self.app.manual_tab.year_var.set(str(now.year))
            self.app.manual_tab.month_var.set(str(now.month))
            self.app.manual_tab.day_var.set(str(now.day))
            
            # 启动处理
            self.app.manual_tab.process_files()
            
            # 等待处理完成
            time.sleep(2)
            
            # 验证结果
            self.assertTrue(any(self.output_dir.iterdir()))
            self.app.quit()
            
        # 在新线程中运行测试
        thread = threading.Thread(target=run_test)
        thread.daemon = True
        thread.start()
        
        # 运行主循环
        self.app.mainloop()
        
    def test_similarity_search(self):
        """测试相似照片查找功能"""
        def run_test():
            # 设置输入目录
            self.app.similarity_tab.similarity_input_path.set(str(self.input_dir))
            
            # 启动查找
            self.app.similarity_tab.start_search()
            
            # 等待处理完成
            time.sleep(2)
            
            # 验证结果（这里主要验证不会崩溃）
            self.app.quit()
            
        # 在新线程中运行测试
        thread = threading.Thread(target=run_test)
        thread.daemon = True
        thread.start()
        
        # 运行主循环
        self.app.mainloop()

if __name__ == '__main__':
    unittest.main() 