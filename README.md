# py-openclaw

一个本地优先、文件驱动、前后端分离的轻量级 AI Agent 工作台。

`py-openclaw` 的目标不是做一个重型 SaaS 平台，而是提供一套透明、可控、易修改的本地 Agent 系统：会话、记忆、技能、知识库、定时任务都尽量落在本地文件系统中，便于查看、编辑、调试和扩展。

## 功能特性

- 流式聊天：基于 SSE 返回 token、工具调用和最终回复
- 文件驱动记忆：长期记忆保存在 `backend/memory/MEMORY.md`
- 技能系统：每个技能一个目录，一个 `SKILL.md`
- 知识库检索：支持对 `backend/knowledge/` 文档做检索
- RAG 模式：支持针对长期记忆的检索增强
- 定时任务：支持“每天固定时间”执行提醒或自动任务
- 联网搜索：支持基于 Tavily 的 `web_search` skill
- 在线编辑：前端可直接编辑 Prompt、Skill、Memory 文件
- 实时任务反馈：定时任务执行过程通过会话级 SSE 主动推送到前端

## 为什么这样设计？

这个项目采用“文件优先 + API 服务 + 前端工作台”的设计，核心考虑是：

- 透明：`MEMORY.md`、`SKILL.md`、`sessions/*.json` 都可以直接打开查看
- 可控：Prompt、技能、记忆和工具协议都能直接修改
- 易调试：系统状态主要落在本地文件中，出现问题更容易定位
- 易扩展：新增技能、工具、知识库或定时任务时，不需要推翻整体结构

相比一开始就引入数据库、复杂任务队列和黑盒 Agent 编排，这套设计更适合本地实验、个人助手和快速迭代。

## 体系结构

### Backend

- Python 3.10+
- FastAPI
- Uvicorn
- LangChain 1.x
- langchain-core
- langchain-deepseek
- LlamaIndex Core
- requests / html2text

后端职责：

- 组装 System Prompt
- 创建和运行 Agent
- 注册工具
- 管理会话、记忆、知识库和定时任务
- 通过 HTTP / SSE 向前端暴露能力

### Frontend

- Next.js 14
- React 18
- TypeScript
- Tailwind CSS
- Monaco Editor

前端职责：

- 展示聊天流式内容
- 展示工具调用链和检索结果
- 编辑 Prompt / Skills / Memory 文件
- 订阅会话级 SSE，实时显示定时任务执行过程

## 核心概念

### Prompt Components

System Prompt 不是硬编码在 Python 中，而是由多个 Markdown 文件拼装而成：

- `backend/workspace/SOUL.md`
- `backend/workspace/IDENTITY.md`
- `backend/workspace/USER.md`
- `backend/workspace/AGENTS.md`
- `backend/SKILLS_SNAPSHOT.md`
- `backend/memory/MEMORY.md`（非 RAG 模式）

### Skills

技能以目录形式存在于 `backend/skills/` 中，每个技能至少包含一个 `SKILL.md`。  
Agent 会先读取技能文档，再按照文档指引调用工具，而不是直接把技能写死成 Python 函数。

当前内置技能包括：

- `get_weather` 查询天气
- `web_search` 联网搜索
- `scheduled_tasks` 定时任务
- `ai-news-daily` 获取AI领域咨询
- `self-evolution` 自我进化

### Memory

记忆分两层：

- 显式长期记忆：`backend/memory/MEMORY.md`
- 检索增强记忆：为 `MEMORY.md` 建立索引，用于 RAG 模式

这样既保留了可读性，也兼顾了当记忆变长时的检索效率。

### Knowledge Base

知识库位于 `backend/knowledge/`。  
当前默认支持索引：

- `.md`
- `.txt`
- `.json`

### Scheduled Tasks

定时任务定义保存在：

- `backend/storage/scheduled_tasks.json`

当前支持：

- 每天固定时间执行任务

例如：

- 每天晚上八点提醒我吃药
- 帮我创建一个每天7点30查询深圳天气的定时任务

定时任务运行时会复用现有 Agent 和工具能力，并把执行过程通过会话级 SSE 实时推送到前端。

