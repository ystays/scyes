from langchain.agents import create_agent
from langchain_ollama import ChatOllama
from llm.model import GEMMA_3_12B, QWEN3_8B
from langchain_core.messages import AIMessageChunk, SystemMessage, HumanMessage, BaseMessage
from typing import Iterator
from langchain.tools import tool

llm = ChatOllama(
    model=GEMMA_3_4B,
    temperature=0,
)

@tool
def search(query: str) -> str:
    """Search for information."""
    return f"Results for: {query}"

@tool
def get_weather(location: str) -> str:
    """Get weather information for a location."""
    return f"Weather in {location}: Sunny, 72°F"

tools = [search, get_weather]

scyes_agent = create_agent(llm, system_prompt=SystemMessage(content=[
    {
        "type": "text",
        "text": "You are an AI assistant.",
    }]), tools=tools)

def invoke_agent(message: str) -> str:
    """Handle llm command by invoking the LLM."""
    try:
        scyes_agent.invoke(message)
        content = response.content
    except Exception as e:
        content = f"Error invoking LLM: {str(e)}"

    return content

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


def stream_agent(input: str, msg_history: list[BaseMessage]) -> Iterator[dict[str, Any] | Any]:
    messages = [
        SystemMessage(
            content="You're a chatbot. Please keep your responses concise, specifically to below 300 words.",
        ),
        *msg_history,
        HumanMessage(content=input),
    ]
    
    try:
        response = scyes_agent.stream({"messages": messages}, stream_mode="messages")
    except Exception as e:
       return Iterator(AIMessageChunk(content=f"Error streaming LLM response: {str(e)}")) 
    return response
