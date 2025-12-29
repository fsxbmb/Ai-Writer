# AI Writer - 智能写作助手

一个类似 Gemini 风格的 AI 写手 Web 应用，集成了 MinerU 文档解析功能。

## 功能特性

- **知识库管理**（核心功能）
  - PDF 文档上传和管理
  - MinerU 智能解析
  - Markdown 编辑和预览
  - 标签分类和搜索

- **知识问答** - 开发中
- **文档生成** - 开发中
- **历史案例** - 开发中

## 技术栈

### 前端
- Vue 3 + TypeScript + Vite
- Naive UI (组件库)
- Pinia (状态管理)
- Vue Router (路由)

### 后端
- Python FastAPI
- MinerU (PDF 解析)

## 项目结构

```
AI_Writer/
├── frontend/          # Vue 3 前端项目
│   ├── src/
│   │   ├── api/              # API 客户端
│   │   ├── components/       # 组件
│   │   ├── layouts/          # 布局
│   │   ├── router/           # 路由
│   │   ├── stores/           # Pinia 状态
│   │   ├── types/            # TypeScript 类型
│   │   └── views/            # 页面
│   ├── package.json
│   └── vite.config.ts
│
├── backend/           # Python FastAPI 后端
│   ├── app/
│   │   ├── api/             # API 路由
│   │   ├── core/            # 配置
│   │   ├── models/          # 数据模型
│   │   ├── schemas/         # Pydantic schemas
│   │   └── services/        # 业务逻辑
│   ├── requirements.txt
│   └── main.py
│
└── MinerU/            # MinerU 文档解析器
```

## 快速开始

### 前提条件

- Node.js 18+
- Python 3.10+
- MinerU 已安装（在项目 MinerU 目录）

### 后端启动

1. 进入后端目录：
```bash
cd backend
```

2. 安装 Python 依赖：
```bash
pip install -r requirements.txt
```

3. 复制环境变量配置：
```bash
cp .env.example .env
```

4. 启动后端服务：
```bash
python -m app.main
```

后端将运行在 `http://localhost:8000`

API 文档：`http://localhost:8000/docs`

### 前端启动

1. 进入前端目录：
```bash
cd frontend
```

2. 安装依赖：
```bash
npm install
```

3. 启动开发服务器：
```bash
npm run dev
```

前端将运行在 `http://localhost:5173`

## 使用说明

### 知识库管理

1. 点击"上传文档"按钮，或拖拽 PDF 文件到上传区域
2. 上传完成后，文档会出现在列表中
3. 点击"解析"按钮，调用 MinerU 进行 PDF 解析
4. 解析完成后，可以预览和编辑 Markdown 内容
5. 使用标签和搜索功能管理文档

### API 端点

#### 文档管理
- `POST /api/documents/upload` - 上传文档
- `POST /api/documents/{id}/parse` - 解析文档
- `GET /api/documents` - 获取文档列表
- `GET /api/documents/{id}` - 获取文档详情
- `PUT /api/documents/{id}` - 更新文档
- `DELETE /api/documents/{id}` - 删除文档
- `GET /api/documents/{id}/download` - 下载文档

## 开发计划

- [x] 前后端项目结构搭建
- [x] MinerU 服务集成
- [x] 文档上传和解析 API
- [x] 知识库管理界面
- [ ] PDF 在线预览
- [ ] Markdown 编辑器增强
- [ ] 知识问答页面
- [ ] 文档生成页面
- [ ] 历史案例页面

## 常见问题

### MinerU 未安装

如果 MinerU 未正确安装，后端会使用模拟解析器。要使用真实的 MinerU：

1. 确保 MinerU 已安装在 `../MinerU` 目录
2. 检查 Python 路径是否包含 MinerU

### CORS 错误

如果遇到 CORS 错误，检查后端 `.env` 文件中的 `CORS_ORIGINS` 配置。

## 许可证

MIT
