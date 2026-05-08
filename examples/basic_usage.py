"""Example usage script for Yang RAG System."""

import asyncio
from pathlib import Path

from src.knowledge.manager import get_kb_manager
from src.generation.synthesizer import create_synthesizer


async def main():
    """Demonstrate RAG system usage."""

    # Get knowledge base manager
    manager = get_kb_manager()

    # Create a knowledge base
    print("Creating knowledge base...")
    kb = manager.create_knowledge_base(
        name="My Project Docs",
        description="Documentation for my project",
    )
    print(f"Created: {kb.id} - {kb.name}")

    # Add documents
    docs_path = Path("./docs")
    if docs_path.exists():
        print("\nAdding documents...")
        for file_path in docs_path.glob("**/*"):
            if file_path.is_file():
                try:
                    result = kb.add_document(file_path)
                    print(f"  Added: {file_path.name} ({result['chunk_count']} chunks)")
                except Exception as e:
                    print(f"  Failed: {file_path.name} - {e}")

    # Search knowledge base
    print("\n--- Search Results ---")
    results = kb.search("如何配置系统", top_k=3)
    for i, result in enumerate(results, 1):
        print(f"\n{i}. Score: {result['score']:.2f}")
        print(f"   Source: {result['metadata'].get('source', 'Unknown')}")
        print(f"   Content: {result['content'][:150]}...")

    # Query with RAG
    print("\n--- RAG Query ---")
    synthesizer = create_synthesizer(kb, synthesizer_type="default")
    result = synthesizer.invoke("如何配置系统？")
    print(f"\nAnswer: {result['answer']}")
    print(f"\nSources: {len(result['sources'])} documents")

    # List all knowledge bases
    print("\n--- All Knowledge Bases ---")
    for kb_meta in manager.list_knowledge_bases():
        print(f"- {kb_meta.name} ({kb_meta.id}): {kb_meta.document_count} docs")


if __name__ == "__main__":
    asyncio.run(main())
