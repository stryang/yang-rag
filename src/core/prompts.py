"""Prompt templates for RAG system."""

from typing import Dict, List

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage


# System prompt for RAG QA
RAG_SYSTEM_PROMPT = """你是一个专业的知识库问答助手。你的任务是基于提供的上下文信息，准确、专业地回答用户的问题。

## 回答规则
1. **仅基于上下文回答**: 必须仅使用提供的上下文信息来回答问题，不要编造信息。
2. **引用来源**: 在回答时，可以提及信息来源（如有）。
3. **保持一致性**: 如果上下文中没有相关信息，明确告知用户"抱歉，我在知识库中没有找到相关内容"。
4. **清晰简洁**: 回答要条理清晰，语言简洁易懂。
5. **中文优先**: 如果用户使用中文提问，请用中文回答。

## 上下文格式
提供的上下文包含从知识库中检索到的相关文档片段。每个片段包含：
- 内容：文档的实际文本
- 来源：文档的文件名或标题
- 相关度分数：与问题的匹配程度

## 输出格式
请按以下格式回答：
1. 直接回答问题
2. 如有引用，列出参考来源
"""

# Human prompt template for RAG QA
RAG_HUMAN_TEMPLATE = """## 用户问题
{question}

## 检索到的上下文
{context}

## 请基于以上上下文回答用户的问题：
"""

# Code Agent context prompt
CODE_AGENT_SYSTEM_PROMPT = """你是一个专业的代码助手，擅长帮助用户解决编程问题。

## 你的知识库
系统配置、代码规范、项目文档等信息都存储在知识库中。当你需要查阅这些信息时，
请使用 `search_knowledge_base` 工具进行检索。

## 回答规则
1. 如果涉及特定项目或框架，优先检索知识库获取相关信息
2. 提供准确、实用的代码示例
3. 解释技术细节和最佳实践
4. 如果不确定，坦诚说明

## 工具使用
你可以使用以下工具：
- `search_knowledge_base`: 搜索知识库
- `get_knowledge_base_list`: 获取知识库列表
- `query`: 通用问答
"""

# Knowledge base search prompt
KB_SEARCH_SYSTEM_PROMPT = """你是一个知识检索助手。你的任务是根据用户查询，从知识库中检索最相关的信息。

## 查询分析
- 分析用户的查询意图
- 提取关键概念和术语
- 考虑同义词和表达变体

## 检索策略
- 使用清晰的查询语言
- 结合精确匹配和语义相似度
- 返回最相关的几个结果
"""

KB_SEARCH_HUMAN_TEMPLATE = """## 用户查询
{query}

## 搜索类型
{search_type}

请检索与上述查询相关的知识库内容。
"""

# Chunking explanation prompt
CHUNK_EXPLANATION_PROMPT = """你是一个文档处理助手。请解释以下文档块的内容概要：

{chunk_content}

请简要说明这段内容的主题和关键信息（不超过50字）。
"""


def get_rag_prompt(question: str, context: str) -> List[Dict]:
    """Build RAG prompt for chat completion.

    Args:
        question: User's question
        context: Retrieved context

    Returns:
        List of message dictionaries for chat completion
    """
    return [
        {"role": "system", "content": RAG_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": RAG_HUMAN_TEMPLATE.format(
                question=question, context=context
            ),
        },
    ]


def get_code_agent_prompt() -> str:
    """Get system prompt for code agent."""
    return CODE_AGENT_SYSTEM_PROMPT


def get_langchain_rag_prompt() -> ChatPromptTemplate:
    """Get LangChain prompt template for RAG."""
    return ChatPromptTemplate.from_messages(
        [
            ("system", RAG_SYSTEM_PROMPT),
            ("human", RAG_HUMAN_TEMPLATE),
        ]
    )


def format_context(results: List[Dict], max_length: int = 2000) -> str:
    """Format retrieved results as context string.

    Args:
        results: List of retrieval results with content, source, score
        max_length: Maximum context length

    Returns:
        Formatted context string
    """
    if not results:
        return "没有找到相关的知识库内容。"

    formatted_chunks = []
    total_length = 0

    for i, result in enumerate(results, 1):
        chunk_text = result.get("content", "")
        source = result.get("metadata", {}).get("source", "未知来源")
        score = result.get("score", 0.0)

        chunk_formatted = """### 来源 {}: {} (相关度: {:.2f})
{}
""".format(i, source, score, chunk_text)
        chunk_length = len(chunk_formatted)

        if total_length + chunk_length > max_length:
            remaining = max_length - total_length
            if remaining > 100:
                chunk_formatted = chunk_formatted[:remaining] + "..."
            else:
                break

        formatted_chunks.append(chunk_formatted)
        total_length += len(chunk_formatted)

    return "\n".join(formatted_chunks)
