from langchain.tools import tool
import requests
from config import app_config


@tool
def gif_search(query: str) -> str:
    """Search for a GIF matching the query. Returns a GIF URL."""
    url = "https://api.klipy.com/api/v1/gifs/search"
    params = {
        "q": query,
        "api_key": app_config.klipy_api_key,
        "limit": 1
    }
    
    data = requests.get(
        url,
        params=params,
        timeout=10
    ).json()
    results = data.get("data", {}).get("gifs", []) or data.get("data", [])
    if results:
        return results[0].get("gif", {}).get("url") or results[0].get(
            "url", "No GIF URL found"
        )
    return "No GIFs found for that query."
