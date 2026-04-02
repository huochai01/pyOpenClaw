# Mini-OpenClaw README

---

## 一、项目介绍

### 1. 功能与目标定位
**Mini-OpenClaw** 是一个基于 **Python** 重构的、轻量级且高度透明的 AI Agent 系统，旨在复刻并优化 OpenClaw（原名 Moltbot/Clawdbot）的核心体验。

本项目不追求构建庞大的 SaaS 平台，而是致力于打造一个**运行在本地的、拥有“真实记忆”的数字副手**。其核心差异化定位在于：

- **文件即记忆 (File-first Memory)**：摒弃不透明的向量数据库，回归最原始、最通用的 Markdown/JSON 文件系统。用户的每一次对话、Agent 的每一次反思，都以人类可读的文件形式存在。
- **技能即插件 (Skills as Plugins)**：遵循 Anthropic 的 Agent Skills 范式，通过文件夹结构管理能力，实现“拖入即用”的技能扩展。
- **透明可控**：所有的 System Prompt 拼接逻辑、工具调用过程、记忆读写操作对开发者完全透明，拒绝“黑盒”Agent。

### 2. 项目核心技术架构
本项目要求完全采用 **前后端分离** 架构，后端作为纯 API 服务运行。

- **后端语言**：Python 3.10+ (强制使用 Type Hinting)。
- **Web 框架**：**FastAPI** (提供 RESTful 接口，支持异步处理)。
- **Agent 编排引擎**：**LangChain 1.x (Stable Release)**。
  - **核心 API**：必须使用 `create_agent` API (`from langchain.agents import create_agent`)。这是 LangChain 1.0 版本发布的最新标准 API，用于构建基于 Graph 运行时的 Agent。
  - **核心说明**：严禁使用旧版的 `AgentExecutor` 或早期的 `create_react_agent`（旧链式结构）。`create_agent` 底层虽然基于 LangGraph 运行时，但提供了更简洁的标准化接口，本项目应紧跟这一最新范式。
- **RAG 检索引擎**：**LlamaIndex (LlamaIndex Core)**。
  - 用于处理非结构化文档的混合检索 (Hybrid Search)，作为 Agent 的知识外挂。
- **模型接口**：兼容 OpenAI API 格式 (支持 OpenRouter, DeepSeek, Claude 等模型直连)。
- **数据存储**：本地文件系统 (Local File System) 为主，不引入 MySQL/Redis 等重型依赖。

---

## 技术选型

| 层级 | 技术 | 说明 |
|:---|:---|:---|
| 后端框架 | FastAPI+Uvicorn | 异步HTTP+SSE流式推送 |
| Agent引擎 | LangChain1.x create_agent | 非AgentExecutor，非遗留 create_react_agent |
| LLM | DeepSeek (langchain-deepseek) | 通过ChatDeepSeek原生接入，兼容OpenAI API格式 |
| RAG | LlamaIndex Core | 向量检索+BM25混合搜索 |
| Embedding | OpenAI text-embedding-3-small | 通过 OPENAI_BASE_URL可切换代理 |
| Token计数 | tiktoken cl100k_base | 精确token统计 |
| 前端框架 | Next.js14 App Router | TypeScript+React18 |
| UI | TailwindCSS+Shadcn/UI风格 | Apple风毛玻璃效果 |
| 代码编辑器 | Monaco Editor | 在线编辑Memory/Skill文件 |
| 状态管理 | React Context | 无Redux，单一 AppProvider |
| 存储 | 本地文件系统 | 无MySQL/Redis，JSON+ Markdown文件 |

---

## 项目结构

