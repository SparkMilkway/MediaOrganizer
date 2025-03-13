import re
from typing import Optional

def format_size(size_in_bytes: int) -> str:
    """将字节大小转换为人类可读格式"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_in_bytes < 1024:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024
    return f"{size_in_bytes:.2f} TB"

def get_number_from_filename(filename: str) -> Optional[int]:
    """从文件名中提取数字"""
    match = re.search(r'(\d+)', filename)
    return int(match.group(1)) if match else None

def generate_report(input_stats: dict, output_stats: dict) -> str:
    """生成处理报告"""
    report = "照片视频处理统计报告\n"
    report += "=" * 50 + "\n\n"
    
    report += "输入目录统计：\n"
    report += f"图片数量：{input_stats['images']['count']} 个\n"
    report += f"图片大小：{format_size(input_stats['images']['size'])}\n"
    report += f"视频数量：{input_stats['videos']['count']} 个\n"
    report += f"视频大小：{format_size(input_stats['videos']['size'])}\n"
    report += f"总文件数：{input_stats['images']['count'] + input_stats['videos']['count']} 个\n"
    report += f"总大小：{format_size(input_stats['images']['size'] + input_stats['videos']['size'])}\n\n"
    
    report += "输出目录统计：\n"
    report += f"图片数量：{output_stats['images']['count']} 个\n"
    report += f"图片大小：{format_size(output_stats['images']['size'])}\n"
    report += f"视频数量：{output_stats['videos']['count']} 个\n"
    report += f"视频大小：{format_size(output_stats['videos']['size'])}\n"
    report += f"总文件数：{output_stats['images']['count'] + output_stats['videos']['count']} 个\n"
    report += f"总大小：{format_size(output_stats['images']['size'] + output_stats['videos']['size'])}\n"
    
    return report 