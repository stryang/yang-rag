"""Simple MCP Server for Yang RAG System.

This is a lightweight MCP server implementation using JSON-RPC over stdio.
Compatible with Python 3.8.
"""

import json
import sys
from typing import Any, Dict, List, Optional


def handle_request(request: Dict) -> Dict:
    """Handle MCP JSON-RPC request."""
    method = request.get("method", "")
    request_id = request.get("id")
    params = request.get("params", {})

    result = None
    error = None

    try:
        if method == "initialize":
            result = {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": True,
                    "resources": True,
                },
                "serverInfo": {
                    "name": "yang-rag-mcp",
                    "version": "1.0.0",
                },
            }
        elif method == "tools/list":
            result = {"tools": get_tools()}
        elif method == "tools/call":
            tool_name = params.get("name", "")
            tool_args = params.get("arguments", {})
            result = call_tool(tool_name, tool_args)
        elif method == "resources/list":
            result = {"resources": get_resources()}
        elif method == "resources/read":
            uri = params.get("uri", "")
            result = read_resource(uri)
        elif method == "notifications/initialized":
            result = None
        else:
            error = {"code": -32601, "message": "Method not found: {}".format(method)}
    except Exception as e:
        error = {"code": -32603, "message": "Internal error: {}".format(str(e))}

    response = {"jsonrpc": "2.0"}
    if request_id is not None:
        response["id"] = request_id
    if error:
        response["error"] = error
    else:
        response["result"] = result

    return response


def get_tools() -> List[Dict]:
    """Get list of available tools."""
    return [
        {
            "name": "search_knowledge_base",
            "description": "Search the knowledge base for relevant documents.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query string",
                    },
                    "knowledge_base_id": {
                        "type": "string",
                        "description": "Knowledge base ID to search in",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of results to return",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        },
        {
            "name": "list_knowledge_bases",
            "description": "List all available knowledge bases.",
            "inputSchema": {
                "type": "object",
                "properties": {},
            },
        },
        {
            "name": "query_with_context",
            "description": "Query the RAG system with a natural language question.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "Question to ask",
                    },
                    "knowledge_base_id": {
                        "type": "string",
                        "description": "Knowledge base ID to query",
                    },
                },
                "required": ["question"],
            },
        },
        {
            "name": "create_knowledge_base",
            "description": "Create a new knowledge base.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name of the knowledge base",
                    },
                    "description": {
                        "type": "string",
                        "description": "Description of the knowledge base",
                    },
                },
                "required": ["name"],
            },
        },
    ]


def call_tool(name: str, arguments: Dict) -> Dict:
    """Call a tool and return result."""
    try:
        if name == "search_knowledge_base":
            return search_knowledge_base(arguments)
        elif name == "list_knowledge_bases":
            return list_knowledge_bases(arguments)
        elif name == "query_with_context":
            return query_with_context(arguments)
        elif name == "create_knowledge_base":
            return create_knowledge_base(arguments)
        else:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "Unknown tool: {}".format(name),
                    }
                ],
                "isError": True,
            }
    except Exception as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": "Error: {}".format(str(e)),
                }
            ],
            "isError": True,
        }


def search_knowledge_base(args: Dict) -> Dict:
    """Search knowledge base."""
    from src.knowledge.manager import get_kb_manager

    query = args.get("query", "")
    kb_id = args.get("knowledge_base_id")
    top_k = args.get("top_k", 5)

    manager = get_kb_manager()

    if kb_id:
        kb = manager.get_knowledge_base(kb_id)
        results = kb.search(query=query, top_k=top_k)
    else:
        all_results = []
        for kb_meta in manager.list_knowledge_bases():
            kb = manager.get_knowledge_base(kb_meta.id)
            kb_results = kb.search(query=query, top_k=top_k)
            for r in kb_results:
                r["knowledge_base"] = kb_meta.name
            all_results.extend(kb_results)
        all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
        results = all_results[:top_k]

    if not results:
        text = "No results found"
    else:
        lines = []
        for i, r in enumerate(results, 1):
            source = r.get("metadata", {}).get("source", "Unknown")
            score = r.get("score", 0)
            content = r.get("content", "")[:200]
            kb_name = r.get("knowledge_base", "")
            lines.append("### Result {} [{}]".format(i, kb_name))
            lines.append("**Source:** {}".format(source))
            lines.append("**Relevance:** {:.2f}".format(score))
            lines.append("**Content:**\n{}...\n".format(content))
        text = "\n".join(lines)

    return {
        "content": [{"type": "text", "text": text}],
    }