mini-openclaw/
├── backend/
│   ├── app.py              # FastAPI 入口,路由注册,启动初始化
│   ├── config.py           # 全局配置管理(config.json 持久化)
│   ├── requirements.txt    # Python 依赖
│   ├── .env.example        # 环境变量模板
│   ├── api/                # API 路由层
│   │   ├── chat.py         # POST /api/chat —SSE 流式对话
│   │   ├── sessions.py     # 会话CRUD +标题生成
│   │   ├── files.py        # 文件读写+技能列表
│   │   ├── tokens.py       # Token 统计
│   │   ├── compress.py     # 对话压缩
│   │   └── config_api.py   # RAG 模式开关
│   │
│   ├── graph/              # Agent 核心逻辑
│   │   ├── agent.py        # AgentManager — 构建 & 流式调用
│   │   ├── session_manager.py  # 会话持久化（JSON 文件）
│   │   ├── prompt_builder.py   # System Prompt 组装器
│   │   └── memory_indexer.py   # MEMORY.md 向量索引（RAG）
│   │
│   ├── tools/              # 5 个核心工具
│   │   ├── __init__.py     # 工具注册工厂
│   │   ├── terminal_tool.py    # 沙箱终端
│   │   ├── python_repl_tool.py # Python 解释器
│   │   ├── fetch_url_tool.py   # 网页抓取（HTML→Markdown）
│   │   ├── read_file_tool.py   # 沙箱文件读取
│   │   ├── search_knowledge_tool.py  # 知识库搜索
│   │   └── skills_scanner.py   # 技能目录扫描器
│   │
│   ├── workspace/          # System Prompt 组件
│   │   ├── SOUL.md         # 人格、语气、边界
│   │   ├── IDENTITY.md     # 名称、风格、Emoji
│   │   ├── USER.md         # 用户画像
│   │   └── AGENTS.md       # 操作指南 & 记忆/技能协议
│   │
│   ├── skills/             # 技能目录（每个技能一个子目录）
│   │   └── get_weather/
│   │       └── SKILL.md    # 示例：天气查询技能
│   │
│   ├── memory/
│   │   └── MEMORY.md       # 跨会话长期记忆
│   │
│   ├── knowledge/          # 知识库文档（供 RAG 检索）summary结果
│   │
│   ├── sessions/           # 会话 JSON 文件
│   │   └── archive/        # 压缩归档
│   │
│   ├── storage/            # LlamaIndex 持久化索引
│   │   └── memory_index/   # MEMORY.md 专用索引
│   │
│   └── SKILLS_SNAPSHOT.md  # 技能快照（启动时自动生成）
│
├── frontend/               # Next.js 14+
│   └── src/
│       ├── app/
│       │   ├── layout.tsx      # Next.js 根布局
│       │   ├── page.tsx        # 主页面（三栏布局）
│       │   └── globals.css     # 全局样式
│       │
│       ├── lib/
│       │   ├── store.tsx       # React Context 状态管理
│       │   └── api.ts          # 后端 API 客户端
│       │
│       └── components/
│           ├── chat/
│           │   ├── ChatPanel.tsx      # 聊天面板（消息列表 + 输入框）
│           │   ├── ChatMessage.tsx    # 消息气泡（Markdown 渲染）
│           │   ├── ChatInput.tsx      # 输入框
│           │   ├── ThoughtChain.tsx   # 工具调用思维链（可折叠）
│           │   └── RetrievalCard.tsx  # RAG 检索结果卡片
│           │
│           ├── layout/
│           │   ├── Navbar.tsx         # 顶部导航栏
│           │   ├── Sidebar.tsx        # 左侧边栏(会话列表+Raw Messages)
│           │   └── ResizeHandle.tsx   # 面板拖拽分隔条
│           │
│           └── editor/
│               └── InspectorPanel.tsx  # 右侧检查器(Monaco 编辑器)
│
└── README.md

---

## 环境配置

复制`.env.example` 为`.env` 并填入API Key:

```bash
cd backend
cp .env.example .env
```

```bash
# DeepSeek(Agent 主模型)
DEEPSEEK_API_KEY=sk-xxx
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# OpenAI(Embedding 模型,用于知识库&RAG 检索)
OPENAI_API_KEY=sk-xxx
OPENAI_BASE_URL=https://api.openai.com/v1
EMBEDDING_MODEL=text-embedding-3-small
```