## 项目结构

```text
py-openclaw/
├─ backend/
│  ├─ api/                 # FastAPI 路由
│  ├─ graph/               # Agent / Prompt / Session / Memory 核心逻辑
│  ├─ scheduler/           # 定时任务存储与执行
│  ├─ tools/               # LangChain 工具
│  ├─ skills/              # 技能目录
│  ├─ knowledge/           # 知识库文档
│  ├─ memory/              # 长期记忆
│  ├─ sessions/            # 会话 JSON
│  ├─ storage/             # 索引与运行时持久化数据
│  ├─ workspace/           # Prompt 组件文件
│  ├─ app.py               # FastAPI 入口
│  ├─ requirements.txt
│  ├─ .env.example
│  └─ SKILLS_SNAPSHOT.md
├─ frontend/
│  ├─ src/
│  │  ├─ app/
│  │  ├─ components/
│  │  └─ lib/
│  └─ package.json
├─ FINAL.md
└─ README.md
```

## 快速开始

### 1. Clone

```bash
git clone <your-repo-url>
cd pyOpenClaw
```

### 2. Configure Environment

复制环境变量模板：

```bash
cd backend
copy .env.example .env
```

最少需要配置：

```env
DEEPSEEK_API_KEY=your_key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

OPENAI_API_KEY=your_key
OPENAI_BASE_URL=https://api.openai.com/v1
EMBEDDING_MODEL=text-embedding-3-small

TAVILY_API_KEY=your_key
```

说明：

- `DEEPSEEK_*`：主聊天模型
- `OPENAI_*`：embedding / RAG
- `TAVILY_API_KEY`：联网搜索 skill 使用

如果你使用 OpenRouter 或其他兼容 OpenAI 的 embedding 服务，可以修改 `OPENAI_BASE_URL` 和模型名。

### 3. 启动后端

```bash
cd backend
pip install -r requirements.txt
uvicorn app:app --port 8010 --host 0.0.0.0 --reload
```

### 4. 启动前端

```bash
cd frontend
npm install
npm run dev
```

默认地址：

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8010`

## 使用方法

### 聊天

直接在前端输入消息即可，后端会：

- 加载当前会话历史
- 构建最新 Prompt
- 动态注册工具
- 通过 SSE 流式返回结果

### 编辑 Memory

长期记忆文件：

- `backend/memory/MEMORY.md`

可以：

- 在前端右侧编辑器中直接修改
- 让 Agent 帮你写入长期记忆

保存后会自动重建记忆索引。

### 编辑 Skills

技能文件位于：

- `backend/skills/*/SKILL.md`

保存技能文件时：

- `backend/SKILLS_SNAPSHOT.md` 会自动刷新

### 使用知识库

把文档放进：

- `backend/knowledge/`

之后通过 Agent 或知识库工具触发检索即可。

### 使用定时任务

示例：

- “每天晚上八点提醒我吃药”
- “帮我创建一个每天7点30查询深圳天气的定时任务”

到点后：

- 后台会自动触发任务
- 当前会话中会新增对应的 user / assistant 消息
- 前端会实时显示执行过程

## 工具

当前核心工具包括：

- `terminal`
- `python_repl`
- `fetch_url`
- `read_file`
- `write_file`
- `search_knowledge_base`
- `schedule_task`
- `list_scheduled_tasks`
- `cancel_scheduled_task`

## 开发笔记

- 修改技能时，优先改 `SKILL.md`
- 修改系统行为prompt时，优先改 `backend/workspace/` 下的 Markdown 文件
- 修改持久化逻辑时，重点关注：
  - `backend/sessions/`
  - `backend/memory/`
  - `backend/storage/`
- 新增工具时，记得同步更新：
  - `backend/tools/`
  - `backend/tools/__init__.py`
  - `backend/workspace/AGENTS.md`

## 当前限制

- `knowledge/` 当前默认不支持 PDF 索引
- 某些复杂中文网页对 `fetch_url` 支持有限
- 定时任务当前只支持“每天固定时间”
- 当前更适合本地单用户，不是面向高并发生产环境
