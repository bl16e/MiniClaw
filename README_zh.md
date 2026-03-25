# MiniClaw

[English](README.md) | [中文](README_zh.md)

MiniClaw 是一个基于 LangGraph 的模块化 Agent 全栈应用。支持异步工作流编排、工具调用与人工审批、轻量 RAG、子代理并行执行、持久化检查点以及 Time Travel 调试。

## 界面截图

| 工具执行 & Markdown 渲染 | 人工审批（Human-in-the-Loop） |
|---|---|
| ![chat-tool-table](docs/images/chat-tool-table.png) | ![chat-approval](docs/images/chat-approval.png) |

## 功能特性

**Agent 核心**
- LangGraph 异步工作流，内置分类器路由（RAG / 子代理 / 直接回答）
- 多工具并行执行
- 基于 Chroma 的本地文档和对话历史 RAG 检索
- 子代理 Fan-out / Fan-in 并行分析
- 经验反思与自动历史摘要

**全栈 Chat UI**
- FastAPI 后端，SSE 流式传输实时输出
- React + TypeScript 前端，Zustand 状态管理
- Markdown 渲染：GFM 表格、代码高亮、一键复制
- 工具调用卡片，实时状态指示器（pending / executing / completed / error）
- 敏感工具审批横幅（send_email、download_file、run_python_code）

**会话管理**
- 多会话支持，SQLite 持久化检查点
- Time Travel：从历史面板中任意检查点重放
- 分支：从任意历史状态分叉出新对话
- 历史面板按用户交互轮次过滤（而非内部节点步骤）

## 架构

```text
客户端 (React + Vite)               服务端 (FastAPI)
+-----------------+   POST /chat   +------------------+
|  SessionSidebar |--------------->|  SSE Stream      |---> graph.astream()
|  ChatPanel      |<-- SSE events -|  Handler         |
|  HistoryPanel   |                |                  |
|  ApprovalBanner |-- POST /approve|  ApprovalManager |---> asyncio.Event
+-----------------+                +------------------+
```

## 项目结构

```text
.
+-- agent_core.py           # 图组装与路由
+-- api.py                  # FastAPI 应用与路由
+-- api_models.py           # Pydantic 请求/响应模型
+-- approval_manager.py     # 异步审批状态机
+-- stream_handler.py       # SSE 流式包装器
+-- checkpointer.py         # AsyncSqliteSaver 初始化
+-- session_manager.py      # 会话 CRUD 与 Time Travel
+-- runner.py               # CLI 流式运行器
+-- main.py                 # CLI 入口（支持斜杠命令）
+-- config.py               # 环境变量配置
+-- state.py                # AgentState 类型定义
+-- utils.py                # 敏感工具检测、经验反思
+-- nodes/                  # 图节点实现
+-- tools/                  # 工具定义
+-- rag/                    # Chroma 检索辅助
+-- skills/                 # 技能提示词与 SOP
+-- Dockerfile              # 后端容器镜像
+-- docker-compose.yml      # 全栈编排
+-- web/                    # React 前端
    +-- Dockerfile          # 前端多阶段构建
    +-- nginx.conf          # Nginx 反向代理配置
    +-- src/
        +-- api/            # REST + SSE 请求封装
        +-- stores/         # Zustand 全局状态
        +-- hooks/          # useChat, useSessions
        +-- components/     # Chat、Sidebar、History 面板
        +-- types/          # TypeScript 类型定义
```

## 快速开始

### 环境要求

- Python 3.9+
- Node.js 18+
- 兼容 OpenAI 格式的 API 端点

### 安装

```bash
git clone https://github.com/bl16e/MiniClaw.git
cd MiniClaw

# 安装 Python 依赖
pip install -r requirements.txt

# 安装前端依赖
cd web && npm install && cd ..
```

### 配置

```bash
cp .env.example .env
# 编辑 .env 填入你的 API Key
```

| 变量 | 必填 | 说明 |
|------|------|------|
| `OPENAI_API_KEY` | 是 | OpenAI 兼容端点的 API Key |
| `OPENAI_API_BASE` | 否 | API 基础 URL（默认：DashScope） |
| `MODEL_NAME` | 否 | 模型名称（默认：qwen-max） |
| `HTTP_PROXY` / `HTTPS_PROXY` | 否 | 网络代理 |
| `GMAIL_CREDENTIALS_FILE` | 否 | Gmail OAuth 凭证路径 |
| `CORS_ORIGINS` | 否 | 允许的 CORS 来源，逗号分隔（默认：`http://localhost:5173`） |

### 运行

**Web UI（推荐）**

```bash
# 终端 1：启动后端
uvicorn api:app --reload --port 8000

# 终端 2：启动前端
cd web && npm run dev
```

浏览器打开 http://localhost:5173

**CLI 模式**

```bash
python main.py
```

CLI 命令：`/sessions`、`/new`、`/switch`、`/history`、`/replay`、`/branch`、`/help`

### Docker 部署

确保已安装 Docker 和 Docker Compose，然后：

```bash
cp .env.example .env
# 编辑 .env 填入你的 API Key

docker compose up --build
```

浏览器打开 http://localhost

后台运行：

```bash
docker compose up --build -d
```

停止服务：

```bash
docker compose down
```

持久化数据（检查点和向量数据库）存储在 Docker 命名卷中，容器重启后数据不会丢失。

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/chat/{thread_id}` | 发送消息，返回 SSE 流 |
| POST | `/api/chat/{thread_id}/approve` | 审批/拒绝敏感工具 |
| GET | `/api/sessions` | 列出所有会话 |
| POST | `/api/sessions` | 创建新会话 |
| GET | `/api/sessions/{thread_id}/messages` | 完整消息历史 |
| GET | `/api/sessions/{thread_id}/history` | 检查点历史（按轮次） |
| POST | `/api/sessions/{thread_id}/replay` | 从检查点重放（SSE） |
| POST | `/api/sessions/{thread_id}/branch` | 从检查点分支 |
| DELETE | `/api/sessions/{thread_id}` | 删除会话 |

## SSE 事件协议

| 事件 | 数据 | 说明 |
|------|------|------|
| `node_start` | `{node, step}` | 图节点开始执行 |
| `message_complete` | `{content, role}` | 完整 AI 消息 |
| `tool_call` | `{id, name, args}` | 工具调用 |
| `tool_result` | `{id, name, result, status}` | 工具执行结果 |
| `approval_required` | `{tools: [...]}` | 等待用户审批 |
| `approval_resolved` | `{approved}` | 审批结果 |
| `complete` | `{thread_id}` | 本轮对话完成 |
| `error` | `{message}` | 发生错误 |

## 安全说明

- 敏感工具（`send_email`、`download_file`、`run_python_code`、`filesystem` 写操作）需要用户显式审批
- 密钥和认证文件通过 `.gitignore` 排除
- 代码执行工具使用受限内建函数集（禁止 `eval`、`exec`、`import`、`open`）
