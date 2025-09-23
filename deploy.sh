#!/bin/bash

# Agentic Society Web 部署脚本

echo "🚀 开始部署 Agentic Society Web 应用..."

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

# 检查docker-compose是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose 未安装，请先安装 docker-compose"
    exit 1
fi

# 构建镜像
echo "📦 构建Docker镜像..."
docker-compose build

# 停止并删除旧容器
echo "🔄 清理旧容器..."
docker-compose down

# 启动服务
echo "▶️ 启动服务..."
docker-compose up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "🔍 检查服务状态..."
if curl -s http://localhost:5000 > /dev/null; then
    echo "✅ 部署成功！应用运行在 http://localhost:5000"
else
    echo "❌ 部署失败，请检查日志"
    docker-compose logs
fi

echo ""
echo "📋 常用命令:"
echo "  查看日志: docker-compose logs -f"
echo "  停止服务: docker-compose down"
echo "  重启服务: docker-compose restart"
echo "  查看状态: docker-compose ps"