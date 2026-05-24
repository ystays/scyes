from typing import AsyncIterator

from langchain_core.messages import (
    AIMessageChunk,
    SystemMessage,
    HumanMessage,
    BaseMessage,
)
from langchain_ollama import ChatOllama
from llm.model import GEMMA_4_26B

from observability.langfuse import langfuse  # noqa F401
from langfuse.langchain import CallbackHandler

# Initialize Langfuse CallbackHandler for Langchain (tracing)
langfuse_handler = CallbackHandler()

llm = ChatOllama(
    model=GEMMA_4_26B,
    temperature=0,
)


def astream(
    input: str, msg_history: list[BaseMessage]
) -> AsyncIterator[AIMessageChunk]:
    messages = [
        SystemMessage(
            content="You're a chatbot. Please keep your responses concise, specifically to below 300 words.",
        ),
        *msg_history,
        HumanMessage(content=input),
    ]

    try:
        response = llm.astream(messages, config={"callbacks": [langfuse_handler]})
    except Exception as e:
        return AsyncIterator(
            AIMessageChunk(content=f"Error streaming LLM response: {str(e)}")
        )
    return response
