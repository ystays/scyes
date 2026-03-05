from typing import AsyncIterator, Any
from datetime import datetime

from langchain.agents import create_agent
from langchain_core.messages import AIMessageChunk, SystemMessage, HumanMessage, BaseMessage

from integrations.tavily import tavily_search
from llm.google import google_model

from observability.langfuse import langfuse
from langfuse.langchain import CallbackHandler

# Initialize Langfuse CallbackHandler for Langchain (tracing)
langfuse_handler = CallbackHandler()

llm = google_model

# Add tools here
tools = [
    tavily_search
]

scyes_agent = create_agent(llm, system_prompt=SystemMessage(content=[
    {
        "type": "text",
        "text": f"You're a chatbot. Please keep your responses concise, specifically to below 300 words. Today is {datetime.today().strftime('%Y-%m-%d')}.",
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

async def astream_agent(input: str, msg_history: list[BaseMessage]) -> AsyncIterator[dict[str, Any] | Any]:
    messages = [
        SystemMessage(
            content="You're a chatbot. Please keep your responses concise, specifically to below 300 words.",
        ),
        # *msg_history,  # remove history to reduce context size
        HumanMessage(content=input),
    ]

    try:
        async for item in scyes_agent.astream(
            {"messages": messages},
            stream_mode="messages",
            config={"callbacks": [langfuse_handler]}
        ):
            yield item
    except Exception as e:
        yield AIMessageChunk(content=f"Error streaming LLM response: {str(e)}"), {}