OPENAI_BASE_URL 支持换成任意兼容OpenAI Embedding 接口的代理地址。

---

## 启动方式
```bash
# 后端(端口8002)
cd backend
pip install -r requirements.txt
uvicorn app:app --port 8002 --host 0.0.0.0 --reload

# 前端(端口3000)
cd frontend
npm install
npm run dev
```

本机访问 `http://localhost:3000`，局域网内其他设备访问 `http://<本机IP>:3000`。

---

## 后端架构详解

### 应用入口 app.py

启动时通过`lifespan` 执行三步初始化:
```bash
1. `scan_skills()` → 扫描skills/**/SKILL.md,生成SKILLS_SNAPSHOT.md
2. `agent_manager.initialize()` → 创建ChatDeepSeek LLM 实例,注册5个工具
3. `memory_indexer.rebuild_index()` → 构建MEMORY.md 向量索引(供RAG 使用)
```
随后注册6个API 路由模块,所有路由统一挂载在/api 前缀下。

---

### Agent 引擎 graph/

#### agent.py — AgentManager

核心单例类,管理Agent 的生命周期。

| 方法 | 职责 |
|:---|:---|
| initialize(base_dir) | 创建 ChatDeepSeek LLM、加载工具列表、初始化 SessionManager |
| _build_agent() | **每次调用都重建**，确保读取最新的SystemPrompt和 RAG配置 |
| _build_messages() | 将会话历史（dict列表）转换为LangChain的 HumanMessage/ AIMessage |
| astream(message, history) | 核心流式方法，依次yield 6种事件 |

**astream()的流式事件序列:**
[RAG模式] retrieval → token... → tool_start → tool_end → new_response → token... → done
[普通模式] token... → tool_start → tool_end → new_response → token... → done

关键机制:
- **多段响应**: Agent 每次执行完工具后再次生成文本时,会yield 一个new_response 事件,前端据此创建新的助手消息气泡
- **RAG 注入**: 如果开启RAG 模式,在调用Agent 之前先检索MEMORY.md,将结果作为临时上下文追加到history 尾部(不持久化到会话文件)

#### session_manager.py — 会话持久化

以JSON 文件管理每个会话的完整历史。

核心方法:

| 方法 | 说明 |
|:---|:---|
| load_session(id) | 返回原始消息数组 |
| load_session_for_agent(id) | **为LLM优化**：合并连续的assistant消息、注入 compressed_context |
| save_message(id, role, content, tool_calls) | 追加消息到JSON文件 |
| compress_history(id, summary, n) | 归档前N条消息到 sessions/archive/，摘要写入 compressed_context |
| get_compressed_context(id) | 获取压缩摘要 (多次压缩用 --- 分隔) |

`load_session_for_agent()`与`load_session()`的区别:LLM 要求严格的user/assistant 交替,而实际存储中可能有连续多条assistant 消息(工具调用产生的多段响应),此方法将它们合并为单条。如果存在`compressed_context`,还会在消息列表头部插入一条虚拟的assistant 消息承载历史摘要。

#### prompt_builder.py — System Prompt 组装

按固定顺序拼接6个Markdown 文件为完整的System Prompt:

1. `SKILLS_SNAPSHOT.md` — 可用技能清单
2. `workspace/SOUL.md` — 人格、语气、边界
3. `workspace/IDENTITY.md` — 名称、风格
4. `workspace/USER.md` — 用户画像
5. `workspace/AGENTS.md` — 行为准则&记忆操作指南&协议
6. `memory/MEMORY.md` — 跨会话长期记忆(RAG 模式下替换为引导语)

每个文件内容上限 **20,000字符** ,超出则截断并标记 `...[truncated]`。

RAG 模式下的变化: 跳过MEMORY.md,改为追加一段RAG 引导语,告知Agent 记忆将通过检索动态注入。

