"""
照片视频整理工具测试包
包含单元测试和集成测试
"""

from pathlib import Path

# 设置测试资源目录
TEST_RESOURCES_DIR = Path(__file__).parent / "resources"
TEST_RESOURCES_DIR.mkdir(exist_ok=True) 