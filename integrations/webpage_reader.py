from langchain.tools import tool
import requests
from bs4 import BeautifulSoup


@tool
def read_webpage(url: str) -> str:
    """Fetch and extract readable text content from a webpage URL."""
    response = requests.get(
        url,
        timeout=15,
        headers={"User-Agent": "Mozilla/5.0"}
    )
    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True)
    
    return text[:3000]
