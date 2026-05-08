# Yang RAG System - 系统文档

> 企业级检索增强生成（RAG）系统，基于 LangChain 构建，支持多种文档格式、向量存储和 MCP 协议集成。

---

## 目录

- [系统概述](#系统概述)
- [系统架构](#系统架构)
- [RAG 完整流程说明](#rag-完整流程说明)
- [代码模块详解](#代码模块详解)
- [快速开始](#快速开始)
- [API 使用指南](#api-使用指南)
- [MCP 协议集成](#mcp-协议集成)
- [跨设备接入指南](#跨设备接入指南)
- [配置参考](#配置参考)
- [最佳实践](#最佳实践)
- [常见问题](#常见问题)

---

## 系统概述

### 什么是 Yang RAG System

Yang RAG System 是一个企业级 RAG（Retrieval-Augmented Generation）系统，专注于为代码助手和知识管理系统提供智能检索能力。

### 核心能力

| 能力 | 描述 |
|------|------|
| **知识库管理** | 支持多格式文档上传、智能分块、向量存储 |
| **语义检索** | 基于 Embedding 的向量相似度搜索 |
| **混合检索** | 结合语义和关键词检索，提升准确率 |
| **答案合成** | 基于 LLM 的 RAG 答案生成 |
| **MCP 协议** | 支持 Cursor、Claude Code 等 Code Agent |
| **OpenAI 兼容** | 提供 `/v1/chat/completions` 兼容接口 |

### 技术栈

- **框架**: LangChain
- **API**: FastAPI + Uvicorn
- **向量存储**: ChromaDB / FAISS / Milvus
- **文档处理**: pypdf, python-docx, python-pptx
- **LLM**: OpenAI GPT 系列（兼容其他 OpenAI 兼容 API）

### 近期补齐项（2026-04）

以下功能已从“部分实现”补齐为“可用闭环”：

1. **知识库元数据持久化闭环**：文档上传/文本写入/知识库更新后会自动刷新并落盘到 `data/kb_metadata`，服务重启后可自动恢复。
2. **知识库管理 CRUD 完整化**：新增 `PATCH /api/v1/knowledge/{kb_id}`，支持修改知识库名称和描述。
3. **检索策略可配置**：`search` 与 `chat/completions` 均支持 `vector/hybrid` 检索模式，以及可选 reranker 参数。
4. **管理后台统计改为实时**：Dashboard 不再使用硬编码数据，直接读取知识库、文档总量与 RAG 服务健康状态。

---

## 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         客户端层                                  │
├──────────────────┬──────────────────┬───────────────────────────┤
│   Cursor         │   Claude Code     │   其他应用 / curl / SDK    │
└────────┬────────┴────────┬─────────┴────────────┬────────────────┘
         │                 │                      │
         ▼                 ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                      协议接口层                                   │
├──────────────────────────┬──────────────────────────────────────┤
│    MCP Server (stdio)    │      REST API (HTTP)                 │
│    src/mcp_server/       │      src/api/main.py                 │
└──────────────────────────┴──────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      核心服务层                                   │
├──────────────────┬──────────────────┬───────────────────────────┤
│  KnowledgeManager │    Retrieval     │    Generation              │
│  src/knowledge/   │  src/retrieval/  │  src/generation/           │
│                   │                  │                           │
│  - loader.py      │  - retriever.py  │  - synthesizer.py          │
│  - splitter.py    │  - reranker.py   │                            │
│  - embedder.py    │                  │                            │
│  - store.py       │                  │                            │
│  - manager.py     │                  │                            │
└──────────────────┴──────────────────┴───────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      数据存储层                                   │
├──────────────────┬──────────────────┬───────────────────────────┤
│   ChromaDB       │   FAISS          │   文件系统                 │
│   (向量存储)      │   (向量存储)      │   (KB 元数据)             │
└──────────────────┴──────────────────┴───────────────────────────┘
```

### 数据流

#### 文档上传流程

```
用户上传文档 → Loader 解析 → Splitter 分块 → Embedder 向量化 → ChromaDB 存储
```

1. **Loader**: 解析 PDF/DOCX/TXT 等多格式文档
2. **Splitter**: 将长文档拆分为 500 字符的块（可配置）
3. **Embedder**: 使用 OpenAI Embedding 将文本转为 1536 维向量
4. **Store**: 存储到 ChromaDB 向量数据库

#### 查询/问答流程（核心 RAG 流程）

```
用户问题 → Embedder 向量化 → 向量检索 → 重排序 → 格式化上下文 → LLM 生成 → 返回答案
```

1. **Embedding**: 将用户问题转为向量
2. **检索**: 在 ChromaDB 中找到最相似的 K 个文档块
3. **重排序**: 使用 Cross-Encoder 进一步优化相关性
4. **格式化**: 将检索结果整理为上下文 prompt
5. **LLM 生成**: 调用 LLM（GPT-4o 等）生成答案
6. **返回**: 流式或完整返回答案及来源

### 完整双 Agent 架构（推荐）

这是通过 MCP 与 Cursor/Claude Code 集成的推荐架构：

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        Cursor / Claude Code (主 Agent)                       │
│                                                                              │
│   用户: "帮我实现用户认证功能"                                                │
│       ↓                                                                     │
│   Agent 分析需求 → 决定调用 MCP 工具                                         │
└──────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        │ MCP JSON-RPC
                                        ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                        Yang RAG System (知识 Agent)                          │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                    1. 接收查询                                         │   │
│   │                    2. 向量检索 → 找到相关文档片段                        │   │
│   │                    3. 格式化上下文                                       │   │
│   │                    4. 组装 Prompt (问题 + 上下文)                        │   │
│   │                    5. 调用 LLM (GPT-4o) 生成答案                        │   │
│   │                    6. 流式返回答案 + 来源                                 │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                         LLM (外部服务)                                  │   │
│   │                    OpenAI / Azure OpenAI / Ollama                      │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        │ 返回检索结果和生成答案
                                        ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                        Cursor / Claude Code (主 Agent)                       │
│                                                                              │
│   接收 RAG 返回的答案 → 基于上下文编写代码 → 展示给用户                       │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 为什么需要 LLM 生成？

检索返回的是**原始文档片段**，LLM 的作用是：

| 步骤 | 输入 | 输出 |
|------|------|------|
| 检索 | 用户问题 | 相关文档片段（原始文本） |
| LLM 生成 | 问题 + 文档片段 | 整理后的答案（可读性强） |

**示例**：

```
用户问题: "如何配置数据库连接池？"

检索结果（原始）:
- 片段1: "connection_pool_size = 50"
- 片段2: "pool = Pool(host='localhost')"

LLM 生成（可读）:
"配置数据库连接池需要设置 pool_size 参数，示例代码：
pool = Pool(host='localhost', connection_pool_size=50)
建议根据服务器内存调整，一般设置为 CPU 核心数的 2-4 倍。"
```

---

## RAG 完整流程说明

### 流程概览

Yang RAG System 实现了标准的 RAG 流程，完整处理链路如下：

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           文档处理流程                                    │
│                                                                         │
│  文档上传 ──→ Loader ──→ Splitter ──→ Embedder ──→ ChromaDB            │
│              (解析)      (分块)      (向量化)      (存储)                │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                           查询处理流程                                    │
│                                                                         │
│  用户问题 ──→ Embedder ──→ 向量检索 ──→ 重排序 ──→ 格式化 ──→ LLM ──→ 答案│
│             (向量化)     (Top-K)    (优化)    (Prompt)    (生成)         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 详细步骤说明

#### 阶段 1：文档处理（一次性）

| 步骤 | 组件 | 说明 |
|------|------|------|
| 1 | `loader.py` | 解析 PDF/DOCX/TXT 等格式，提取文本内容 |
| 2 | `splitter.py` | 将长文档拆分为 300-1000 字符的块 |
| 3 | `embedder.py` | 调用 OpenAI Embedding API，将文本转为 1536 维向量 |
| 4 | `store.py` | 将向量和元数据存储到 ChromaDB |

#### 阶段 2：查询处理（每次查询）

| 步骤 | 组件 | 说明 |
|------|------|------|
| 1 | `embedder.py` | 将用户问题转为向量 |
| 2 | `retriever.py` | 在向量数据库中检索最相似的 K 个文档块 |
| 3 | `reranker.py` | 使用 Cross-Encoder 进一步优化相关性排序 |
| 4 | `prompts.py` | 将检索结果格式化为上下文 Prompt |
| 5 | `synthesizer.py` | 调用 LLM，传入问题 + 上下文，生成答案 |
| 6 | 返回 | 流式或完整返回答案及来源引用 |

### Prompt 组装示例

```
System: 你是一个专业的知识库问答助手...
       规则：仅基于上下文回答、引用来源、清晰简洁...

Human: ## 用户问题
       如何在 FastAPI 中实现 JWT 认证？

       ## 检索到的上下文
       ### 来源 1: auth.md (相关度: 0.95)
       def create_access_token(data: dict):
           to_encode = data.copy()
           expire = datetime.utcnow() + timedelta(minutes=30)
           to_encode.update({"exp": expire})
           return jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")

       ### 来源 2: config.py (相关度: 0.87)
       SECRET_KEY = "your-secret-key-here"
       ALGORITHM = "HS256"

       ## 请基于以上上下文回答用户的问题：
```

---

## 代码模块详解

### 1. `src/knowledge/` - 知识库管理模块

#### `loader.py` - 文档加载器

负责从多种文件格式中提取文本内容。

```python
from src.knowledge.loader import get_loader

loader = get_loader()
documents = loader.load("path/to/document.pdf")
```

**支持的格式**:

| 格式 | 后缀 | 实现方式 |
|------|------|----------|
| PDF | `.pdf` | pypdf |
| Word | `.docx`, `.doc` | python-docx |
| 文本 | `.txt` | 原生读取 |
| Markdown | `.md`, `.markdown` | 原生读取 |
| HTML | `.html`, `.htm` | 原生读取 |
| PowerPoint | `.pptx`, `.ppt` | python-pptx |
| Excel | `.xlsx`, `.xls` | 原生读取（文本内容） |

#### `splitter.py` - 文本分块器

将长文档拆分为适合检索的较小块。

**分块策略**:

| 策略 | 类 | 适用场景 |
|------|-----|---------|
| `recursive` | `TextSplitter` | 通用文本 |
| `markdown` | `MarkdownSplitter` | Markdown 文档 |
| `code` | `CodeSplitter` | 代码文件 |
| `smart` | `HSplitter` | 自动选择最佳策略 |

```python
from src.knowledge.splitter import get_splitter

# 使用智能分块
splitter = get_splitter(splitter_type="smart", chunk_size=500, chunk_overlap=50)
chunks = splitter.split_documents(documents)
```

#### `embedder.py` - 向量化模块

将文本转换为向量表示。

```python
from src.knowledge.embedder import get_embedder

embedder = get_embedder(provider="openai", model="text-embedding-3-small")
vectors = embedder.embed_documents(texts)
```

#### `store.py` - 向量存储

管理向量数据库的读写操作。

```python
from src.knowledge.store import get_vector_store

store = get_vector_store(
    collection_name="my_kb",
    embedding_function=embedder
)
store.add_documents(chunks)
results = store.similarity_search(query="...", k=5)
```

**支持的向量存储**:

- **ChromaDB**: 默认，轻量级本地向量数据库
- **FAISS**: Facebook AI 相似度搜索库
- **Milvus**: 分布式向量数据库（需额外配置）

#### `manager.py` - 知识库管理器

核心类，管理多个知识库的生命周期。

```python
from src.knowledge.manager import get_kb_manager

manager = get_kb_manager()

# 创建知识库
kb = manager.create_knowledge_base(name="My Docs", description="我的文档")

# 添加文档
kb.add_document("./docs/guide.pdf")

# 搜索
results = kb.search(query="如何配置", top_k=5)

# 获取统计
stats = kb.get_stats()
```

**核心类**:

| 类 | 职责 |
|----|------|
| `KnowledgeBase` | 单个知识库的操作接口 |
| `KnowledgeBaseManager` | 管理多个知识库（单例模式） |

---

### 2. `src/retrieval/` - 检索模块

#### `retriever.py` - 检索器

提供多种检索策略。

**检索器类型**:

| 类型 | 类 | 描述 |
|------|-----|------|
| `vector` | `KnowledgeBaseRetriever` | 纯向量相似度检索 |
| `hybrid` | `HybridRetriever` | 向量 + 关键词混合检索 |
| `ensemble` | `EnsembleRetriever` | 多检索器融合 |

```python
from src.retrieval.retriever import create_retriever

# 向量检索
retriever = create_retriever(kb, retriever_type="vector", top_k=5)

# 混合检索（向量 70% + 关键词 30%）
retriever = create_retriever(kb, retriever_type="hybrid", vector_weight=0.7, keyword_weight=0.3)

results = retriever.search(query="Python 最佳实践")
```

#### `reranker.py` - 重排序

使用 Cross-Encoder 对初步检索结果进行重排序，提升相关性。

```python
from src.retrieval.reranker import get_reranker

reranker = get_reranker("cross-encoder")
reranked = reranker.rerank(query="...", documents=docs, top_k=3)
```

---

### 3. `src/generation/` - 生成模块

#### `synthesizer.py` - 答案合成器

结合检索结果和 LLM 生成答案。

**合成器类型**:

| 类型 | 类 | 适用场景 |
|------|-----|----------|
| `default` | `RAGSynthesizer` | 标准 RAG 问答 |
| `streaming` | `StreamingRAGSynthesizer` | 流式响应 |
| `code-agent` | `CodeAgentRAGSynthesizer` | 代码助手场景 |

```python
from src.generation.synthesizer import create_synthesizer

# 标准合成器
synthesizer = create_synthesizer(kb, synthesizer_type="default")

# 代码助手合成器
synthesizer = create_synthesizer(kb, synthesizer_type="code-agent")

# 执行问答
result = synthesizer.invoke(
    query="如何在 FastAPI 中实现认证？",
    return_sources=True
)

print(result["answer"])
print(result["sources"])
```

#### LLM 生成流程详解

`RAGSynthesizer` 是核心生成模块，其工作流程如下：

```
用户问题
    │
    ▼
┌─────────────────┐
│ 1. 检索文档       │ ← KnowledgeBase.search()
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 2. 重排序        │ ← CrossEncoder 优化相关性
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 3. 格式化上下文   │ ← format_context() 组装 prompt
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 4. 调用 LLM     │ ← LangChain Chain: Prompt + LLM + OutputParser
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 5. 返回结果      │ ← answer + sources
└─────────────────┘
```

**核心代码** (`synthesizer.py` 第 108-133 行):

```python
def _generate(self, query: str, context: str, conversation_history=None) -> str:
    """Generate answer using LLM."""
    from langchain_core.prompts import ChatPromptTemplate

    # 组装 prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", RAG_SYSTEM_PROMPT),
        ("human", RAG_HUMAN_TEMPLATE),  # 包含 {question} 和 {context}
    ])

    # 构建 chain 并调用 LLM
    chain = prompt | self.llm | StrOutputParser()
    response = chain.invoke({
        "question": query,
        "context": context,
    })
    return response
```

**使用的 Prompt 模板** (`prompts.py`):

```python
# 系统提示词
RAG_SYSTEM_PROMPT = """你是一个专业的知识库问答助手...
# 包含回答规则、上下文格式、输出格式等指令"""

# 用户提示词
RAG_HUMAN_TEMPLATE = """
## 用户问题
{question}

## 检索到的上下文
{context}

## 请基于以上上下文回答用户的问题：
"""
```

**流式返回实现**:

`StreamingRAGSynthesizer` 支持实时流式返回：

```python
# API 端点使用
@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest):
    if request.stream:
        return StreamingResponse(
            stream_chat_response(synthesizer, query, history),
            media_type="text/event-stream",
        )

async def stream_chat_response(synthesizer, query, history):
    results = synthesizer.invoke(query, history, return_sources=True)
    yield f"data: {json.dumps({'type': 'sources', 'data': results['sources']})}\n\n"
    for chunk in results["answer"]:
        yield f"data: {json.dumps({'type': 'content', 'data': chunk})}\n\n"
    yield "data: [DONE]\n\n"
```

---

### 4. `src/api/` - REST API 模块

基于 FastAPI 的 HTTP 接口，提供 OpenAI 兼容的 `/v1/chat/completions` 端点。

**API 端点**:

| 方法 | 路径 | 描述 |
|------|------|------|
| `GET` | `/` | 服务信息 |
| `GET` | `/health` | 健康检查 |
| `GET` | `/api/v1/knowledge` | 列出所有知识库 |
| `POST` | `/api/v1/knowledge` | 创建知识库 |
| `GET` | `/api/v1/knowledge/{kb_id}` | 获取知识库详情 |
| `PATCH` | `/api/v1/knowledge/{kb_id}` | 更新知识库名称/描述 |
| `DELETE` | `/api/v1/knowledge/{kb_id}` | 删除知识库 |
| `POST` | `/api/v1/knowledge/{kb_id}/upload` | 上传文档 |
| `POST` | `/api/v1/knowledge/{kb_id}/search` | 搜索知识库 |
| `POST` | `/v1/chat/completions` | OpenAI 兼容问答 |

**检索与重排参数（已支持）**:

- `retrieval_mode`: `vector` 或 `hybrid`
- `retrieval_top_k`: 初次召回数量
- `use_reranker`: 是否启用重排
- `reranker_type`: `simple` / `cross-encoder` / `llm`
- `rerank_top_k`: 重排后保留数量

**启动方式**:

```bash
# 开发模式（热重载）
python -m src.api.main

# 或使用 uvicorn
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

---

### 5. `src/mcp_server/` - MCP 协议模块

实现 Model Context Protocol，通过 stdio 与 Cursor、Claude Code 等 Code Agent 通信。

**架构**:

```
Cursor/Claude Code  ←→  MCP Server (stdio)  ←→  Knowledge Manager
                     JSON-RPC
```

**可用工具**:

| 工具 | 描述 | 参数 |
|------|------|------|
| `search_knowledge_base` | 语义搜索 | `query`, `knowledge_base_id?`, `top_k?` |
| `list_knowledge_bases` | 列出知识库 | - |
| `query_with_context` | RAG 问答 | `question`, `knowledge_base_id?` |
| `create_knowledge_base` | 创建知识库 | `name`, `description?` |

**启动方式**:

```bash
python -m src.mcp_server.server
```

---

### 6. `src/core/` - 核心配置模块

#### `config.py` - 配置管理

使用 Pydantic Settings 管理环境变量配置。

```python
from src.core.config import settings

print(settings.openai_api_key)
print(settings.retrieval_top_k)
```

#### `prompts.py` - 提示词模板

预定义的系统提示词和用户模板。

---

## 快速开始

### 1. 安装依赖

```bash
cd /Users/leo/IdeaProjects/yang/rag
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填写你的 OpenAI API Key
```

**最小配置**:

```env
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
```

### 3. 启动服务

**方式一：REST API**

```bash
python -m src.api.main
# 服务运行在 http://localhost:8000
```

**方式二：MCP Server**

```bash
python -m src.mcp_server.server
# 通过 stdio 通信
```

### 4. 使用示例

```python
from src.knowledge.manager import get_kb_manager
from src.generation.synthesizer import create_synthesizer

# 获取管理器
manager = get_kb_manager()

# 创建知识库
kb = manager.create_knowledge_base(
    name="My Docs",
    description="我的文档"
)

# 添加文档
kb.add_document("./docs/guide.pdf")

# 创建合成器并问答
synthesizer = create_synthesizer(kb)
result = synthesizer.invoke("如何配置系统？")

print(result["answer"])
```

---

## API 使用指南

### 基础设置

```bash
# 设置 API 地址和密钥
export API_URL="http://localhost:8000"
export API_KEY="rag-secret-key"
```

### 创建知识库

```bash
curl -X POST "$API_URL/api/v1/knowledge" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "name": "My Docs",
    "description": "我的文档知识库"
  }'
```

**响应示例**:

```json
{
  "id": "a1b2c3d4e5f6g7h8",
  "name": "My Docs",
  "description": "我的文档知识库",
  "document_count": 0,
  "chunk_count": 0,
  "embedding_model": "text-embedding-3-small",
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```

### 上传文档

```bash
curl -X POST "$API_URL/api/v1/knowledge/{kb_id}/upload" \
  -F "file=@./docs/guide.pdf" \
  -H "X-API-Key: $API_KEY"
```

**响应示例**:

```json
{
  "status": "success",
  "file_name": "guide.pdf",
  "document_count": 1,
  "chunk_count": 15,
  "knowledge_base_id": "a1b2c3d4e5f6g7h8"
}
```

### 更新知识库信息

```bash
curl -X PATCH "$API_URL/api/v1/knowledge/{kb_id}" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "name": "My Docs v2",
    "description": "更新后的描述"
  }'
```

### 搜索知识库

```bash
curl -X POST "$API_URL/api/v1/knowledge/{kb_id}/search" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "query": "如何配置系统",
    "top_k": 5,
    "retrieval_mode": "hybrid",
    "retrieval_top_k": 10,
    "use_reranker": true,
    "reranker_type": "simple",
    "rerank_top_k": 5
  }'
```

### RAG 问答

```bash
curl -X POST "$API_URL/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "messages": [
      {"role": "user", "content": "如何在项目中配置日志？"}
    ],
    "knowledge_base_id": "{kb_id}",
    "retrieval_mode": "hybrid",
    "retrieval_top_k": 8,
    "use_reranker": true,
    "reranker_type": "simple",
    "rerank_top_k": 3,
    "temperature": 0.7,
    "max_tokens": 2000
  }'
```

### 流式响应

```bash
curl -X POST "$API_URL/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "messages": [{"role": "user", "content": "解释 RAG 原理"}],
    "knowledge_base_id": "{kb_id}",
    "stream": true
  }'
```

### Python SDK 示例

```python
import requests

API_URL = "http://localhost:8000"
API_KEY = "rag-secret-key"
headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

# 创建知识库
resp = requests.post(
    f"{API_URL}/api/v1/knowledge",
    headers=headers,
    json={"name": "My Docs", "description": "测试"}
)
kb_id = resp.json()["id"]

# 上传文档
with open("docs/guide.pdf", "rb") as f:
    files = {"file": f}
    resp = requests.post(
        f"{API_URL}/api/v1/knowledge/{kb_id}/upload",
        headers={"X-API-Key": API_KEY},
        files=files
    )

# RAG 问答
resp = requests.post(
    f"{API_URL}/v1/chat/completions",
    headers=headers,
    json={
        "messages": [{"role": "user", "content": "如何配置？"}],
        "knowledge_base_id": kb_id
    }
)
print(resp.json()["choices"][0]["message"]["content"])
```

---

## MCP 协议集成

### 什么是 MCP

MCP（Model Context Protocol）是一种标准协议，允许 AI 助手（如 Cursor、Claude Code）调用外部工具和服务。

### Cursor 配置

1. 打开 Cursor 设置（`Cmd + ,`）
2. 进入 **MCP (Model Context Protocol)** 设置
3. 点击 **Add New Server**
4. 填写配置：

```json
{
  "mcpServers": {
    "yang-rag": {
      "command": "python",
      "args": ["-m", "src.mcp_server.server"],
      "cwd": "/Users/leo/IdeaProjects/yang/rag"
    }
  }
}
```

5. 点击保存并重启 Cursor

### Claude Code 配置

在 `~/.claude/settings.json` 或项目 `.claude/mcp.json` 中添加：

```json
{
  "mcpServers": {
    "yang-rag": {
      "command": "python",
      "args": ["-m", "src.mcp_server.server"],
      "cwd": "/Users/leo/IdeaProjects/yang/rag"
    }
  }
}
```

### MCP 工具使用

在 Cursor 或 Claude Code 的对话中使用：

```
@yang-rag search_knowledge_base "Python 最佳实践" --top_k 5

@yang-rag list_knowledge_bases

@yang-rag query_with_context "如何在项目中配置日志？"

@yang-rag create_knowledge_base "项目文档" --description "项目开发文档"
```

---

## 跨设备接入指南

### 场景说明

Yang RAG System 支持在本地运行，并被远程的 Cursor 或 Claude Code 实例接入。

### 方案一：REST API 远程调用

适合有公网 IP 或通过 VPN 连接的场景。

#### 服务器端配置

```env
# .env
API_HOST=0.0.0.0  # 监听所有接口
API_PORT=8000
API_KEY=your-secure-api-key  # 使用强密码
```

#### 启动服务

```bash
python -m src.api.main
# 或使用 nohup 后台运行
nohup python -m src.api.main > /var/log/rag.log 2>&1 &
```

#### 客户端调用

```python
import requests

API_URL = "http://your-server-ip:8000"
API_KEY = "your-secure-api-key"

headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

resp = requests.post(
    f"{API_URL}/v1/chat/completions",
    headers=headers,
    json={
        "messages": [{"role": "user", "content": "查询内容"}],
        "knowledge_base_id": "your-kb-id"
    }
)
```

### 方案二：SSH 隧道 + MCP

适合内网服务器，通过 SSH 隧道暴露 MCP 服务。

#### 服务器端

```bash
# 在服务器上启动 MCP 服务
python -m src.mcp_server.server > /tmp/mcp.log 2>&1 &
```

#### 客户端（通过 SSH 隧道访问）

```bash
# 创建 SSH 隧道
ssh -L 8001:localhost:8001 user@your-server-ip -N

# 在 SSH 会话中运行 MCP 服务
ssh user@your-server-ip "cd /path/to/yang/rag && python -m src.mcp_server.server"
```

### 方案三：Docker 部署

适合需要隔离环境或在不同机器上部署的场景。

#### Dockerfile 示例

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-m", "src.api.main"]
```

#### 构建和运行

```bash
# 构建镜像
docker build -t yang-rag:latest .

# 运行
docker run -d \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -e OPENAI_API_KEY=your-key \
  yang-rag:latest
```

### 方案四：Claude Code MCP 配置（推荐）

对于 Claude Code，可以直接配置 MCP 服务 URL：

```json
{
  "mcpServers": {
    "yang-rag-remote": {
      "command": "python",
      "args": [
        "-c",
        """
import subprocess
import sys
result = subprocess.run(
    ['curl', '-s', '-X', 'POST', 'http://YOUR_SERVER:8000/api/v1/knowledge/search', 
     '-H', 'Content-Type: application/json', 
     '-H', 'X-API-Key: YOUR_KEY',
     '-d', '{\"query\": \"' + sys.argv[1] + '\", \"top_k\": 5}'],
    capture_output=True, text=True
)
print(result.stdout)
"""
      ]
    }
  }
}
```

### 安全建议

1. **使用 HTTPS**: 生产环境使用 Nginx/Caddy 反向代理并配置 SSL
2. **强密码**: API_KEY 使用随机强密码
3. **网络隔离**: 使用防火墙限制访问
4. **日志监控**: 启用访问日志便于审计

```nginx
# Nginx 配置示例
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 配置参考

### 环境变量完整列表

| 变量名 | 默认值 | 描述 |
|--------|--------|------|
| **OpenAI 配置** |||
| `OPENAI_API_KEY` | - | OpenAI API 密钥（必填） |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | API 基础地址 |
| `OPENAI_MODEL` | `gpt-4o-mini` | 聊天模型 |
| **Embedding 配置** |||
| `EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding 模型 |
| `EMBEDDING_DIMENSION` | `1536` | 向量维度 |
| **向量存储** |||
| `VECTOR_STORE_TYPE` | `chroma` | 存储类型: chroma/faiss/milvus |
| `VECTOR_STORE_PERSIST_DIR` | `./data/vectorstore` | 存储路径 |
| `CHROMA_TENANT` | `default_tenant` | ChromaDB 租户 |
| `CHROMA_DATABASE` | `default_database` | ChromaDB 数据库 |
| **API 配置** |||
| `API_HOST` | `0.0.0.0` | 监听地址 |
| `API_PORT` | `8000` | 监听端口 |
| `API_KEY` | `rag-secret-key` | API 认证密钥 |
| **检索配置** |||
| `RETRIEVAL_TOP_K` | `5` | 检索结果数 |
| `RERANK_TOP_K` | `3` | 重排后结果数 |
| `CHUNK_SIZE` | `500` | 文本块大小 |
| `CHUNK_OVERLAP` | `50` | 块重叠大小 |

### 自定义配置示例

```env
# 生产环境配置
OPENAI_API_KEY=sk-prod-key
OPENAI_MODEL=gpt-4o
OPENAI_BASE_URL=https://api.openai.com/v1

# 使用 Azure OpenAI
OPENAI_API_KEY=your-azure-key
OPENAI_BASE_URL=https://your-resource.openai.azure.com
OPENAI_MODEL=gpt-4o

# 使用本地模型（如 Ollama）
OPENAI_API_KEY=ollama
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_MODEL=llama3
EMBEDDING_MODEL=mxbai-embed-large

# 向量存储
VECTOR_STORE_TYPE=chroma
VECTOR_STORE_PERSIST_DIR=/mnt/vectorstore

# 安全
API_KEY=生成的强密码
```

---

## 最佳实践

### 文档准备

1. **文档质量**: 使用结构清晰、排版规范的文档
2. **格式选择**: Markdown > PDF > Word > 纯文本
3. **大小控制**: 单个文件建议 < 50MB
4. **预清洗**: 移除无关内容（页眉页脚、水印等）

### 分块策略

| 场景 | chunk_size | chunk_overlap | 策略 |
|------|------------|---------------|------|
| 短文档/FAQ | 300-500 | 50-100 | recursive |
| 技术文档 | 500-800 | 50-100 | smart |
| 长篇文章 | 800-1000 | 100-150 | smart |
| 代码库 | 300-500 | 50 | code |

### 检索优化

1. **混合检索**: 对复杂查询使用 `hybrid` 策略
2. **重排序**: 启用 Cross-Encoder 重排序提升准确率
3. **元数据过滤**: 利用文档元数据精确筛选

### 性能优化

1. **批量上传**: 多个文档时批量处理
2. **异步 API**: 使用异步接口提升并发能力
3. **缓存 Embedding**: ChromaDB 支持持久化缓存

### 安全建议

1. **环境隔离**: 生产环境使用虚拟环境或 Docker
2. **密钥管理**: 使用 `.env` 文件，添加到 `.gitignore`
3. **访问控制**: 配置防火墙和 API 限流
4. **日志审计**: 启用访问日志记录

---

## 常见问题

### Q: MCP 服务启动失败

**检查项**:
1. Python 环境是否正确激活
2. 依赖是否完整安装
3. 工作目录是否正确

```bash
# 验证
python -c "from src.knowledge.manager import get_kb_manager; print('OK')"
```

### Q: 文档上传成功但搜索无结果

**可能原因**:
1. 文档内容为空或格式不支持
2. 向量存储未正确初始化
3. Embedding 服务异常

```bash
# 检查知识库状态
curl http://localhost:8000/api/v1/knowledge/{kb_id}
```

### Q: API 返回 401 错误

**检查**:
1. `X-API-Key` 请求头是否正确
2. API_KEY 环境变量是否与配置一致

---

## License

MIT License
