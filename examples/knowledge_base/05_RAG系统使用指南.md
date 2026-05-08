# RAG 系统使用指南

## 1. 概述

RAG (Retrieval-Augmented Generation) 系统结合了检索和生成两种能力，可以基于知识库中的文档回答用户问题。

## 2. 快速开始

### 2.1 启动服务

```bash
# 激活虚拟环境
source venv/bin/activate

# 启动 API 服务
python -m src.api.main

# 或启动 MCP Server (用于 Cursor)
python -m src.mcp_server.server
```

### 2.2 基本使用

```python
from src.knowledge.manager import get_kb_manager
from src.generation.synthesizer import create_synthesizer

# 获取管理器
manager = get_kb_manager()

# 创建知识库
kb = manager.create_knowledge_base(
    name="我的知识库",
    description="项目文档"
)

# 添加文档
kb.add_document("./docs/guide.pdf")

# 问答
synthesizer = create_synthesizer(kb)
result = synthesizer.invoke("如何使用本系统？")

print(result["answer"])
```

## 3. API 使用

### 3.1 创建知识库

```bash
curl -X POST http://localhost:8000/api/v1/knowledge \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "name": "项目文档",
    "description": "包含所有项目相关文档"
  }'
```

### 3.2 上传文档

```bash
curl -X POST http://localhost:8000/api/v1/knowledge/{kb_id}/upload \
  -F "file=@./docs/guide.pdf" \
  -H "X-API-Key: your-api-key"
```

### 3.3 问答

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "messages": [
      {"role": "user", "content": "系统架构是什么样的？"}
    ],
    "knowledge_base_id": "your-kb-id"
  }'
```

## 4. Cursor MCP 集成

### 4.1 配置 MCP Server

在 Cursor 设置中添加：

```json
{
  "mcpServers": {
    "yang-rag": {
      "command": "python3",
      "args": ["-m", "src.mcp_server.server"],
      "cwd": "/path/to/rag-project"
    }
  }
}
```

### 4.2 使用 MCP 工具

在 Cursor 对话中使用以下工具：

| 工具 | 说明 | 示例 |
|------|------|------|
| `search_knowledge_base` | 搜索知识库 | `search_knowledge_base "Python 最佳实践"` |
| `list_knowledge_bases` | 列出知识库 | `list_knowledge_bases` |
| `query_with_context` | RAG 问答 | `query_with_context "如何配置系统？"` |
| `create_knowledge_base` | 创建知识库 | `create_knowledge_base name="新知识库"` |

### 4.3 示例对话

```
用户: 搜索我的代码规范文档
Cursor: 使用 search_knowledge_base 工具搜索"代码规范"

用户: 如何在项目中添加新功能？
Cursor: 使用 query_with_context 工具回答这个问题
```

## 5. 支持的文件格式

| 格式 | 说明 | 扩展名 |
|------|------|--------|
| PDF | 便携式文档 | .pdf |
| Word | 微软 Word 文档 | .docx, .doc |
| 纯文本 | 文本文件 | .txt |
| Markdown | Markdown 格式 | .md |
| HTML | 网页文件 | .html, .htm |
| PowerPoint | 演示文稿 | .pptx, .ppt |
| Excel | 电子表格 | .xlsx, .xls |

## 6. 配置参数

### 6.1 检索参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `RETRIEVAL_TOP_K` | 5 | 检索返回结果数 |
| `RERANK_TOP_K` | 3 | 重排后结果数 |
| `CHUNK_SIZE` | 500 | 文本块大小 |
| `CHUNK_OVERLAP` | 50 | 块重叠大小 |

### 6.2 模型参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `EMBEDDING_MODEL` | text-embedding-3-small | Embedding 模型 |
| `OPENAI_MODEL` | gpt-4o-mini | 问答使用模型 |

## 7. 架构说明

```
┌─────────────────────────────────────────────────────────────┐
│                        RAG System                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Document   │───▶│   Chunking   │───▶│   Embedding  │  │
│  │    Loader    │    │              │    │              │  │
│  └──────────────┘    └──────────────┘    └──────┬───────┘  │
│                                                     │          │
│                                                     ▼          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │    Answer    │◀───│    LLM       │◀───│   Context    │  │
│  │   Output     │    │   Generate   │    │   Builder    │  │
│  └──────────────┘    └──────────────┘    └──────▲───────┘  │
│                                                     │          │
│                                                     │          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   User        │───▶│   Retrieve   │───▶│  Vector DB   │  │
│  │   Query       │    │              │    │  (ChromaDB)  │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## 8. 故障排除

### 8.1 常见问题

**Q: 上传文档失败？**
A: 检查文件格式是否支持，确保文件可读

**Q: 检索结果不准确？**
A: 调整 CHUNK_SIZE 和 RETRIEVAL_TOP_K 参数

**Q: 回答质量不佳？**
A: 确保知识库文档质量，尝试使用更大的 CHUNK_SIZE

### 8.2 日志查看

```bash
# API 日志
python -m src.api.main --log-level debug

# MCP Server 日志
python -m src.mcp_server.server --verbose
```

## 9. 联系方式

如有问题，请联系：
- 邮箱: support@example.com
- 文档: https://docs.example.com
