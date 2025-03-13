#!/usr/bin/env python3
import os
import re
from datetime import datetime
from pathlib import Path
import shutil
from PIL import Image
import piexif
from typing import Optional, Tuple, List
import logging
from tqdm import tqdm

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_creation_date_from_exif(file_path: str) -> Optional[datetime]:
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
        logging.warning(f"无法从{file_path}读取EXIF信息: {str(e)}")
    return None

def get_number_from_filename(filename: str) -> Optional[int]:
    """从文件名中提取数字"""
    match = re.search(r'(\d+)', filename)
    return int(match.group(1)) if match else None

def find_related_files(files: List[str], target_file: str) -> List[str]:
    """找到所有相关的文件（基于文件名中的数字）"""
    target_num = get_number_from_filename(target_file)
    if target_num is None:
        return []
    
    related = []
    for file in files:
        num = get_number_from_filename(file)
        if num is not None and abs(num - target_num) <= 1:
            related.append(file)
    return related

def get_file_stats(files: List[Path]) -> dict:
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

def format_size(size_in_bytes: int) -> str:
    """将字节大小转换为人类可读格式"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_in_bytes < 1024:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024
    return f"{size_in_bytes:.2f} TB"

def generate_report(input_stats: dict, output_stats: dict, output_path: Path) -> None:
    """生成处理报告并保存到文件"""
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
    
    report_path = output_path / "处理报告.txt"
    report_path.write_text(report, encoding='utf-8')
    logging.info(f"统计报告已保存到：{report_path}")

def copy_to_unsorted(file_path: Path, output_path: Path) -> None:
    """将无法处理的文件复制到未分类目录"""
    try:
        # 创建未分类目录
        unsorted_dir = output_path / "Unsorted"
        unsorted_dir.mkdir(parents=True, exist_ok=True)
        
        # 直接复制到Unsorted目录下，不保留原路径结构
        new_path = unsorted_dir / file_path.name
        
        # 如果目标路径已存在同名文件，添加数字后缀
        counter = 1
        while new_path.exists():
            new_path = unsorted_dir / f"{file_path.stem}_{counter}{file_path.suffix}"
            counter += 1
            
        shutil.copy2(str(file_path), str(new_path))
        logging.info(f"已将文件 {file_path.name} 复制到未分类目录")
    except Exception as e:
        logging.error(f"复制文件到未分类目录失败: {str(e)}")

def process_directory(input_dir: str, output_dir: str):
    """处理指定目录下的所有照片和视频文件（包括所有子目录）"""
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
    input_stats = get_file_stats(all_files)
    
    # 按文件名中的数字排序
    all_files = sorted(all_files, key=lambda x: (x.parent, get_number_from_filename(x.name) or 0))

    # 按目录分组处理文件
    files_by_dir = {}
    for file in all_files:
        files_by_dir.setdefault(file.parent, []).append(file)

    # 处理每个目录中的文件
    processed_files = set()
    for dir_path, dir_files in tqdm(files_by_dir.items(), desc="处理目录"):
        logging.info(f"正在处理目录: {dir_path}")
        
        # 处理当前目录中的每个文件
        for file in dir_files:
            if file.name in processed_files:
                continue

            # 找到相关文件（只在同一目录内查找）
            related_files = find_related_files(
                [f.name for f in dir_files], 
                file.name
            )
            creation_date = None

            # 尝试从相关文件中获取创建时间
            for related_file in related_files:
                if creation_date:
                    break
                full_path = str(dir_path / related_file)
                creation_date = get_creation_date_from_exif(full_path)

            if not creation_date:
                logging.warning(f"无法确定{file.name}的创建时间，将此文件及相关文件移至未分类目录")
                # 将所有相关文件都复制到未分类目录
                for related_file in related_files:
                    related_path = dir_path / related_file
                    if related_path.exists():
                        copy_to_unsorted(related_path, output_path)
                        processed_files.add(related_file)
                continue

            # 为所有相关文件设置正确的时间并复制到对应目录
            for related_file in related_files:
                file_path = dir_path / related_file
                if file_path.exists():
                    # 创建目标目录
                    year_dir = output_path / str(creation_date.year)
                    month_dir = year_dir / f"{creation_date.month:02d}"
                    month_dir.mkdir(parents=True, exist_ok=True)

                    # 设置文件时间
                    timestamp = creation_date.timestamp()
                    os.utime(str(file_path), (timestamp, timestamp))

                    # 复制文件
                    new_path = month_dir / related_file
                    shutil.copy2(str(file_path), str(new_path))
                    processed_files.add(related_file)
                    logging.info(f"已复制文件 {related_file}")
    
    # 获取输出目录的统计信息
    output_files = [
        f for f in output_path.rglob('*') 
        if f.suffix.lower() in supported_extensions
    ]
    output_stats = get_file_stats(output_files)
    
    # 生成报告
    generate_report(input_stats, output_stats, output_path)

def main():
    import argparse
    parser = argparse.ArgumentParser(description='整理照片和视频文件')
    parser.add_argument('input_dir', help='输入目录路径')
    parser.add_argument('--output-dir', '-o', 
                      help='输出目录路径（默认为输入目录）',
                      default=None)
    args = parser.parse_args()

    try:
        # 如果没有指定输出目录，使用输入目录
        output_dir = args.output_dir if args.output_dir else args.input_dir
        process_directory(args.input_dir, output_dir)
        print("处理完成！")
    except Exception as e:
        logging.error(f"处理过程中发生错误: {str(e)}")
        raise

if __name__ == '__main__':
    main() 