#### AGENTS.md 的默认配置 (核心修正)
由于 Agent 默认并不知道它是通过“阅读文件”来学习技能的，因此必须在初始化时生成一个包含明确指令的 `AGENTS.md`。

- 必须包含的元指令 (Meta-Instructions)：
```
# 操作指南

## 技能调用协议 (SKILL PROTOCOL)
你拥有一个技能列表 (SKILLS_SNAPSHOT)，其中列出了你可以使用的能力及其定义文件的位置。

**当你要使用某个技能时，必须严格遵守以下步骤:**

1. 你的第一步行动永远是使用 `read_file` 工具读取该技能对应的 `location` 路径下的 Markdown 文件。
2. 仔细阅读文件中的内容、步骤和示例。
3. 根据文件中的指示，结合你内置的 Core Tools (terminal, python_repl, fetch_url) 来执行具体任务。

**禁止**直接猜测技能的参数或用法，必须先读取文件!

## 记忆协议 (MEMORY PROTOCOL)

### 长期记忆
- 文件位置: `memory/MEMORY.md`
- 当对话中出现值得长期记住的信息时 (如用户偏好、重要决策)，使用 `terminal` 工具将内容追加到 MEMORY.md

### 会话日志
- 文件位置: `memory/logs/YYYY-MM-DD.md`
- 每日自动归档的对话摘要

### 记忆读取
- 在回答问题前，检查 MEMORY.md 中是否有相关的历史信息
- 优先使用已记录的用户偏好

## 工具使用规范
1. **terminal**: 用于执行 Shell 命令，注意安全边界
2. **python_repl**: 用于计算、数据处理、脚本执行
3. **fetch_url**: 用于获取网页内容，返回清洗后的 Markdown
4. **read_file**: 用于读取本地文件，是技能调用的第一步
5. **search_knowledge_base**: 用于在知识库中检索信息

## 回复规范
- 执行工具调用前，简要说明你的意图
- 工具执行结果要进行摘要，不要原封不动返回
- 遇到错误时，尝试其他方案或向用户说明
```

#### memory_indexer.py — MEMORY.md 向量索引

专门为`memory/MEMORY.md` 构建的LlamaIndex 向量索引,独立于知识库索引(存储路径`storage/memory_index/`)。

| 方法 | 说明 |
|:---|:---|
| rebuild_index() | 读取MEMORY.md → SentenceSplitter(chunk_size=256, overlap=32)切片 → 构建VectorStoreIndex → 持久化 |
| retrieve(query, top_k=3) | 语义检索，返回 [{text, score, source}] |
| _maybe_rebuild() | 每次检索前通过MD5检查文件是否变更，变更则自动重建 |

另外,当用户通过Monaco 编辑器保存MEMORY.md时,`files.py` 的`save_file` 端点也会主动触发`rebuild_index()`。

本系统不依赖外部向量数据库（Milvus / Pinecone 等），
但会在本地构建轻量向量索引。

---

### 五大核心工具 tools/

所有工具均继承LangChain_core.tools 的`BaseTool`,通过`tools/__init__.py` 的`get_all_tools(base_dir)`统一注册。

| 工具 | 文件 | 功能 | 安全措施 |
|:---|:---|:---|:---|
| terminal | terminal_tool.py | 执行Shell命令 | 黑名单（`rm -rf /`、`mkfs`、`shutdown` 等）；CWD 限制在项目根目录；30s超时；输出截断5000字符 |
| python_repl | python_repl_tool.py | 执行Python代码 | 封装LangChain原生 PythonREPLTool |
| fetch_url | fetch_url_tool.py | 抓取网页内容 | 自动识别JSON/HTML；HTML通过html2text转Markdown；15s超时; 输出截断5000字符 |
| read_file | read_file_tool.py | 读取项目内文件 | 路径遍历检查（不可逃逸出 `root_dir`）；输出截断10,000字符 |
| search_knowledge_base | search_knowledge_tool.py | 搜索知识库 | 惰性加载索引；从knowledge/目录构建；top-3语义检索；必须实现 **Hybrid Search** (关键词检索 BM25 + 向量检索 Vector Search)；索引持久化到 storage/ |

