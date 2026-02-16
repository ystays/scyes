from typing import Iterator

from langchain_core.messages import AIMessageChunk, SystemMessage, HumanMessage, BaseMessage
from langchain_ollama import ChatOllama
from llm.model import QWEN3_8B, GEMMA_3_4B

from observability.langfuse import langfuse
from langfuse.langchain import CallbackHandler

# Initialize Langfuse CallbackHandler for Langchain (tracing)
langfuse_handler = CallbackHandler()

llm = ChatOllama(
    model=GEMMA_3_4B,
    temperature=0,
)

def stream(input: str, msg_history: list[BaseMessage]) -> Iterator[AIMessageChunk]:
    messages = [
        SystemMessage(
            content="You're a chatbot. Please keep your responses concise, specifically to below 300 words.",
        ),
        *msg_history,
        HumanMessage(content=input),
    ]
    
    try:
        response = llm.stream(
            messages, 
            config={"callbacks": [langfuse_handler]}
        )
    except Exception as e:
       return Iterator(AIMessageChunk(content=f"Error streaming LLM response: {str(e)}")) 
    return response