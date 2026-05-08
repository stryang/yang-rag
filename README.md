# Yang RAG System

一个基于 LangChain 构建的企业级 RAG（检索增强生成）系统。

## 功能特性

### 1. 知识库管理
- **多格式支持**: PDF、DOCX、TXT、Markdown、HTML、PPTX、XLSX
- **智能分块**: 多种分块策略，支持代码、Markdown、通用文本
- **向量存储**: 支持 ChromaDB、FAISS 和 Milvus（可选依赖）
- **CRUD 操作**: 创建、更新、删除知识库

### 2. 检索增强
- **语义检索**: 基于向量相似度搜索
- **混合检索**: 结合向量和关键词检索
- **重排序**: 使用 Cross-Encoder 提升结果相关性

### 3. 接口协议
- **OpenAI 兼容 API**: `/v1/chat/completions`
- **MCP Server**: Model Context Protocol 支持 Cursor 等 Code Agent

## 快速开始

### 1. 安装依赖

```bash
cd /Users/leo/IdeaProjects/yang/rag
pip install -r requirements.txt
```

### 2. 配置环境

```bash
cp .env.example .env
# 编辑 .env 填写你的 OpenAI API Key
```

### 3. 启动服务

**REST API:**
```bash
python -m src.api.main
```

**MCP Server (用于 Cursor):**
```bash
python -m src.mcp_server.server
```

## API 使用示例

### 创建知识库
```bash
curl -X POST http://localhost:8000/api/v1/knowledge \
  -H "Content-Type: application/json" \
  -H "X-API-Key: rag-secret-key" \
  -d '{"name": "My Docs", "description": "My documentation"}'
```

### 上传文档
```bash
curl -X POST http://localhost:8000/api/v1/knowledge/{kb_id}/upload \
  -F "file=@./docs/guide.pdf" \
  -H "X-API-Key: rag-secret-key"
```

### 问答
```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-API-Key: rag-secret-key" \
  -d '{
    "messages": [{"role": "user", "content": "如何配置系统？"}],
    "knowledge_base_id": "{kb_id}"
  }'
```

## Cursor MCP 配置

1. 打开 Cursor 设置
2. 进入 MCP (Model Context Protocol) 设置
3. 添加新服务器：

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

4. 重启 Cursor

### MCP 工具使用

在 Cursor 对话中使用:

```
search_knowledge_base "Python 最佳实践" --top_k 5
list_knowledge_bases
query_with_context "如何在项目中配置日志？"
```

## 项目结构

```
rag/
├── src/
│   ├── api/              # FastAPI REST API
│   │   └── main.py
│   ├── mcp_server/       # MCP Server
│   │   └── server.py
│   ├── knowledge/        # 知识库管理
│   │   ├── loader.py    # 文档加载
│   │   ├── splitter.py   # 文本分块
│   │   ├── embedder.py   # 向量化
│   │   ├── store.py      # 向量存储
│   │   └── manager.py    # 知识库管理
│   ├── retrieval/        # 检索模块
│   │   ├── retriever.py  # 检索器
│   │   └── reranker.py   # 重排序
│   ├── generation/       # 生成模块
│   │   └── synthesizer.py # 答案合成
│   └── core/             # 核心配置
│       ├── config.py
│       └── prompts.py
├── tests/               # 测试
├── examples/            # 示例代码
├── docs/                # 文档
└── README.md
```

## 环境变量

| 变量名 | 默认值 | 描述 |
|--------|--------|------|
| `OPENAI_API_KEY` | - | OpenAI API Key |
| `OPENAI_BASE_URL` | https://api.openai.com/v1 | API Base URL |
| `OPENAI_MODEL` | gpt-4o-mini | 模型名称 |
| `EMBEDDING_MODEL` | text-embedding-3-small | Embedding 模型 |
| `VECTOR_STORE_TYPE` | chroma | 向量存储类型 |
| `API_KEY` | rag-secret-key | API 认证密钥 |
| `RETRIEVAL_TOP_K` | 5 | 检索结果数 |
| `RERANK_TOP_K` | 3 | 重排后结果数 |
| `CHUNK_SIZE` | 500 | 文本块大小 |
| `CHUNK_OVERLAP` | 50 | 块重叠大小 |

## 开发

### 运行测试

```bash
pytest tests/ -v
```

### 代码示例

```python
from src.knowledge.manager import get_kb_manager
from src.generation.synthesizer import create_synthesizer

# 获取知识库管理器
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

## License

MIT License

---

## 完整文档

如需更详细的系统介绍、代码模块说明、使用指南和跨设备接入配置，请参阅 [系统完整文档](docs/SYSTEM_DOCUMENTATION.md)。
