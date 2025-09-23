# 使用Python官方镜像
FROM python:3.11-alpine

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apk update && apk add --no-cache \
    gcc \
    g++ \
    musl-dev \
    linux-headers

# 复制项目文件
COPY . .

# 安装Poetry
RUN pip install poetry

# 配置Poetry不创建虚拟环境（在容器中不需要）
RUN poetry config virtualenvs.create false

# 安装项目依赖
RUN poetry install --no-dev

# 暴露端口
EXPOSE 5000

# 设置环境变量
ENV PYTHONPATH=/app
ENV FLASK_ENV=production

# 启动命令
CMD ["python", "web/app.py"]