"""照片视频整理工具的GUI模块"""

# 首先导入基础组件
from .base_tab import BaseTab
from .batch_tab import BatchTab
from .manual_tab import ManualTab
from .similarity_tab import SimilarityTab

# 然后导入主窗口
from .main_window import PhotoOrganizerGUI

__all__ = [
    'BaseTab',
    'BatchTab',
    'ManualTab',
    'SimilarityTab',
    'PhotoOrganizerGUI'
] 