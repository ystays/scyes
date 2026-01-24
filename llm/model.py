from langchain_ollama import ChatOllama
from langchain_core.messages import AIMessage

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