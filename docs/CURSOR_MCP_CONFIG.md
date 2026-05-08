# Cursor MCP Configuration for Yang RAG System

## Option 1: Using Simple MCP Server (Recommended - Works with Python 3.8+)

Add to your Cursor settings (Settings > MCP > Add new server):

```json
{
  "mcpServers": {
    "yang-rag": {
      "command": "python3",
      "args": ["-m", "src.mcp_server.simple_server"],
      "cwd": "/path/to/your/rag-project"
    }
  }
}
```

## Option 2: Using uv (Recommended for faster startup)

```json
{
  "mcpServers": {
    "yang-rag": {
      "command": "uv",
      "args": ["run", "python", "-m", "src.mcp_server.simple_server"],
      "cwd": "/path/to/your/rag-project"
    }
  }
}
```

## Option 3: Using Docker (For isolated environment)

```bash
# Build Docker image
docker build -t yang-rag-mcp .

# Add to Cursor MCP settings
{
  "mcpServers": {
    "yang-rag": {
      "command": "docker",
      "args": ["run", "--rm", "-i", "yang-rag-mcp"]
    }
  }
}
```

## Environment Variables

Create a `.env` file in the project root:

```bash
# Copy from example and fill in your values
cp .env.example .env
```

Required environment variables:

- `OPENAI_API_KEY` - Your OpenAI API key (required)
- `API_KEY` - API key for authentication (optional for MCP)

## Testing the Connection

After configuring, test the connection:

1. Open Cursor
2. Type in the chat: "list_knowledge_bases"
3. You should see the available knowledge bases

## Available MCP Tools

Once connected, you can use these tools in Cursor:

| Tool | Description | Arguments |
|------|-------------|-----------|
| `search_knowledge_base` | Search for relevant documents | `query`, `knowledge_base_id?`, `top_k?` |
| `list_knowledge_bases` | List all knowledge bases | - |
| `get_knowledge_base_info` | Get KB details | `knowledge_base_id` |
| `query_with_context` | Ask questions with RAG context | `question`, `knowledge_base_id?` |
| `create_knowledge_base` | Create a new knowledge base | `name`, `description?` |

## MCP Resources

Access knowledge base information as resources:

- `yang-rag://knowledge-base/{kb_id}` - Get KB statistics