#### skills_scanner.py

非工具,而是启动时执行的扫描器:遍历`skills/*/SKILL.md`,解析YAML frontmatter (`name`、`description`),生成XML 格式的`SKILLS_SNAPSHOT.md`。该快照被纳入System Prompt,让Agent 知道有哪些可用技能。

---

### API 层 api/

#### chat.py — 流式对话

`POST /api/chat` 是系统的核心端点。

**请求体:**
```json
{"message":"你好","session_id":"abc123","stream":true}
```
- Response: 支持 **SSE (Server-Sent Events)** 流式输出，实时推送 Agent 的思考过程 (Thought/Tool Calls) 和最终回复。
内部流程：
1. 调用 `session_manager.load_session_for_agent()` 获取经过合并优化的历史
2. 判断是否为会话的第一条消息（用于后续自动生成标题）
3. 创建 `event_generator()`，内部调用 `agent_manager.astream()`
4. 按段（segment）追踪响应——每次工具执行后 Agent 重新生成文本时开启新段
5. `done` 事件到达后：保存用户消息 + 每段助手消息到会话文件
6. 如果是首条消息，额外调用 DeepSeek 生成 ≤10 字的中文标题
SSE 事件类型：
| 事件            | 数据                     | 触发时机                  |
| :------------ | :--------------------- | :-------------------- |
| retrieval     | {query,results}        | RAG模式检索完成后            |
| token         | {content}              | LLM输出每个token          |
| tool_start   | {tool,input}           | Agent调用工具前            |
| tool_end     | {tool,output}          | 工具返回结果后               |
| new_response | 0                      | 工具执行完毕、Agent开始新一轮文本生成 |
| done          | {content, session_id} | 整轮响应结束                |
| title         | {session_id,title}    | 首次对话后自动生成标题           |
| error         | {error}                | 发生异常                  |

#### sessions.py — 会话管理
| 端点                                | 方法     | 说明                                  |
| :-------------------------------- | :----- | :---------------------------------- |
| /api/sessions                     | GET    | 列出所有会话 (按更新时间倒序)                    |
| /api/sessions                     | POST   | 创建新会话 (UUID命名)                      |
| /api/sessions/{id}                | PUT    | 重命名会话                               |
| /api/sessions/{id}                | DELETE | 删除会话                                |
| /api/sessions/{id}/messages       | GET    | 获取完整消息（含System Prompt）              |
| /api/sessions/{id}/history        | GET    | 获取对话历史（不含System Prompt，含tool calls） |
| /api/sessions/{id}/generate-title | POST   | AI生成标题                              |

#### files.py — 文件操作
| 端点                  | 方法   | 说明         |
| :------------------ | :--- | :--------- |
| /api/files?path=... | GET  | 读取文件内容     |
| /api/files          | POST | 保存文件（编辑器用） |
| /api/skills         | GET  | 列出可用技能     |

路径白名单机制:
- **允许的目录前缀**: `workspace/`、`memory/`、`skills/`、`knowledge/`
- **允许的根目录文件**: `SKILLS_SNAPSHOT.md`
- 包含路径遍历检测（..攻击防护）
保存`memory/MEMORY.md` 时会自动触发`memory_indexer.rebuild_index()`

#### tokens.py — Token 统计
| 端点                       | 方法   | 说明                                                  |
| :----------------------- | :--- | :-------------------------------------------------- |
| /api/tokens/session/{id} | GET  | 返回 {system_tokens, message_tokens, total_tokens} |
| /api/tokens/files        | POST | 批量统计文件 token 数，body: {paths: [...]}                |

使用`tiktoken` 的`cl100k_base` 编码器,与GPT-4系列一致。

