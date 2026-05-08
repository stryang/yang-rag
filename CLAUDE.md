# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Install dependencies
```bash
pip install -r requirements.txt
```

### Start services
```bash
# REST API (port 8000)
python -m src.api.main

# MCP Server (stdio, for Cursor integration)
python -m src.mcp_server.server

# Admin backend + frontend
bash start-admin.sh
```

### Run tests
```bash
pytest tests/ -v
pytest tests/test_rag.py::TestClassName::test_method_name  # single test
pytest --cov=src --cov-report=term-missing                 # with coverage
```

### Environment setup
```bash
cp .env.example .env
# Fill in LLM_API_KEY and EMBEDDING_API_KEY at minimum
```

## Architecture

This is a multi-service RAG (Retrieval-Augmented Generation) system with three entry points.

### 1. Main RAG service (`src/`)

Built with FastAPI + LangChain. Data flows: document upload → load → split → embed → store; query → retrieve → (rerank) → synthesize.

| Module | Responsibility |
|---|---|
| `src/core/config.py` | `Settings` (pydantic-settings), reads `.env`. Single `settings` singleton. |
| `src/knowledge/manager.py` | `KnowledgeBaseManager` singleton; persists KB metadata as JSON in `./data/kb_metadata/`. `KnowledgeBase` lazily initializes its embedder/vector store. |
| `src/knowledge/loader.py` | Document loading for PDF, DOCX, TXT, MD, HTML, PPTX, XLSX |
| `src/knowledge/splitter.py` | Text chunking strategies (smart/code/markdown/generic) |
| `src/knowledge/embedder.py` | Embedding providers: openai, siliconflow, huggingface/local, ollama |
| `src/knowledge/store.py` | Vector store abstraction: ChromaDB (default), FAISS, Milvus |
| `src/retrieval/retriever.py` | `KnowledgeBaseRetriever` (vector) and hybrid retriever |
| `src/retrieval/reranker.py` | Rerankers: simple (score-based), cross-encoder, LLM-based |
| `src/generation/synthesizer.py` | LLM answer synthesis; `create_llm()` supports openai/ollama/siliconflow/qwen |
| `src/api/main.py` | FastAPI app; all mutating routes require `X-API-Key` header |
| `src/mcp_server/server.py` | Lightweight JSON-RPC over stdio (no `mcp` library; Python 3.8 compatible) |

### 2. Admin backend (`admin-backend/`)

Separate FastAPI app with SQLite (`admin-backend/data/admin.db`). Handles user auth and admin operations.

### 3. Admin frontend (`admin-frontend/`)

Vite + React + TypeScript + Tailwind CSS. Build output in `admin-frontend/dist/`.

## Key Design Decisions

- **KnowledgeBase lazy init**: Embedder and vector store are deferred until first use (`_ensure_initialized()`), so listing KBs doesn't trigger embedding API calls.
- **KB metadata persistence**: Each KB is a JSON file at `./data/kb_metadata/{id}.json`. Vector data lives in `./data/vectorstore/`.
- **Two API prefixes**: Knowledge management is under `/api/v1/knowledge`; OpenAI-compatible chat is at `/v1/chat/completions`.
- **Python 3.8 compatibility**: `requirements.txt` pins older package versions; the MCP server avoids the `mcp` library for this reason.
- **Provider abstraction**: LLM and embedding providers are selected via `LLM_PROVIDER`/`EMBEDDING_PROVIDER` env vars. To add a new provider, extend `create_llm()` in `synthesizer.py` and `get_embedder()` in `embedder.py`.

## API Authentication

All mutating endpoints require `X-API-Key: <API_KEY>` header. Default key is `rag-secret-key` (override with `API_KEY` in `.env`).

## Data Directories

| Path | Contents |
|---|---|
| `./data/vectorstore/` | ChromaDB or FAISS persisted vectors |
| `./data/kb_metadata/` | JSON metadata for each knowledge base |
| `./data/uploads/` | Temporary upload staging (auto-deleted after indexing) |
