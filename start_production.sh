#!/bin/bash

# Agentic Society Web 生产环境启动脚本

echo "🚀 启动 Agentic Society Web 生产环境..."

# 检查是否在项目目录
if [ ! -f "pyproject.toml" ]; then
    echo "❌ 请在项目根目录运行此脚本"
    exit 1
fi

# 检查Poetry是否安装
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry 未安装，请先安装 Poetry"
    exit 1
fi

# 安装依赖（如果需要）
echo "📦 检查依赖..."
poetry install --no-dev

# 启动web服务
echo "▶️ 启动Web服务..."
cd web
poetry run python app.py

echo ""
echo "✅ 服务已启动"
echo "🌐 访问地址: http://127.0.0.1:5000"
echo "🌐 网络访问: http://10.22.160.77:5000"
echo ""
echo "按 Ctrl+C 停止服务"