#### compress.py — 对话压缩
| 端点                          | 方法   | 说明           |
| :-------------------------- | :--- | :----------- |
| /api/sessions/{id}/compress | POST | 压缩前 50% 历史消息 |

流程：
1. 检查消息数量 ≥ 4
2. 取前 50% 消息（最少 4 条）
3. 调用 DeepSeek（temperature=0.3）生成中文摘要（≤500 字）
4. 调用 session_manager.compress_history() 归档 + 写入摘要
5. 返回 {archived_count, remaining_count}
归档文件存储在 sessions/archive/{session_id}_{timestamp}.json。

#### config_api.py — 配置管理
| 端点                   | 方法  | 说明                              |
| :------------------- | :-- | :------------------------------ |
| /api/config/rag-mode | GET | 获取 RAG 模式状态                     |
| /api/config/rag-mode | PUT | 切换 RAG 模式，body: {enabled: bool} |
配置持久化到backend/config.json。

---

### System Prompt 组装

Agent 每次被调用时都会**重新读取**所有Markdown 文件并组装System Prompt,确保workspace 文件的实时编辑能立即生效:
┌───────────────────────────────────┐
│ <!-- Skills Snapshot -->          │  ← SKILLS_SNAPSHOT.md
│ <!-- Soul -->                     │  ← workspace/SOUL.md
│ <!-- Identity -->                 │  ← workspace/IDENTITY.md
│ <!-- User Profile -->             │  ← workspace/USER.md
│ <!-- Agents Guide -->             │  ← workspace/AGENTS.md
│ <!-- Long-term Memory -->         │  ← memory/MEMORY.md（RAG 模式下替换为引导语）
└───────────────────────────────────┘
每个组件间以 \n\n 分隔，每个组件带 HTML 注释标签便于调试定位。

---

### 会话存储格式

**文件路径:** `sessions/{session_id}.json`

```json
{
  "title": "讨论天气查询",
  "created_at": 1706000000.0,
  "updated_at": 1706000100.0,
  "compressed_context": "用户之前询问了北京天气...",
  "messages": [
    {"role": "user", "content": "北京天气怎么样?"},
    {
      "role": "assistant",
      "content": "让我查一下...",
      "tool_calls": [
        {"tool": "terminal", "input": "curl wttr.in/Beijing", "output": "..."}
      ]
    },
    {"role": "assistant", "content": "北京今天晴,气温25°C。"}
  ]
}
```

说明：
- **v1 兼容**：如果文件内容是纯数组 [...]，_read_file() 会自动迁移为 v2 格式
- **多段 assistant**：一次工具调用后会产生多条连续的 assistant 消息
- **compressed_context**：可选字段，多次压缩用 --- 分隔

---

### Skills 技能系统

技能不是Python 函数,而是 **纯Markdown 指令文件**。Agent 通过`read_file` 工具读取SKILL.md,理解步骤后用核心工具执行。

**目录结构:**
```
skills/
└── get_weather/
    └── SKILL.md
```

**SKILL.md 格式**:
```
---
name: 天气查询
description: 查询指定城市的天气信息
---

## 步骤
1. 使用 `fetch_url` 工具访问 wttr.in/{城市名}
2. 解析返回的天气数据
3. 以友好的格式回复用户
```

在 Agent 启动或会话开始时，系统扫描 `skills` 文件夹，读取每个 `SKILL.md` 的元数据 (Frontmatter)，并将其汇总生成 `SKILLS_SNAPSHOT.md`。
```
`SKILLS_SNAPSHOT.md` 示例：
<available_skills>
  <skill>
    <name>get_weather</name>
    <description>获取指定城市的实时天气信息</description>
    <location>./backend/skills/get_weather/SKILL.md</location>
  </skill>
</available_skills>
```
注意：location 使用相对路径。

