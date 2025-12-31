# 项目部署指南 - WSL2 Ubuntu

从零开始在 WSL2 Ubuntu 环境中部署 AI Writer 项目。

## 目录
1. [环境准备](#环境准备)
2. [克隆项目](#克隆项目)
3. [安装依赖](#安装依赖)
4. [配置环境](#配置环境)
5. [启动服务](#启动服务)
6. [常见问题](#常见问题)

---

## 环境准备

### 1. 更新系统
```bash
sudo apt update && sudo apt upgrade -y
```

### 2. 安装基础工具
```bash
# 安装 curl, git, wget 等
sudo apt install -y curl git wget build-essential

# 安装 Python 3 和 pip
sudo apt install -y python3 python3-pip python3-venv

# 安装 Node.js 18+ (使用 NodeSource)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# 验证安装
node --version  # 应该显示 v18.x.x
npm --version
python3 --version
```

### 3. 安装 Docker 和 Docker Compose
```bash
# 安装 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 将当前用户添加到 docker 组（避免每次 sudo）
sudo usermod -aG docker $USER

# 安装 Docker Compose
sudo apt install -y docker-compose-plugin

# 重新登录以使 docker 组生效
# 或者执行：newgrp docker

# 验证安装
docker --version
docker compose version
```

### 4. 安装 MinerU（可选但推荐）
```bash
# 方法 1: 使用 pip 安装（推荐）
pip install mineru

# 方法 2: 从源码安装
git clone https://github.com/opendatalab/MinerU.git
cd MinerU
pip install -e .
```

---

## 克隆项目

```bash
# 克隆项目
git clone https://github.com/fsxbmb/Ai-Writer.git
cd Ai-Writer

# 查看项目结构
ls -la
```

---

## 安装依赖

### 1. 后端依赖

```bash
# 进入后端目录
cd backend

# (可选) 创建 Python 虚拟环境
python3 -m venv venv
source venv/bin/activate  # 激活虚拟环境

# 安装依赖
pip install -r requirements.txt

# 如果需要向量搜索功能，安装额外的包
pip install pymilvus sentence-transformers
```

### 2. 前端依赖

```bash
# 返回项目根目录
cd ..

# 进入前端目录
cd frontend

# 安装依赖（如果网络慢，可以使用国内镜像）
npm install

# 或使用淘宝镜像加速
npm install --registry=https://registry.npmmirror.com
```

---

## 配置环境

### 1. 后端环境变量

```bash
# 进入后端目录
cd backend

# 复制环境变量示例文件
cp .env.example .env

# 编辑 .env 文件（可选，使用默认配置也可以）
nano .env
```

`.env` 文件主要配置项：
```env
# FastAPI 配置
APP_NAME=AI Writer Backend
APP_VERSION=0.0.1
DEBUG=True
HOST=0.0.0.0
PORT=8000

# CORS 配置（如果前端地址不同，需要修改）
CORS_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173"]

# 文件存储配置
UPLOAD_DIR=./uploads
PARSE_OUTPUT_DIR=./parsed_data
MAX_UPLOAD_SIZE=104857600  # 100MB

# MinerU 配置
MINERU_BACKEND=pipeline
MINERU_OUTPUT_DIR=./parsed_output
MINERU_LANG=ch
```

### 2. 创建必要的目录

```bash
# 在 backend 目录下创建所需目录
mkdir -p uploads parsed_output parsed_data
```

---

## 启动服务

### 方式一：完整启动（包含 Milvus 向量数据库）

如果你需要使用向量搜索和 RAG 功能，需要先启动 Milvus 数据库：

#### 1. 启动 Milvus（可选）

```bash
# 从项目根目录进入 milvus 目录
cd milvus

# 启动 Milvus 服务
docker compose up -d

# 查看服务状态
docker compose ps

# 等待服务启动（约 30-60 秒）
# 可以查看日志确认启动成功
docker compose logs -f standalone
# 看到 "successfully started and ready to serve" 即启动成功
```

Milvus 服务端口：
- 19530: Milvus 服务端口
- 9091: 管理界面
- 9001: MinIO 控制台

#### 2. 启动后端

```bash
# 打开新终端，进入 backend 目录
cd Ai-Writer/backend

# 如果使用了虚拟环境，激活它
source venv/bin/activate

# 启动后端服务
python -m app.main

# 后端将运行在 http://localhost:8000
# API 文档：http://localhost:8000/docs
```

#### 3. 启动前端

```bash
# 打开新终端，进入 frontend 目录
cd Ai-Writer/frontend

# 启动开发服务器
npm run dev

# 前端将运行在 http://localhost:5173
```

### 方式二：简化启动（不使用向量数据库）

如果不需要 RAG 知识问答功能，可以跳过 Milvus，直接启动后端和前端：

```bash
# 终端 1: 启动后端
cd Ai-Writer/backend
source venv/bin/activate  # 如果使用虚拟环境
python -m app.main

# 终端 2: 启动前端
cd Ai-Writer/frontend
npm run dev
```

---

## 访问应用

启动成功后，在浏览器中访问：

- **前端应用**: http://localhost:5173
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **Milvus 管理界面** (可选): http://localhost:9091

---

## 常见问题

### 1. MinerU 未安装或不可用

**问题**: 后端启动时提示 MinerU 未找到

**解决方案**:
```bash
# 方案 1: 安装 MinerU
pip install mineru

# 方案 2: 如果已安装但路径不对，创建符号链接
ln -s /path/to/MinerU ../MinerU
```

### 2. Docker 权限问题

**问题**: 运行 docker 命令时提示 permission denied

**解决方案**:
```bash
# 将用户添加到 docker 组
sudo usermod -aG docker $USER

# 重新登录或执行
newgrp docker
```

### 3. Milvus 启动失败

**问题**: Milvus 容器启动失败或无法连接

**解决方案**:
```bash
# 查看容器日志
docker compose -f milvus/docker-compose.yml logs

# 重启服务
docker compose -f milvus/docker-compose.yml restart

# 完全清理后重新启动
docker compose -f milvus/docker-compose.yml down -v
docker compose -f milvus/docker-compose.yml up -d
```

### 4. 端口被占用

**问题**: 端口 8000、5173 或 19530 已被占用

**解决方案**:
```bash
# 查看端口占用情况
sudo lsof -i :8000
sudo lsof -i :5173
sudo lsof -i :19530

# 杀死占用进程
sudo kill -9 <PID>

# 或者修改配置文件中的端口号
```

### 5. npm install 速度慢或失败

**解决方案**:
```bash
# 使用国内镜像
npm config set registry https://registry.npmmirror.com

# 或安装时指定镜像
npm install --registry=https://registry.npmmirror.com
```

### 6. Python 依赖安装失败

**解决方案**:
```bash
# 升级 pip
pip install --upgrade pip

# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 或者逐个安装，查看具体错误
```

### 7. CORS 错误

**问题**: 前端无法连接后端，浏览器提示 CORS 错误

**解决方案**:
检查 `backend/.env` 文件中的 `CORS_ORIGINS` 配置：
```env
# 确保包含前端地址
CORS_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173"]
```

### 8. WSL2 网络访问问题

**问题**: Windows 浏览器无法访问 WSL2 中的服务

**解决方案**:
```bash
# 获取 WSL2 的 IP 地址
hostname -I

# 在 Windows 浏览器中使用 WSL2 的 IP 访问
# 例如：http://172.x.x.x:5173

# 或者使用 localhost（WSL2 会自动转发）
# 确保没有防火墙拦截
```

---

## 开发模式 vs 生产模式

### 开发模式（当前配置）
- 前端：`npm run dev` - Vite 开发服务器，支持热更新
- 后端：`python -m app.main` - FastAPI 开发模式，显示详细错误信息

### 生产模式（推荐）

#### 前端构建
```bash
cd frontend
npm run build
# 生成 dist/ 目录，包含静态文件
```

#### 后端启动（使用 uvicorn）
```bash
cd backend
# 生产模式配置
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 性能优化建议

1. **使用虚拟环境**: Python 项目建议使用虚拟环境隔离依赖
2. **PM2 管理进程**: 使用 PM2 管理 Node.js 和 Python 进程
   ```bash
   npm install -g pm2
   pm2 start "npm run dev" --name ai-writer-frontend
   ```
3. **Nginx 反向代理**: 生产环境建议使用 Nginx
4. **数据库优化**: 大量数据时考虑使用 PostgreSQL 替代 JSON 文件

---

## 更新项目

```bash
# 拉取最新代码
git pull origin main

# 更新后端依赖
cd backend
pip install -r requirements.txt --upgrade

# 更新前端依赖
cd ../frontend
npm install

# 重启服务
```

---

## 技术支持

如有问题，请查看：
- GitHub Issues: https://github.com/fsxbmb/Ai-Writer/issues
- API 文档: http://localhost:8000/docs
- MinerU 文档: https://github.com/opendatalab/MinerU
- Milvus 文档: https://milvus.io/docs

---

## 许可证

MIT
