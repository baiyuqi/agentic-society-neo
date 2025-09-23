# Agentic Society Web 部署指南

## 🐳 Docker 部署

### 前提条件
- Docker 已安装
- docker-compose 已安装

### 快速部署

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd agentic-society-neo
   ```

2. **一键部署**
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```

3. **手动部署**
   ```bash
   # 构建镜像
   docker-compose build

   # 启动服务
   docker-compose up -d
   ```

### 访问应用
- 本地访问: http://localhost:5000
- 网络访问: http://<服务器IP>:5000

## 🔧 管理命令

```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 更新部署（代码更新后）
docker-compose down
docker-compose build
docker-compose up -d
```

## ⚙️ 环境配置

### 生产环境变量
在 `docker-compose.yml` 中设置：

```yaml
environment:
  - FLASK_ENV=production
  - DATABASE_URL=postgresql://user:pass@host/db
```

### 数据持久化
数据目录自动挂载到 `./data`，确保重启后数据不丢失。

## 🚀 生产环境部署

### 云服务器部署
1. 上传项目文件到服务器
2. 安装 Docker 和 docker-compose
3. 运行部署脚本

### 容器注册表（可选）
```bash
# 构建并推送镜像
docker build -t your-registry/agentic-society:latest .
docker push your-registry/agentic-society:latest

# 使用镜像部署
docker run -p 5000:5000 your-registry/agentic-society:latest
```

## 📊 监控和日志

### 日志查看
```bash
# 实时查看日志
docker-compose logs -f agentic-society-web

# 查看最近100行日志
docker-compose logs --tail=100 agentic-society-web
```

### 健康检查
应用启动后，访问 `/` 端点检查服务状态。

## 🔒 安全建议

1. 使用 HTTPS 反向代理（如 Nginx）
2. 设置防火墙规则
3. 定期更新依赖包
4. 监控容器资源使用

## 🆘 故障排除

### 常见问题

**端口被占用**
```bash
# 检查端口占用
netstat -tulpn | grep 5000

# 修改端口（在 docker-compose.yml 中）
ports:
  - "8080:5000"
```

**构建失败**
```bash
# 清理缓存重新构建
docker system prune
docker-compose build --no-cache
```

**权限问题**
```bash
# 给部署脚本执行权限
chmod +x deploy.sh
```