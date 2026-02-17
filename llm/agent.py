from typing import Iterator, Any

from langchain.agents import create_agent
from langchain_ollama import ChatOllama
from langchain_core.messages import AIMessageChunk, SystemMessage, HumanMessage, BaseMessage
from llm.model import QWEN3_8B

from integrations.tavily import tavily_search

from observability.langfuse import langfuse
from langfuse.langchain import CallbackHandler

# Initialize Langfuse CallbackHandler for Langchain (tracing)
langfuse_handler = CallbackHandler()

llm = ChatOllama(
    model=QWEN3_8B,
    temperature=0,
)

# Add tools here
tools = [tavily_search]

scyes_agent = create_agent(llm, system_prompt=SystemMessage(content=[
    {
        "type": "text",
        "text": "You are an AI assistant.",
    }]), tools=tools)

def invoke_agent(message: str) -> str:
    """Handle llm command by invoking the LLM."""
    try:
        response = scyes_agent.invoke(
            message,
            config={"callbacks": [langfuse_handler]}
        )
        content = response.content
    except Exception as e:
        content = f"Error invoking LLM: {str(e)}"
    return content

def stream_agent(input: str, msg_history: list[BaseMessage]) -> Iterator[dict[str, Any] | Any]:
    messages = [
        SystemMessage(
            content="You're a chatbot. Please keep your responses concise, specifically to below 300 words.",
        ),
        # *msg_history,  # remove history to reduce context size
        HumanMessage(content=input),
    ]
    
    try:
        response = scyes_agent.stream(
            {"messages": messages},
            stream_mode="messages",
            config={"callbacks": [langfuse_handler]}
        )
    except Exception as e:
       return Iterator(AIMessageChunk(content=f"Error streaming LLM response: {str(e)}")) 
    return response
