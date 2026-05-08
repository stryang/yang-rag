#!/usr/bin/env python
"""CLI tool for managing the RAG knowledge base."""

import sys
import os
import argparse
from pathlib import Path

# Determine project root
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv()


def create_knowledge_base(name: str, description: str = "") -> str:
    """Create a new knowledge base and return its ID."""
    from src.knowledge.manager import KnowledgeBaseManager

    manager = KnowledgeBaseManager()
    kb = manager.create_knowledge_base(name=name, description=description)
    print("Created knowledge base: {} (ID: {})".format(name, kb.id))
    return kb.id


def add_documents(kb_id: str, paths: list) -> dict:
    """Add documents to a knowledge base."""
    from src.knowledge.manager import KnowledgeBaseManager

    manager = KnowledgeBaseManager()
    kb = manager.get_knowledge_base(kb_id)

    results = []
    for path in paths:
        path = Path(path)
        if path.exists():
            if path.is_file():
                result = kb.add_document(path)
                print("Added: {} ({} chunks)".format(path.name, result["chunk_count"]))
                results.append(result)
            elif path.is_dir():
                for file_path in path.rglob("*"):
                    if file_path.is_file():
                        try:
                            result = kb.add_document(file_path)
                            print("Added: {} ({} chunks)".format(file_path.name, result["chunk_count"]))
                            results.append(result)
                        except Exception as e:
                            print("Failed: {} - {}".format(file_path.name, e))
    return results


def list_knowledge_bases() -> list:
    """List all knowledge bases."""
    from src.knowledge.manager import KnowledgeBaseManager

    manager = KnowledgeBaseManager()
    kbs = manager.list_knowledge_bases()

    if not kbs:
        print("No knowledge bases found.")
        return []

    print("\n" + "=" * 60)
    print("{:<20} {:<16} {:<6} {:<8}".format("Name", "ID", "Docs", "Chunks"))
    print("=" * 60)

    for kb in kbs:
        print("{:<20} {:<16} {:<6} {:<8}".format(
            kb.name, kb.id, kb.document_count, kb.chunk_count
        ))

    print("=" * 60)
    return kbs


def search_knowledge_base(kb_id: str, query: str, top_k: int = 5) -> list:
    """Search a knowledge base."""
    from src.knowledge.manager import KnowledgeBaseManager

    manager = KnowledgeBaseManager()
    kb = manager.get_knowledge_base(kb_id)

    results = kb.search(query=query, top_k=top_k)

    print("\nSearch results for: '{}'".format(query))
    print("=" * 60)

    for i, result in enumerate(results, 1):
        source = result.get("metadata", {}).get("source", "Unknown")
        score = result.get("score", 0)
        content = result.get("content", "")[:200]

        print("\n{}. Score: {:.4f}".format(i, score))
        print("   Source: {}".format(source))
        print("   Content: {}...".format(content))

    print("=" * 60)
    return results


def load_examples(kb_id: str = None) -> str:
    """Load example documents into a knowledge base."""
    from src.knowledge.manager import KnowledgeBaseManager

    manager = KnowledgeBaseManager()

    # Create or get knowledge base
    if kb_id:
        kb = manager.get_knowledge_base(kb_id)
    else:
        kb = manager.create_knowledge_base(
            name="示例知识库",
            description="包含系统架构、代码规范等示例文档"
        )
        kb_id = kb.id

    # Find example files
    examples_dir = PROJECT_ROOT / "examples" / "knowledge_base"
    if not examples_dir.exists():
        print("Example directory not found: {}".format(examples_dir))
        return kb_id

    # Add all markdown files
    md_files = list(examples_dir.glob("*.md"))
    if md_files:
        print("\nLoading {} example documents...".format(len(md_files)))
        for md_file in md_files:
            try:
                result = kb.add_document(md_file)
                print("  + {} ({} chunks)".format(md_file.name, result["chunk_count"]))
            except Exception as e:
                print("  - {}: {}".format(md_file.name, e))

    print("\nKnowledge base '{}' ready! ID: {}".format(kb.name, kb.id))
    return kb_id


def query_with_rag(kb_id: str, question: str) -> dict:
    """Query with RAG."""
    from src.knowledge.manager import KnowledgeBaseManager
    from src.generation.synthesizer import create_synthesizer

    manager = KnowledgeBaseManager()
    kb = manager.get_knowledge_base(kb_id)

    synthesizer = create_synthesizer(kb, synthesizer_type="default")
    result = synthesizer.invoke(question)

    print("\nQ: {}".format(question))
    print("\nA:")
    print(result["answer"])

    if result.get("sources"):
        print("\n--- Sources ---")
        for i, source in enumerate(result["sources"], 1):
            print("{}. {}".format(i, source.get("source", "Unknown")))

    return result


def main():
    parser = argparse.ArgumentParser(description="RAG Knowledge Base CLI")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Create KB
    create_parser = subparsers.add_parser("create", help="Create a knowledge base")
    create_parser.add_argument("--name", "-n", required=True, help="Knowledge base name")
    create_parser.add_argument("--description", "-d", default="", help="Description")

    # Add documents
    add_parser = subparsers.add_parser("add", help="Add documents to knowledge base")
    add_parser.add_argument("--kb-id", "-k", required=True, help="Knowledge base ID")
    add_parser.add_argument("paths", nargs="+", help="File or directory paths")

    # List KBs
    subparsers.add_parser("list", help="List all knowledge bases")

    # Search
    search_parser = subparsers.add_parser("search", help="Search knowledge base")
    search_parser.add_argument("--kb-id", "-k", required=True, help="Knowledge base ID")
    search_parser.add_argument("--query", "-q", required=True, help="Search query")
    search_parser.add_argument("--top-k", "-t", type=int, default=5, help="Number of results")

    # Query with RAG
    query_parser = subparsers.add_parser("query", help="Query with RAG")
    query_parser.add_argument("--kb-id", "-k", required=True, help="Knowledge base ID")
    query_parser.add_argument("--question", "-q", required=True, help="Question")

    # Load examples
    examples_parser = subparsers.add_parser("load-examples", help="Load example documents")
    examples_parser.add_argument("--kb-id", "-k", help="Knowledge base ID (optional)")

    args = parser.parse_args()

    if args.command == "create":
        create_knowledge_base(args.name, args.description)
    elif args.command == "add":
        add_documents(args.kb_id, args.paths)
    elif args.command == "list":
        list_knowledge_bases()
    elif args.command == "search":
        search_knowledge_base(args.kb_id, args.query, args.top_k)
    elif args.command == "query":
        query_with_rag(args.kb_id, args.question)
    elif args.command == "load-examples":
        load_examples(args.kb_id)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
