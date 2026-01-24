from langchain_ollama import ChatOllama
from langchain_core.messages import AIMessageChunk
from typing import Iterator

llm = ChatOllama(
    model="gemma3:4b",
    temperature=0,
)

# messages = [
#     (
#         "system",
#         "You are a helpful assistant that translates English to French. Translate the user sentence.",
#     ),
#     ("human", "I love programming."),
# ]
# ai_msg: AIMessage = llm.invoke(messages)
# print(ai_msg.content)

def invoke(message: str) -> str:
    """Handle llm command by invoking the LLM."""
    try:
        response = llm.invoke(message)
        content = response.content
    except Exception as e:
        content = f"Error invoking LLM: {str(e)}"

    return content

def stream(message: str) -> Iterator[AIMessageChunk]:
    try:
        response = llm.stream(message)
    except Exception as e:
       return Iterator(AIMessageChunk(content=f"Error streaming LLM response: {str(e)}")) 
    return response