Agent Skills 调用流程 (Execution)
这是本系统最独特的地方：
1. 感知：Agent 在 System Prompt 中看到 available_skills 列表。
2. 决策：当用户请求 “查询北京天气” 时，Agent 发现 get_weather 技能匹配。
3. 行动 (Tool Call)：Agent 不调用 get_weather() 函数 (因为它不存在)，而是调用 read_file(path="./backend/skills/get_weather/SKILL.md")。
4. 学习与执行：Agent 读取 Markdown 内容，理解操作步骤 (例如：" 使用 fetch_url 访问某天气 API"或" 使用 python_repl 运行以下代码 ")，然后**动态调用 Core Tools** (Terminal/Python) 来完成任务。

---

## 前端架构概览
三栏IDE 风格布局,基于Flexbox +可拖拽分隔条:
┌─────────────────────────────────────────────────────────────┐
│  Navbar (mini OpenClaw / 代码仓库)                          │
├──────────┬─────────────────────────────┬──────────────────┤
│ Sidebar  │      ChatPanel              │ InspectorPanel   │
│          │                             │                  │
│ 会话列表  │    消息气泡                  │ Memory / Skills  │
│          │    ├─ ThoughtChain          │ 文件列表          │
│ Raw Msgs │    ├─ RetrievalCard         │                  │
│ 扳手/RAG │    └─ Markdown 内容         │ Monaco 编辑器    │
│ Token 统计│                             │ Token 统计        │
│          │    ChatInput                │                  │
├──────────┴─────────────────────────────┴──────────────────┤
│  ResizeHandle (可拖拽)                                      │
└─────────────────────────────────────────────────────────────┘
**状态管理**：全部通过 `store.tsx` 的 React Context 管理，包括消息列表、会话切换、面板宽度、流式状态、压缩状态、RAG 模式等。
**API 客户端**（`api.ts`）：
- `streamChat()` 实现了自定义的 SSE 解析器（因为浏览器原生 `EventSource` 只支持 GET，而聊天接口是 POST）
- `API_BASE` 动态取 `window.location.hostname`，自动适配本机 / 局域网访问

### 1. 设计理念与布局架构
前端采用 IDE (集成开发环境) 风格，三栏式布局。
- 左侧 (Sidebar): 导航 (Chat/Memory/Skills) + 会话列表。
- 中间 (Stage): 对话流 + **思考链可视化 (Collapsible Thoughts)**。
- 右侧 (Inspector): Monaco Editor，用于实时查看/编辑正在使用的 `SKILL.md` 或 `MEMORY.md`。

### 2. 技术栈
- 框架: Next.js 14+ (App Router), TypeScript
- UI: Shadcn/UI, Tailwind CSS, Lucide Icons
- Editor: Monaco Editor (配置为 Light Theme)

### 3. UI/UX 风格规范
- 色调: 浅色 Apple 风格 (Frosty Glass)。
  - 背景: 纯白/极浅灰 (`#fafafa`)，高透毛玻璃效果。
  - 强调色: 克莱因蓝 (Klein Blue) 或 活力橙。
- 导航栏: 顶部固定，半透明。
  - 左中: `"mini OpenClaw"`
  - 右侧: `"代码仓库"` (链接至 `https://github.com/huochai01`)。


---

## 核心数据流

### 用户发送消息
前端                                    后端
 │
 ├─ store.sendMessage(text)
 │   ├─ 创建 user + assistant 占位消息
 │   └─ streamChat(text, sessionId) ──────→ POST /api/chat
 │                                           │
 │                                           ├─ load_session_for_agent()
 │                                           │   ├─ 合并连续 assistant 消息
 │                                           │   └─ 注入 compressed_context
 │                                           │
 │                                           ├─ [RAG] memory_indexer.retrieve()
 │                                           │   └─ yield retrieval 事件
 │                                           │
 │                                           ├─ _build_agent()
 │                                           │   ├─ build_system_prompt()
 │                                           │   └─ create_agent(llm, tools, prompt)
 │                                           │
 │   ← SSE: token ──────────────────────────├─ agent.astream()
 │   ← SSE: tool_start ────────────────────│   ├─ yield token/tool_start/tool_end
 │   ← SSE: tool_end ──────────────────────│   └─ yield done
 │   ← SSE: new_response ──────────────────│
 │   ← SSE: token ──────────────────────────│
 │   ← SSE: done ───────────────────────────├─ save_message(user + assistant segments)
 │                                           │
 │   ← SSE: title ──────────────────────────└─ [首次] _generate_title()
 │
 ├─ 实时更新 messages state
 └─ 刷新 sessions 列表