def list_knowledge_bases(args: Dict) -> Dict:
    """List knowledge bases."""
    from src.knowledge.manager import get_kb_manager

    manager = get_kb_manager()
    kbs = manager.list_knowledge_bases()

    if not kbs:
        text = "No knowledge bases found. Create one first!"
    else:
        lines = ["## Available Knowledge Bases\n"]
        for kb in kbs:
            lines.append("- **{}** (ID: `{}`)".format(kb.name, kb.id))
            lines.append("  - Description: {}".format(kb.description or "N/A"))
            lines.append("  - Documents: {}, Chunks: {}".format(kb.document_count, kb.chunk_count))
            lines.append("  - Created: {}\n".format(kb.created_at))
        text = "\n".join(lines)

    return {
        "content": [{"type": "text", "text": text}],
    }


def query_with_context(args: Dict) -> Dict:
    """Query with context."""
    from src.knowledge.manager import get_kb_manager
    from src.generation.synthesizer import create_synthesizer

    question = args.get("question", "")
    kb_id = args.get("knowledge_base_id")

    if not question:
        return {
            "content": [{"type": "text", "text": "Question is required"}],
            "isError": True,
        }

    manager = get_kb_manager()

    if not kb_id:
        kbs = manager.list_knowledge_bases()
        if not kbs:
            return {
                "content": [{"type": "text", "text": "No knowledge base available. Create one first."}],
                "isError": True,
            }
        kb_id = kbs[0].id

    try:
        kb = manager.get_knowledge_base(kb_id)
    except KeyError:
        return {
            "content": [{"type": "text", "text": "Knowledge base {} not found".format(kb_id)}],
            "isError": True,
        }

    synthesizer = create_synthesizer(kb, synthesizer_type="code-agent")
    result = synthesizer.invoke(question, return_sources=True)

    lines = ["## Answer\n", result["answer"], "\n## Sources\n"]
    for i, source in enumerate(result.get("sources", []), 1):
        content = source.get("content", "")[:200]
        lines.append("{}. **{}**: {}...".format(i, source.get("source", "Unknown"), content))

    return {
        "content": [{"type": "text", "text": "\n".join(lines)}],
    }


def create_knowledge_base(args: Dict) -> Dict:
    """Create knowledge base."""
    from src.knowledge.manager import get_kb_manager

    name = args.get("name", "")
    description = args.get("description", "")

    if not name:
        return {
            "content": [{"type": "text", "text": "Name is required"}],
            "isError": True,
        }

    manager = get_kb_manager()
    kb = manager.create_knowledge_base(name=name, description=description)

    return {
        "content": [{
            "type": "text",
            "text": "Knowledge base '{}' created successfully!\nID: `{}`\n\nUse this ID to add documents or search.".format(
                name, kb.id
            ),
        }],
    }


def get_resources() -> List[Dict]:
    """Get list of resources."""
    from src.knowledge.manager import get_kb_manager

    manager = get_kb_manager()
    kbs = manager.list_knowledge_bases()

    resources = []
    for kb in kbs:
        resources.append({
            "uri": "yang-rag://knowledge-base/{}".format(kb.id),
            "name": kb.name,
            "description": kb.description or "No description",
            "mimeType": "application/json",
        })

    return resources


def read_resource(uri: str) -> Dict:
    """Read a resource."""
    from src.knowledge.manager import get_kb_manager
    import json

    if uri.startswith("yang-rag://knowledge-base/"):
        kb_id = uri.split("/")[-1]
        manager = get_kb_manager()
        try:
            kb = manager.get_knowledge_base(kb_id)
            stats = kb.get_stats()
            contents = json.dumps(stats, indent=2)
        except KeyError:
            contents = "Knowledge base {} not found".format(kb_id)
    else:
        contents = "Unknown resource: {}".format(uri)

    return {
        "contents": [{"uri": uri, "mimeType": "application/json", "text": contents}],
    }


def main():
    """Main MCP server loop."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            request = json.loads(line)
            response = handle_request(request)

            if response.get("id") is not None:
                print(json.dumps(response), flush=True)
        except json.JSONDecodeError:
            error_response = {
                "jsonrpc": "2.0",
                "error": {"code": -32700, "message": "Parse error"},
            }
            print(json.dumps(error_response), flush=True)


if __name__ == "__main__":
    main()
