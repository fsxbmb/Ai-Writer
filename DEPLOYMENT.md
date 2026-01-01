# AI Writer 项目部署指南 - WSL2 Ubuntu

**适用于笔记本电脑的完整部署指南 - 包含本地 LLM 配置**

---

## 📋 目录

1. [快速开始](#快速开始) - 5分钟快速部署
2. [完整部署步骤](#完整部署步骤) - 详细安装指南
3. [Ollama 本地 LLM 配置](#ollama-本地-llm-配置) - 可选功能
4. [WSL2 专用配置](#wsl2-专用配置)
5. [笔记本性能优化](#笔记本性能优化)
6. [功能说明](#功能说明)
7. [常见问题解决](#常见问题解决)

---

## 🚀 快速开始

**适合已安装 WSL2 Ubuntu 的用户**

### 基础模式（推荐新手）

```bash
# 1. 克隆项目
git clone https://github.com/fsxbmb/Ai-Writer.git
cd Ai-Writer

# 2. 安装后端依赖
cd backend
pip install -r requirements.txt
cp .env.example .env

# 3. 安装前端依赖
cd ../frontend
npm install

# 4. 启动服务
# 终端1: cd backend && python -m app.main
# 终端2: cd frontend && npm run dev

# 5. 访问应用
# 浏览器打开: http://localhost:5173
```

### 完整模式（含 Ollama 和 Milvus）

```bash
# 额外步骤：安装 Ollama（用于本地 LLM）
curl -fsSL https://ollama.com/install.sh | sh

# 启动 Ollama 服务
ollama serve &

# 下载模型（示例：Qwen2.5）
ollama pull qwen2.5:7b

# 启动 Milvus（用于向量搜索）
cd milvus && docker compose up -d
```

---

## 📦 完整部署步骤

### 第一步：在 Windows 上安装 WSL2

#### 1.1 检查系统要求
- Windows 10 版本 2004 或更高（内部版本 19041 或更高）
- 或 Windows 11
- 至少 8GB RAM（推荐 16GB，使用本地 LLM 建议 32GB）
- 至少 20GB 可用磁盘空间

#### 1.2 安装 WSL2
```powershell
# 在 PowerShell (管理员) 中运行
wsl --install

# 重启计算机后，WSL 会自动安装 Ubuntu
# 设置用户名和密码
```

#### 1.3 更新 WSL2（可选但推荐）
```powershell
wsl --update
```

---

### 第二步：配置 WSL2 Ubuntu

#### 2.1 更新系统
```bash
# 进入 WSL2 Ubuntu
sudo apt update && sudo apt upgrade -y
```

#### 2.2 安装基础工具
```bash
# 安装必要工具
sudo apt install -y curl git wget build-essential vim

# 安装 Python 3 和 pip
sudo apt install -y python3 python3-pip python3-venv

# 安装 Node.js 18+
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# 验证安装
echo "Node.js: $(node --version)"
echo "npm: $(npm --version)"
echo "Python: $(python3 --version)"
```

#### 2.3 安装文档转换依赖（可选）

如果需要使用文档导出功能：

```bash
# 安装 wkhtmltopdf（用于 HTML 转 PDF）
sudo apt install -y wkhtmltopdf

# 安装 Pandoc（用于文档格式转换）
sudo apt install -y pandoc
```

#### 2.4 配置 Git（可选）
```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

---

### 第三步：安装 Docker（可选，用于 Milvus）

**⚠️ 注意：Docker 会占用较多资源，如果不需要向量搜索功能可以跳过**

```bash
# 安装 Docker
curl -fsSL https://get.docker.com | sudo sh

# 将当前用户添加到 docker 组
sudo usermod -aG docker $USER

# 重新登录 WSL 使配置生效
# 在 PowerShell 中运行: wsl --shutdown
# 然后重新打开 WSL

# 验证安装
docker --version
```

---

### 第四步：安装 Ollama（可选，用于本地 LLM）

**⚠️ 注意：Ollama 需要 GPU 支持（推荐）或充足的 CPU 资源**

#### 4.1 安装 Ollama

```bash
# 官方安装脚本
curl -fsSL https://ollama.com/install.sh | sh

# 验证安装
ollama --version
```

#### 4.2 下载模型

```bash
# 启动 Ollama 服务
ollama serve &

# 等待服务启动后，下载模型
# 小模型（适合 8-16GB RAM）
ollama pull qwen2.5:3b

# 中等模型（推荐，适合 16-32GB RAM）
ollama pull qwen2.5:7b
ollama pull qwen2.5:14b

# 大模型（适合 32GB+ RAM）
ollama pull qwen2.5:32b

# 查看已安装的模型
ollama list
```

#### 4.3 测试 Ollama

```bash
# 测试对话
ollama run qwen2.5:7b "你好，请介绍一下自己"

# 查看模型信息
ollama show qwen2.5:7b
```

---

### 第五步：克隆项目

```bash
# 选择项目安装位置（推荐放在用户目录下）
cd ~

# 克隆项目
git clone https://github.com/fsxbmb/Ai-Writer.git
cd Ai-Writer

# 查看项目结构
ls -la
```

---

### 第六步：安装项目依赖

#### 6.1 后端安装

```bash
# 进入后端目录
cd backend

# 创建 Python 虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate

# 升级 pip
pip install --upgrade pip

# 安装依赖（使用国内镜像加速）
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 安装 MinerU（可选，用于 PDF 解析）
pip install mineru

# 安装额外的向量搜索依赖（如果使用 Milvus）
pip install pymilvus sentence-transformers

# 配置环境变量
cp .env.example .env

# 创建必要目录
mkdir -p uploads parsed_output parsed_data images
```

#### 6.2 配置后端环境变量

编辑 `.env` 文件：

```bash
nano .env
```

添加 Ollama 配置（如果已安装）：

```env
# FastAPI 配置
APP_NAME=AI Writer Backend
APP_VERSION=0.0.1
DEBUG=True
HOST=0.0.0.0
PORT=8000

# CORS 配置
CORS_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173"]

# 文件存储配置
UPLOAD_DIR=./uploads
PARSE_OUTPUT_DIR=./parsed_data
MAX_UPLOAD_SIZE=104857600  # 100MB

# MinerU 配置
MINERU_BACKEND=pipeline
MINERU_OUTPUT_DIR=./parsed_output
MINERU_LANG=ch

# Ollama 配置（如果使用本地 LLM）
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b
OLLAMA_TIMEOUT=120

# Milvus 配置（如果使用向量搜索）
MILVUS_HOST=localhost
MILVUS_PORT=19530
```

#### 6.3 前端安装

```bash
# 进入前端目录
cd ../frontend

# 配置 npm 使用国内镜像
npm config set registry https://registry.npmmirror.com

# 安装依赖
npm install

# 验证安装
npm run build  # 测试编译是否成功
rm -rf dist     # 删除测试构建
```

---

### 第七步：启动应用

#### 方式 A：基础模式（推荐新手）

**仅启动前后端，使用模拟 LLM**

```bash
# 终端 1 - 启动后端
cd ~/Ai-Writer/backend
source venv/bin/activate  # 如果使用虚拟环境
python -m app.main

# 终端 2 - 启动前端
cd ~/Ai-Writer/frontend
npm run dev
```

**访问地址**：
- 前端：http://localhost:5173
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs

#### 方式 B：本地 LLM 模式

**使用 Ollama 本地模型**

```bash
# 终端 1 - 启动 Ollama
ollama serve

# 终端 2 - 启动后端
cd ~/Ai-Writer/backend
source venv/bin/activate
python -m app.main

# 终端 3 - 启动前端
cd ~/Ai-Writer/frontend
npm run dev
```

**特点**：
- ✅ 完全离线运行
- ✅ 数据隐私保护
- ✅ 无需 API 费用
- ⚠️ 需要较好的硬件配置

#### 方式 C：完整模式（含向量搜索）

**包含 Milvus 向量数据库，支持高级 RAG 功能**

```bash
# 终端 1 - 启动 Milvus
cd ~/Ai-Writer/milvus
docker compose up -d

# 等待 30-60 秒，检查状态
docker compose ps

# 终端 2 - 启动 Ollama（可选）
ollama serve

# 终端 3 - 启动后端
cd ~/Ai-Writer/backend
source venv/bin/activate
python -m app.main

# 终端 4 - 启动前端
cd ~/Ai-Writer/frontend
npm run dev
```

---

## 🤖 Ollama 本地 LLM 配置

### 推荐模型

根据硬件配置选择合适的模型：

| RAM 配置 | 推荐模型 | 命令 | 说明 |
|---------|---------|------|------|
| 8GB | qwen2.5:3b | `ollama pull qwen2.5:3b` | 轻量级，速度最快 |
| 16GB | qwen2.5:7b | `ollama pull qwen2.5:7b` | 平衡性能和速度 |
| 32GB | qwen2.5:14b | `ollama pull qwen2.5:14b` | 更好的推理能力 |
| 64GB+ | qwen2.5:32b | `ollama pull qwen2.5:32b` | 最佳性能 |

### 模型管理

```bash
# 查看已安装模型
ollama list

# 删除模型
ollama rm qwen2.5:3b

# 更新模型
ollama pull qwen2.5:7b

# 查看模型信息
ollama show qwen2.5:7b

# 运行模型测试
ollama run qwen2.5:7b
```

### 性能优化

**GPU 加速（如果有 NVIDIA 显卡）**：

```bash
# 安装 NVIDIA CUDA 工具包
sudo apt install -y nvidia-cuda-toolkit

# 验证 GPU 识别
nvidia-smi

# Ollama 会自动使用 GPU
```

**CPU 模式优化**：

```bash
# 设置环境变量限制 CPU 使用
export OLLAMA_NUM_GPU=0
export OLLAMA_NUM_THREAD=4
```

---

## 🔧 WSL2 专用配置

### 网络访问配置

WSL2 使用虚拟网络，在 Windows 浏览器访问时：

```bash
# 方式 1: 使用 localhost（推荐）
# WSL2 会自动转发 localhost 端口
# http://localhost:5173

# 方式 2: 使用 WSL2 IP 地址
hostname -I  # 获取 WSL2 IP
# http://172.x.x.x:5173
```

### 文件访问

**Windows 访问 WSL2 文件**：
```powershell
# 在文件资源管理器中
\\wsl$\Ubuntu\home\你的用户名\Ai-Writer
```

**WSL2 访问 Windows 文件**：
```bash
cd /mnt/c/Users/你的用户名/
```

### 性能优化

**将项目放在 WSL2 文件系统中**：
```bash
# ✅ 推荐：放在 WSL2 文件系统
cd ~
git clone https://github.com/fsxbmb/Ai-Writer.git

# ❌ 不推荐：放在 /mnt/c（性能差）
cd /mnt/c/Users/
git clone https://github.com/fsxbmb/Ai-Writer.git
```

---

## 💻 笔记本电脑性能优化

### 1. 内存优化

**检查内存使用**：
```bash
free -h
```

**限制 Docker 内存占用**：
```bash
# 编辑 Docker 配置
sudo vim /etc/docker/daemon.json

# 添加以下内容（根据笔记本内存调整）
{
  "memory": "4g",
  "memory-swap": "4g"
}

# 重启 Docker
sudo systemctl restart docker
```

### 2. CPU 优化

**检查 CPU 核心数**：
```bash
nproc
```

**限制后端 worker 数量**：
```bash
# 编辑 backend 启动命令
uvicorn app.main:app --workers 2  # 根据核心数调整
```

### 3. Ollama 性能调整

**根据硬件选择合适的模型**：

```bash
# 8GB RAM - 使用小模型
ollama pull qwen2.5:3b

# 16GB RAM - 使用中等模型
ollama pull qwen2.5:7b

# 禁用 GPU（如果没有独立显卡）
export OLLAMA_NUM_GPU=0
```

### 4. 磁盘优化

**将依赖安装在虚拟环境中**，节省系统空间：
```bash
# 使用 Python 虚拟环境
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 5. 电源管理

**笔记本使用时建议**：
- ✅ 接通电源运行开发环境
- ✅ 使用"高性能"电源模式
- ⚠️ 电池模式下可能性能下降
- ⚠️ 使用 Ollama 时务必接通电源

---

## 📖 功能说明

### 1. 知识库管理

**基础功能**：
- PDF 文档上传和管理
- MinerU 智能解析（需要安装）
- Markdown 编辑和预览
- 标签分类和搜索

**无需额外配置**，启动即可使用。

### 2. 知识问答 (RAG)

**两种模式**：

**A. 模拟模式（无需额外配置）**
- 使用简单的匹配算法
- 快速响应
- 适合测试和演示

**B. 高级模式（需要 Milvus + Ollama）**
- 向量语义搜索
- LLM 智能回答
- 需要更多资源
- 更好的问答质量

### 3. 文档生成

**支持的模式**：

**A. 模板生成（无需 LLM）**
- 使用预设模板
- 快速生成基础文档

**B. AI 辅助生成（需要 Ollama）**
- LLM 智能生成
- 根据上下文写作
- 支持多种风格

### 4. 文档导出

**支持的格式**：
- Markdown (.md)
- PDF (.pdf) - 需要 wkhtmltopdf
- 纯文本 (.txt)
- HTML (.html)

---

## 🔍 常见问题解决

### 问题 1：npm install 失败

**错误**：`ECONNREFUSED` 或网络超时

**解决方案**：
```bash
# 使用国内镜像
npm config set registry https://registry.npmmirror.com
npm config set disturl https://npmmirror.com/mirrors/node/

# 重新安装
rm -rf node_modules package-lock.json
npm install
```

### 问题 2：Python 依赖安装失败

**错误**：`pip install` 速度慢或失败

**解决方案**：
```bash
# 升级 pip
pip install --upgrade pip

# 使用清华镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 或者永久配置
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

### 问题 3：端口被占用

**错误**：`Address already in use`

**解决方案**：
```bash
# 查看占用端口的进程
sudo lsof -i :8000  # 后端
sudo lsof -i :5173  # 前端
sudo lsof -i :11434 # Ollama

# 杀死进程
sudo kill -9 <PID>

# 或者修改端口
# 编辑 backend/.env: PORT=8001
# 编辑 frontend/vite.config.ts: server.port: 5174
```

### 问题 4：Docker 权限错误

**错误**：`permission denied while trying to connect to the Docker daemon`

**解决方案**：
```bash
# 添加用户到 docker 组
sudo usermod -aG docker $USER

# 重新登录 WSL
# 在 PowerShell 运行：wsl --shutdown
# 然后重新打开 WSL
```

### 问题 5：MinerU 无法使用

**错误**：MinerU 相关错误

**解决方案**：
```bash
# 方案 1: 安装 MinerU
pip install mineru

# 方案 2: 跳过 MinerU，项目会使用模拟解析器
# 不影响其他功能使用
```

### 问题 6：WSL2 网络无法访问

**错误**：Windows 浏览器无法打开 localhost:5173

**解决方案**：
```bash
# 检查 WSL2 服务是否运行
cd ~/Ai-Writer/frontend
npm run dev

# 在 Windows PowerShell 中检查防火墙
# 或尝试使用 WSL2 IP 地址
hostname -I
# 使用返回的 IP 访问，如：http://172.30.144.1:5173
```

### 问题 7：笔记本性能不足

**表现**：应用运行缓慢，卡顿

**解决方案**：
```bash
# 1. 关闭 Milvus（如果不需要向量搜索）
cd ~/Ai-Writer/milvus
docker compose down

# 2. 使用更小的模型
ollama pull qwen2.5:3b

# 3. 减少 worker 数量
# 修改后端启动，使用单进程
python -m app.main

# 4. 检查系统资源
htop  # 需要先安装: sudo apt install htop

# 5. 清理系统缓存
sudo apt clean
sudo apt autoremove
```

### 问题 8：Ollama 无法连接

**错误**：后端无法连接到 Ollama

**解决方案**：
```bash
# 检查 Ollama 服务状态
ps aux | grep ollama

# 启动 Ollama 服务
ollama serve &

# 测试连接
curl http://localhost:11434/api/tags

# 检查后端配置
cat backend/.env | grep OLLAMA
```

### 问题 9：Ollama 模型下载失败

**错误**：模型下载缓慢或失败

**解决方案**：
```bash
# 使用代理（如果有）
export HTTP_PROXY=http://your-proxy:port
export HTTPS_PROXY=http://your-proxy:port

# 或手动下载模型文件
# 参考：https://ollama.com/download
```

### 问题 10：文档导出失败

**错误**：无法导出 PDF 或 Word

**解决方案**：
```bash
# 安装必要的系统依赖
sudo apt install -y wkhtmltopdf pandoc

# 重新安装 Python 依赖
pip install reportlab pdfkit
```

---

## 📝 日常使用

### 启动应用（完整模式）

创建启动脚本 `start-full.sh`：

```bash
# 在项目根目录创建
cat > start-full.sh << 'EOF'
#!/bin/bash

# 启动 Milvus
cd ~/Ai-Writer/milvus
docker compose up -d

# 等待 Milvus 启动
sleep 30

# 启动 Ollama
ollama serve &
sleep 5

# 启动后端
cd ~/Ai-Writer/backend
source venv/bin/activate
python -m app.main &

# 启动前端
cd ~/Ai-Writer/frontend
npm run dev &

echo "应用已启动（完整模式）"
echo "前端: http://localhost:5173"
echo "后端: http://localhost:8000"
echo "Milvus: http://localhost:9091"
EOF

chmod +x start-full.sh
./start-full.sh
```

### 启动应用（基础模式）

创建启动脚本 `start-basic.sh`：

```bash
cat > start-basic.sh << 'EOF'
#!/bin/bash

# 启动后端
cd ~/Ai-Writer/backend
source venv/bin/activate
python -m app.main &

# 启动前端
cd ~/Ai-Writer/frontend
npm run dev &

echo "应用已启动（基础模式）"
echo "前端: http://localhost:5173"
echo "后端: http://localhost:8000"
EOF

chmod +x start-basic.sh
./start-basic.sh
```

### 停止应用

```bash
# 查找并停止进程
pkill -f "python -m app.main"
pkill -f "npm run dev"

# 停止 Milvus
cd ~/Ai-Writer/milvus
docker compose down

# 停止 Ollama
pkill ollama
```

### 更新项目

```bash
cd ~/Ai-Writer
git pull origin main

# 更新后端
cd backend
source venv/bin/activate
pip install -r requirements.txt --upgrade

# 更新前端
cd ../frontend
npm install

# 重启服务
```

---

## 🎯 开发建议

### 1. 使用 VS Code 远程开发

```bash
# 在 WSL2 中安装 VS Code Server
code .

# 或在 Windows VS Code 中安装 "WSL" 扩展
# 然后在 WSL 终端运行: code .
```

### 2. 使用 PM2 管理进程

```bash
# 安装 PM2
npm install -g pm2

# 启动后端
cd ~/Ai-Writer/backend
pm2 start "python -m app.main" --name ai-writer-backend

# 启动前端
cd ~/Ai-Writer/frontend
pm2 start "npm run dev" --name ai-writer-frontend

# 查看状态
pm2 status

# 查看日志
pm2 logs

# 停止所有
pm2 stop all
```

### 3. 数据备份

```bash
# 备份重要数据
cp -r ~/Ai-Writer/backend/data ~/Ai-Writer-backup/
cp -r ~/Ai-Writer/backend/uploads ~/Ai-Writer-backup/
```

---

## 📚 技术支持

- **GitHub Issues**: https://github.com/fsxbmb/Ai-Writer/issues
- **API 文档**: http://localhost:8000/docs
- **项目 README**: https://github.com/fsxbmb/Ai-Writer
- **Ollama 文档**: https://ollama.com/docs
- **MinerU 文档**: https://github.com/opendatalab/MinerU
- **Milvus 文档**: https://milvus.io/docs

---

## ⚡ 快速参考

### 端口说明
- **5173**: 前端开发服务器
- **8000**: 后端 API 服务器
- **11434**: Ollama API 服务
- **19530**: Milvus 向量数据库
- **9091**: Milvus 管理界面
- **9001**: MinIO 控制台

### 目录结构
```
Ai-Writer/
├── backend/         # Python FastAPI 后端
│   ├── app/        # 应用代码
│   ├── data/       # 数据文件
│   ├── uploads/    # 上传文件
│   └── venv/       # 虚拟环境
├── frontend/       # Vue 3 前端
│   └── src/       # 源代码
├── milvus/        # 向量数据库配置
└── DEPLOYMENT.md  # 本文件
```

### 常用命令
```bash
# 启动后端
cd backend && python -m app.main

# 启动前端
cd frontend && npm run dev

# 启动 Ollama
ollama serve

# 启动 Milvus
cd milvus && docker compose up -d

# 查看日志
tail -f backend/logs/*.log
```

### 环境变量参考

```env
# 后端 .env 配置
DEBUG=True
PORT=8000

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b

# Milvus
MILVUS_HOST=localhost
MILVUS_PORT=19530
```

---

## 📄 许可证

MIT License