### RAG 检索模式
用户开启 RAG ──→ PUT /api/config/rag-mode {enabled: true}
                  └─ config.json 写入 {"rag_mode": true}

用户发送消息 ──→ agent.astream()
                  │
                  ├─ get_rag_mode() → true
                  ├─ memory_indexer.retrieve(query)
                  │   ├─ _maybe_rebuild()  // MD5 检测变更
                  │   └─ index.as_retriever(top_k=3)
                  │
                  ├─ yield {"type": "retrieval", results: [...]}
                  ├─ 将检索结果拼接为 "[记忆检索结果]" 上下文
                  └─ 追加到 history 末尾（仅当次请求，不持久化）

前端收到 retrieval 事件 ──→ 存入 message.retrievals
                            └─ RetrievalCard 渲染紫色折叠卡片

### 对话压缩
用户点击扳手 ──→ 确认弹窗 ──→ POST /api/sessions/{id}/compress
                                │
                                ├─ 取前 50% 消息（≥4 条）
                                ├─ DeepSeek 生成中文摘要（≤500字）
                                ├─ 归档到 sessions/archive/
                                ├─ 从 session 中删除这些消息
                                └─ 摘要写入 compressed_context

下次调用 Agent ──→ load_session_for_agent()
                    └─ 在消息列表头部插入:
                       {"role": "assistant", "content": "[以下是之前对话的摘要]\n{摘要}"}

---

## 关键设计决策

| 决策 | 理由 |
|:---|:---|
| 使用create_agent() 而非 AgentExecutor | LangChain1.x推荐的现代API，支持原生流式 |
| 每次请求重建Agent | 确保SystemPrompt反映workspace文件的实时编辑 |
| 文件驱动而非数据库 | 降低部署门槛，所有状态对开发者透明可查 |
| 技能=Markdown指令 | Agent自主阅读并执行，不需要注册新的Python函数 |
| 多段响应分别存储 | 忠实保留工具调用前后的文本段，RawMessages可完整审查 |
| SystemPrompt组件截断20K | 防止MEMORY.md膨胀导致上下文溢出 |
| RAG检索结果不持久化 | 避免会话文件膨胀，检索上下文仅用于当次请求 |
| 路径白名单+遍历检测 | 双重防护，终端和文件读取工具均受沙箱约束 |
| window.location.hostname 动态API地址 | 一份代码同时支持本机和局域网访问 |

## API 接口速查

| 路径 | 方法 | 说明 |
|:---|:---|:---|
| /api/chat | POST | SSE 流式对话 |
| /api/sessions | GET | 列出所有会话 |
| /api/sessions | POST | 创建新会话 |
| /api/sessions/{id} | PUT | 重命名会话 |
| /api/sessions/{id} | DELETE | 删除会话 |
| /api/sessions/{id}/messages | GET | 获取完整消息（含 System Prompt） |
| /api/sessions/{id}/history | GET | 获取对话历史 |
| /api/sessions/{id}/generate-title | POST | AI 生成标题 |
| /api/sessions/{id}/compress | POST | 压缩对话历史 |
| /api/files?path=... | GET | 读取文件 |
| /api/files | POST | 保存文件 |
| /api/skills | GET | 列出技能 |
| /api/tokens/session/{id} | GET | 会话 Token 统计 |
| /api/tokens/files | POST | 文件 Token 统计 |
| /api/config/rag-mode | GET | 获取 RAG 模式状态 |
| /api/config/rag-mode | PUT | 切换 RAG 模式 |