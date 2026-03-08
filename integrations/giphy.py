from langchain.tools import tool
import requests
from config import app_config

@tool
def giphy(query: str) -> str:
    """Search for a GIF matching the query. Returns a URL."""
    url = "https://api.giphy.com/v1/gifs/search"
    params = {
        "q": query,
        "api_key": app_config.giphy_api_key,
        "limit": 1,
    }

    response = requests.get(
        url,
        params=params,
        timeout=10,
    ).json()

    url = response.get("data", {})[0].get("url", "No GIF URL found")

    return url 
