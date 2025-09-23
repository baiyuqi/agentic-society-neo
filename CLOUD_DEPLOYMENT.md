# ☁️ 云平台部署指南

## 🚀 快速部署方案

### 方案1: Heroku (最简单)
**步骤:**
1. 注册 Heroku 账号
2. 安装 Heroku CLI
3. 执行以下命令：

```bash
# 登录Heroku
heroku login

# 创建应用
heroku create agentic-society-web

# 设置构建包
heroku buildpacks:add heroku/python

# 部署
git push heroku main

# 查看日志
heroku logs --tail
```

**访问地址:** https://agentic-society-web.herokuapp.com

### 方案2: Railway (推荐)
**步骤:**
1. 访问 https://railway.app
2. 连接 GitHub 仓库
3. 自动部署

**优势:**
- 免费额度充足
- 自动 HTTPS
- 简单易用

### 方案3: Vercel (适合前端)
**步骤:**
1. 访问 https://vercel.com
2. 导入 GitHub 仓库
3. 配置构建命令

## 🔧 详细部署指南

### AWS Elastic Beanstalk
```bash
# 安装 EB CLI
pip install awsebcli

# 初始化
eb init -p python-3.11 agentic-society-app

# 创建环境
eb create agentic-society-env

# 部署
eb deploy
```

### Google Cloud Run
```bash
# 设置项目
gcloud config set project YOUR_PROJECT_ID

# 构建镜像
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/agentic-society

# 部署到 Cloud Run
gcloud run deploy agentic-society \
  --image gcr.io/YOUR_PROJECT_ID/agentic-society \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### Microsoft Azure App Service
```bash
# 创建资源组
az group create --name agentic-society-rg --location eastus

# 创建应用服务计划
az appservice plan create --name agentic-society-plan --resource-group agentic-society-rg --sku B1

# 创建Web应用
az webapp create --resource-group agentic-society-rg --plan agentic-society-plan --name agentic-society-app

# 部署
az webapp up --name agentic-society-app --resource-group agentic-society-rg
```

## ⚙️ 环境配置

### 生产环境变量
在云平台设置以下环境变量：

```bash
FLASK_ENV=production
PYTHONPATH=/app
DATABASE_URL=你的数据库连接字符串
```

### 数据库配置
如果需要外部数据库：

**Heroku PostgreSQL:**
```bash
heroku addons:create heroku-postgresql:hobby-dev
```

**Railway PostgreSQL:**
- 在 Railway 仪表板添加 PostgreSQL 服务
- 自动获取连接字符串

## 📊 监控和日志

### Heroku 监控
```bash
# 查看应用指标
heroku apps:info

# 查看日志
heroku logs --tail

# 扩展资源
heroku ps:scale web=2
```

### 自定义域名
```bash
# 添加自定义域名
heroku domains:add www.yourdomain.com

# 配置DNS
# 将CNAME记录指向 your-app.herokuapp.com
```

## 💰 成本估算

### 免费方案
- **Heroku:** Hobby Dyno (免费，有使用限制)
- **Railway:** 每月$5免费额度
- **Vercel:** 免费套餐
- **Netlify:** 免费套餐

### 生产方案
- **小型应用:** $7-25/月
- **中型应用:** $25-100/月
- **大型应用:** $100+/月

## 🛡️ 安全配置

### SSL/HTTPS
所有主流云平台自动提供：
- Heroku: 自动SSL
- Railway: 自动HTTPS
- Vercel: 自动SSL

### 环境变量保护
```bash
# 设置敏感信息
heroku config:set SECRET_KEY=your-secret-key
heroku config:set DATABASE_URL=your-db-url
```

## 🔄 持续部署

### GitHub Actions 自动化
推送代码到 main 分支时自动部署：

```yaml
# 已在 .github/workflows/deploy.yml 中配置
```

### 手动部署命令
```bash
# Heroku
git push heroku main

# Railway
railway deploy

# Vercel
vercel --prod
```

## 🆘 故障排除

### 常见问题

**应用无法启动**
```bash
# 检查日志
heroku logs --tail

# 检查依赖
heroku run poetry install
```

**端口冲突**
- 确保应用监听 `$PORT` 环境变量
- 修改 `web/app.py` 中的端口配置

**静态文件404**
- 检查静态文件路径
- 验证 Flask 静态文件配置

### 性能优化

**启用Gzip压缩**
```python
# 在Flask应用中
from flask import gzip
app = Flask(__name__)
gzip = Gzip(app)
```

**缓存配置**
```python
# 设置缓存头
@app.after_request
def add_header(response):
    response.cache_control.max_age = 300
    return response
```

## 📞 支持资源

- [Heroku文档](https://devcenter.heroku.com/)
- [Railway文档](https://docs.railway.app/)
- [Vercel文档](https://vercel.com/docs)
- [AWS文档](https://aws.amazon.com/documentation/)

选择最适合你需求的平台开始部署吧！