#!/bin/bash

# 激活虚拟环境
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "错误：未找到虚拟环境(.venv)，请先运行 python -m venv .venv 创建虚拟环境"
    exit 1
fi

# 检查依赖是否已安装
if ! python -c "import customtkinter" &> /dev/null; then
    echo "正在安装依赖..."
    pip install -r requirements.txt
fi

# 启动GUI程序
# 使用python -c来执行代码，避免直接导入模块
python -c "from src.gui import PhotoOrganizerGUI; app = PhotoOrganizerGUI(); app.mainloop()"
