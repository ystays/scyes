from langchain.agents import create_agent
from langchain.messages import SystemMessage


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