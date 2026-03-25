from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper

wikipedia = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())

def search_wikipedia(query: str) -> str:
    """Search Wikipedia for general knowledge about a topic."""
    try:
        try:
            return wiki_api.summary(query, sentences=5)
        except wiki_api.exceptions.DisambiguationError as e:
            return wiki_api.summary(e.options[0], sentences=5)
    except Exception as e:
        return f"Wikipedia error: {e}"