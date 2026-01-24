from langchain_ollama import ChatOllama
from langchain_core.messages import AIMessageChunk, SystemMessage, HumanMessage, BaseMessage
from typing import Iterator

GEMMA_3_27B = "gemma3:27b"
GEMMA_3_4B = "gemma3:4b"
GPT_OSS_20B = "gpt-oss:20b"
MISTRAL_SMALL_24B = "mistral-small:24b"

llm = ChatOllama(
    model=GEMMA_3_4B,
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
