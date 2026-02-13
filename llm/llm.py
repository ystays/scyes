from langchain_core.messages import AIMessageChunk, SystemMessage, HumanMessage, BaseMessage
from typing import Iterator
from llm.model import QWEN3_8B, GEMMA_3_4B
from langchain_ollama import ChatOllama

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
        response = llm.stream(messages)
    except Exception as e:
       return Iterator(AIMessageChunk(content=f"Error streaming LLM response: {str(e)}")) 
    return response