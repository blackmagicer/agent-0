# 扫地机器人 AI 智能客服系统

基于 LangChain ReAct Agent + RAG 的扫地机器人智能客服系统，后端使用 FastAPI，前端使用 uni-app（Vue 3）。

## 项目结构

```
├── Agent/                   # 后端 (Python/FastAPI)
│   ├── agent_app/
│   │   ├── agent/           # LangChain ReAct Agent + 工具
│   │   ├── rag/             # RAG 向量检索服务 (ChromaDB)
│   │   ├── model/           # LLM 模型工厂
│   │   ├── data/            # 知识库文档 (PDF/TXT)
│   │   ├── prompts/         # 系统提示词模板
│   │   └── utils/           # 工具函数 (配置/文件/日志/路径)
│   ├── core/                # 认证 & 邮件
│   ├── models/              # SQLAlchemy 数据模型
│   ├── repository/          # 数据访问层
│   ├── routers/             # API 路由 (auth/agent/conversation)
│   ├── schemas/             # Pydantic 数据校验
│   ├── services/            # 业务逻辑层
│   ├── alembic/             # 数据库迁移
│   └── main.py              # 应用入口
│
└── agent-app2/              # 前端 (uni-app / Vue 3)
    ├── pages/
    │   ├── login/           # 登录
    │   ├── register/        # 注册
    │   └── index/           # 对话主界面
    ├── http/                # HTTP 请求封装
    └── static/              # 静态资源
```

## 功能特性

- **AI 智能对话** — 基于 LangChain ReAct Agent，支持流式输出
- **RAG 知识库检索** — ChromaDB 向量存储，支持 PDF/TXT 文档加载
- **Agent 工具调用** — 知识库查询、文件读取、天气查询、用户位置、外部数据获取等
- **对话管理** — 多轮对话持久化，历史记录查询
- **用户认证** — 邮箱验证码注册/登录，JWT Token 鉴权
- **跨平台前端** — uni-app 支持 Android、iOS、微信小程序

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI |
| AI 框架 | LangChain + LangGraph |
| 向量数据库 | ChromaDB |
| 关系数据库 | MySQL (SQLAlchemy + aiomysql) |
| 认证 | JWT + 邮箱验证码 |
| 前端 | uni-app (Vue 3) |
| LLM | 通过模型工厂可配置 |

## 快速开始

### 环境要求

- Python 3.11+
- MySQL 8.0+
- Node.js 18+ (前端)
- HBuilderX (uni-app 开发)

### 后端配置

1. 进入 Agent 目录，创建虚拟环境：

```bash
cd Agent
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

2. 复制环境变量文件并修改：

```bash
cp .env.example .env
```

编辑 `.env`，填入数据库、邮箱、JWT 等配置。

3. 配置 Agent（在 `Agent/config/` 目录下编辑 yml 文件）：

- `agent.yml` — LLM 模型、API Key 等
- `rag.yml` — RAG 检索参数
- `chroma.yml` — ChromaDB 持久化路径

4. 初始化数据库：

```bash
alembic upgrade head
```

5. 启动服务：

```bash
python main.py
```

### 前端配置

1. 使用 HBuilderX 打开 `agent-app2/` 目录
2. 修改 `http/http.js` 中的 API 地址为后端实际地址
3. 运行到微信开发者工具 / 真机调试

### API 概览

| 端点 | 说明 |
|------|------|
| `POST /auth/code` | 获取邮箱验证码 |
| `POST /auth/register` | 用户注册 |
| `POST /auth/login` | 用户登录 |
| `POST /agent/chat/stream` | AI 流式对话 |
| `POST /agent/file/upload` | 文件上传 |
| `GET /conversation/list` | 对话列表 |
| `GET /conversation/{id}/messages` | 历史消息 |

## 知识库

将 PDF 或 TXT 文档放入 `Agent/agent_app/data/` 目录，系统启动时会自动加载并构建向量索引。当前预置了扫地机器人选购、使用、维护、故障排除等领域的知识文档。
