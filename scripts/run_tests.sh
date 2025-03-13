#!/bin/bash

# 激活虚拟环境
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "错误：未找到虚拟环境(.venv)，请先运行 python -m venv .venv 创建虚拟环境"
    exit 1
fi

# 检查依赖是否已安装
if ! python -c "import pytest" &> /dev/null; then
    echo "正在安装测试依赖..."
    pip install pytest pytest-cov
fi

# 运行测试
echo "开始运行测试..."
python -m pytest tests/ -v --cov=src --cov-report=term-missing 